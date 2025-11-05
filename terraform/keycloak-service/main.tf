terraform {
  required_version = "~> 1.13"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.2"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
  backend "gcs" {
    prefix = "keycloak-service"
  }
}

provider "google" {
  project = var.gcp_project_id # default inherited by all resources
  region  = var.gcp_region     # default inherited by all resources
}

# Reference existing VPC resources (default network and connector)
data "google_compute_network" "default" {
  name    = "default"
  project = var.gcp_project_id
}

data "google_vpc_access_connector" "vpc_connector" {
  name    = var.vpc_connector_name
  region  = var.gcp_region
  project = var.gcp_project_id
}

# Generate random password for keycloak database user if not provided
resource "random_password" "keycloak_db_password" {
  count   = var.keycloak_db_password == "" ? 1 : 0
  length  = 32
  special = true
}

# Secret Manager secret for keycloak database user password (owned by service)
resource "google_secret_manager_secret" "keycloak_db_password" {
  secret_id = "keycloak-db-password"
  project   = var.gcp_project_id

  replication {
    auto {}
  }

  labels = {
    service = "keycloak"
    purpose = "database-credentials"
  }
}

resource "google_secret_manager_secret_version" "keycloak_db_password" {
  secret      = google_secret_manager_secret.keycloak_db_password.id
  secret_data = var.keycloak_db_password != "" ? var.keycloak_db_password : random_password.keycloak_db_password[0].result
}

# Read the keycloak database password for use in the Cloud Run service
data "google_secret_manager_secret_version" "auth_db_keycloak_password" {
  secret     = google_secret_manager_secret.keycloak_db_password.id
  depends_on = [google_secret_manager_secret_version.keycloak_db_password]
}

# Dynamic data sources for additional secrets
data "google_secret_manager_secret_version" "secrets" {
  for_each = var.secrets
  secret   = each.value.secret_name
  version  = each.value.version
  project  = var.gcp_project_id
}

resource "google_service_account" "keycloak_sa" {
  account_id = "keycloak-sa"
  display_name = "${var.environment} Keycloak Service Account"
  project      = var.gcp_project_id
}

resource "google_project_iam_member" "keycloak_sa_secret_accessor" {
  project = var.gcp_project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.keycloak_sa.email}"
}

# Grant access to Pub/Sub for event publishing
resource "google_project_iam_member" "keycloak_sa_pubsub_publisher" {
  project = var.gcp_project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.keycloak_sa.email}"
}

