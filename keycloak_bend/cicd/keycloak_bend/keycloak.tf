provider "google" {
  project = var.gcp_project_id # default inherited by all resources
  region  = var.gcp_region     # default inherited by all resources
}

resource "google_cloud_run_service" "keycloak" {
  name     = "keycloak"
  location = "us-central1" # This could also be a variable if needed
  project  = var.gcp_project_id
  
  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"            = var.max_scale
        "autoscaling.knative.dev/minScale"            = var.min_scale
        "run.googleapis.com/sessionAffinity"          = "true"
        "run.googleapis.com/vpc-access-connector"     = "projects/${var.gcp_project_id}/locations/${var.gcp_region}/connectors/clourrunconnector"
        "run.googleapis.com/vpc-access-egress"        = "private-ranges-only"
        "run.googleapis.com/startup-cpu-boost"        = "true"
      }
    }
    spec {
      container_concurrency = 80
      timeout_seconds       = 300
      #service_account_name  = "${var.gcp_project_id}-compute@developer.gserviceaccount.com"
      #service_account_name  = "874717964009-compute@developer.gserviceaccount.com"

      containers {
        image = "gcr.io/arxiv-development/arxiv-keycloak/keycloak:latest"

        ports {
          container_port = 8080
        }

        env {
          name  = "DB_ADDR"
          value = var.db_addr
        }
        env {
          name  = "PROXY_MODE"
          value = var.proxy_mode
        }
        env {
          name  = "KC_BOOTSTRAP_ADMIN_USERNAME"
          value = var.kc_bootstrap_admin_username
        }
        env {
          name  = "BOOTSTRAP"
          value = var.bootstrap
        }
        env {
          name  = "LOG_OUTPUT_FORMAT"
          value = var.log_output_format
        }
        env {
          name  = "GCP_PROJECT_ID"
          value = var.gcp_project_id
        }
        env {
          name  = "KC_PORT"
          value = var.kc_port
        }
        env {
          name  = "GRPC_LOG_LEVEL"
          value = var.grpc_log_level
        }
        env {
          name  = "GRPC_TRACE"
          value = var.grpc_trace
        }
        env {
          name  = "ARXIV_USER_REGISTRATION_URL"
          value = var.arxiv_user_registration_url
        }
        env {
          name  = "KC_HOSTNAME"
          value = var.kc_hostname
        }
        env {
          name = "KC_DB_PASS"
          value_from {
            secret_key_ref {
              name    = "authdb-password"
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
        env {
          name = "GCP_CREDENTIALS"
          value_from {
            secret_key_ref {
              name    = "keycloak-pubsub-event-sa"
              key     = "latest"
            }
          }
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "2Gi"
          }
        }

        volume_mounts {
          name        = "authdb-certs-puf-bif-mep"
          mount_path  = "/secrets/authdb-certs"
        }

        startup_probe {
          timeout_seconds    = 240
          period_seconds     = 240
          failure_threshold  = 1
          tcp_socket {
            port = 8080
          }
        }
      }

      volumes {
        name = "authdb-certs-puf-bif-mep"
        secret {
          secret_name = "authdb-certs"
          items {
            key  = "latest"
            path = "db-certs-expand.sh"
          }
        }
      }
    }
  }

  traffic {
    latest_revision = true
    percent         = 100
  }

  autogenerate_revision_name = true
}

resource "google_cloud_run_service_iam_member" "keycloak_service_public_access" {
  location = google_cloud_run_service.keycloak.location
  project  = google_cloud_run_service.keycloak.project
  service  = google_cloud_run_service.keycloak.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# The YAML specifies ingress: all, which means external access is allowed.
# This is usually handled by a separate ingress resource or by setting the
# appropriate IAM policy on the Cloud Run service. Since the YAML explicitly
# mentions `run.googleapis.com/ingress: all`, we'll add an IAM member to allow
# unauthenticated invocations, which is the equivalent for a publicly accessible
# Cloud Run service. 