resource "google_cloud_run_service" "keycloak" {
  name     = "keycloak"
  location = var.gcp_region
  project  = var.gcp_project_id

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"        = var.min_instances
        "autoscaling.knative.dev/maxScale"        = var.max_instances
        "run.googleapis.com/vpc-access-connector" = data.google_vpc_access_connector.vpc_connector.name
        "run.googleapis.com/vpc-access-egress"    = var.vpc_egress
        "run.googleapis.com/cpu-boost"            = var.cpu_boost
        "run.googleapis.com/session-affinity"     = var.session_affinity
      }
    }

    spec {
      service_account_name  = google_service_account.keycloak_sa.email
      container_concurrency = var.container_concurrency
      timeout_seconds       = var.timeout_seconds

      containers {
        image = var.keycloak_image

        startup_probe {
          timeout_seconds    = 240
          period_seconds     = 240
          failure_threshold  = 1
          tcp_socket {
            port = 8080
          }
        }

        resources {
          limits = {
            cpu    = var.cpu_limit
            memory = var.memory_limit
          }
        }

        ports {
          container_port = var.container_port
        }

        env {
          name  = "DB_VENDOR"
          value = "postgres"
        }

        env {
          name  = "DB_ADDR"
          value = var.auth_db_private_ip
        }

        env {
          name  = "DB_DATABASE"
          value = var.auth_db_name
        }

        env {
          name  = "DB_USER"
          value = var.db_user
        }

        env {
          name  = "DB_PASSWORD"
          value = data.google_secret_manager_secret_version.auth_db_keycloak_password.secret_data
        }

        env {
          name  = "JDBC_PARAMS"
          value = var.jdbc_params
        }

        env {
          name  = "KEYCLOAK_START"
          value = var.keycloak_start
        }

        env {
          name  = "GCP_PROJECT_ID"
          value = var.gcp_project_id 
        }

        env {
          name  = "ARXIV_USER_REGISTRATION_URL"
          value = var.arxiv_user_registration_url
        
        }

        env {
          name = "KC_DB_PASS"
          value_from {
            secret_key_ref {
              name    = "auth-db-password"
              key     = "latest"
            }
          }
        }

        env {
          name = "KC_BOOTSTRAP_ADMIN_PASSWORD"
          value_from {
            secret_key_ref {
              name    = "keycloak-admin-password"
              key     = "latest"
            }
          }
        }

        dynamic "env" {
          for_each = var.additional_env_vars
          content {
            name  = env.key
            value = env.value
          }
        }

        # Environment variables from secrets (those without mount_path)
        dynamic "env" {
          for_each = { for k, v in var.secrets : k => v if v.mount_path == null }
          content {
            name = upper(env.key)
            value_from {
              secret_key_ref {
                name = data.google_secret_manager_secret_version.secrets[env.key].secret
                key  = data.google_secret_manager_secret_version.secrets[env.key].version
              }
            }
          }
        }

        # Volume mounts for secrets (those with mount_path)
        dynamic "volume_mounts" {
          for_each = { for k, v in var.secrets : k => v if v.mount_path != null }
          content {
            name       = volume_mounts.key
            mount_path = volume_mounts.value.mount_path
          }
        }
      }

      # Volumes for secrets
      dynamic "volumes" {
        for_each = { for k, v in var.secrets : k => v if v.mount_path != null }
        content {
          name = volumes.key
          secret {
            secret_name  = data.google_secret_manager_secret_version.secrets[volumes.key].secret
            default_mode = 0444
            items {
              key  = data.google_secret_manager_secret_version.secrets[volumes.key].version
              path = basename(volumes.value.mount_path)
            }
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_compute_global_address" "keycloak_ip" {
  name    = "${var.environment}-keycloak-ip"
  project = var.gcp_project_id
}

resource "google_compute_backend_service" "keycloak_backend" {
  name                  = "${var.environment}-keycloak-backend"
  protocol              = "HTTP"
  port_name             = "http"
  load_balancing_scheme = "EXTERNAL"
  project               = var.gcp_project_id
  timeout_sec           = var.backend_timeout_sec

  backend {
    group = google_compute_region_network_endpoint_group.keycloak_neg.id
  }

  health_checks = var.enable_health_check ? [google_compute_health_check.keycloak_health_check[0].id] : []

  depends_on = [google_compute_region_network_endpoint_group.keycloak_neg]
}

resource "google_compute_url_map" "keycloak_url_map" {
  name            = "${var.environment}-keycloak-url-map"
  default_service = google_compute_backend_service.keycloak_backend.self_link
  project         = var.gcp_project_id
}

# Google-managed SSL certificate
resource "google_compute_managed_ssl_certificate" "keycloak_ssl_cert" {
  count   = var.enable_https && length(var.domain_names) > 0 ? 1 : 0
  name    = "${var.environment}-keycloak-ssl-cert"
  project = var.gcp_project_id

  managed {
    domains = var.domain_names
  }
}

# HTTPS target proxy (for SSL/TLS termination)
resource "google_compute_target_https_proxy" "keycloak_https_proxy" {
  count            = var.enable_https && length(var.domain_names) > 0 ? 1 : 0
  name             = "${var.environment}-keycloak-https-proxy"
  url_map          = google_compute_url_map.keycloak_url_map.id
  ssl_certificates = [google_compute_managed_ssl_certificate.keycloak_ssl_cert[0].id]
  project          = var.gcp_project_id
}

# HTTPS forwarding rule (port 443)
resource "google_compute_global_forwarding_rule" "keycloak_https_forward_rule" {
  count      = var.enable_https && length(var.domain_names) > 0 ? 1 : 0
  name       = "${var.environment}-keycloak-https-forwarding-rule"
  ip_address = google_compute_global_address.keycloak_ip.address
  target     = google_compute_target_https_proxy.keycloak_https_proxy[0].id
  port_range = "443"
  project    = var.gcp_project_id
}

# HTTP target proxy (optional, for HTTP to HTTPS redirect or HTTP access)
resource "google_compute_target_http_proxy" "keycloak_http_proxy" {
  name    = "${var.environment}-keycloak-http-proxy"
  url_map = google_compute_url_map.keycloak_url_map.id
  project = var.gcp_project_id
}

# HTTP forwarding rule (port 80)
resource "google_compute_global_forwarding_rule" "keycloak_http_forward_rule" {
  name       = "${var.environment}-keycloak-http-forwarding-rule"
  ip_address = google_compute_global_address.keycloak_ip.address
  target     = google_compute_target_http_proxy.keycloak_http_proxy.id
  port_range = "80"
  project    = var.gcp_project_id
}

resource "google_compute_region_network_endpoint_group" "keycloak_neg" {
  name                  = "${var.environment}-keycloak-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.gcp_region
  project               = var.gcp_project_id

  cloud_run {
    service = google_cloud_run_service.keycloak.name
  }

  depends_on = [google_cloud_run_service.keycloak]
}


resource "google_compute_health_check" "keycloak_health_check" {
  count              = var.enable_health_check ? 1 : 0
  name               = "${var.environment}-keycloak-health-check"
  project            = var.gcp_project_id
  timeout_sec        = var.health_check_timeout
  check_interval_sec = var.health_check_interval

  http_health_check {
    port         = var.container_port
    request_path = var.health_check_path
  }
}

resource "google_cloud_run_service_iam_member" "keycloak_invoker" {
  service  = google_cloud_run_service.keycloak.name
  location = google_cloud_run_service.keycloak.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
