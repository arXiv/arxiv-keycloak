provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

data "terraform_remote_state" "env" {
  backend = "gcs"
  config = {
    bucket = var.terraform_state_bucket
    prefix = "${var.environment_name}-env"
  }
}

data "google_compute_network" "default" {
  name    = "${var.environment_name}-network"
  project = var.gcp_project_id
}

resource "google_cloud_run_service" "keycloak" {
  name     = "keycloak-${var.environment_name}"
  location = "us-central1"
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

      containers {
        image = "gcr.io/${var.gcp_project_id}/arxiv-keycloak/keycloak:${var.keycloak_docker_tag}"

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

resource "google_compute_region_network_endpoint_group" "keycloak_neg" {
  name                  = "keycloak-${var.environment_name}-neg"
  network_endpoint_type = "SERVERLESS"
  region                = "us-central1"
  cloud_run {
    service = google_cloud_run_service.keycloak.name
  }
}

resource "google_compute_backend_service" "keycloak_backend" {
  name                  = "keycloak-${var.environment_name}-backend"
  project               = var.gcp_project_id
  protocol              = "HTTP"
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.keycloak_neg.id
  }
}

resource "google_compute_firewall" "allow_lb_to_cloud_run" {
  name    = "allow-lb-to-keycloak-${var.environment_name}"
  network = data.google_compute_network.default.self_link
  project = var.gcp_project_id

  allow {
    protocol = "tcp"
    ports    = ["8080"]
  }

  source_ranges = ["35.191.0.0/16", "130.211.0.0/22"]
}

resource "null_resource" "update_backend_service" {
  triggers = {
    backend_service_id = google_compute_backend_service.keycloak_backend.id
  }

  provisioner "local-exec" {
    command = "gcloud compute backend-services update keycloak-${var.environment_name}-backend --global --no-health-checks"
  }
}

resource "null_resource" "update_url_map" {
  triggers = {
    keycloak_backend_service_id = google_compute_backend_service.keycloak_backend.id
    url_map_name                = data.terraform_remote_state.env.outputs.load_balancer_name
  }

  provisioner "local-exec" {
    command = <<EOT
      gcloud compute url-maps add-path-matcher ${self.triggers.url_map_name} \
        --global \
        --path-matcher-name=keycloak-matcher \
        --default-service=${data.terraform_remote_state.env.outputs.backend_service_self_link} \
        --backend-service-path-rules='/admin/*=${google_compute_backend_service.keycloak_backend.self_link},/auth/*=${google_compute_backend_service.keycloak_backend.self_link},/realms/*=${google_compute_backend_service.keycloak_backend.self_link}' \
        --project=${var.gcp_project_id}
EOT
  }
}

resource "null_resource" "remove_backend_from_url_map" {
  depends_on = [google_compute_backend_service.keycloak_backend]
  
  triggers = {
    backend_service_id = google_compute_backend_service.keycloak_backend.id
    backend_service_name = google_compute_backend_service.keycloak_backend.name
    project_id        = var.gcp_project_id
  }

  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
      # Try to remove path matcher if URL map still exists
      echo "Attempting to clean up URL map references..."
      
      # List all URL maps and try to remove the keycloak path matcher from each
      gcloud compute url-maps list --format="value(name)" --project=${self.triggers.project_id} | while read urlmap; do
        if [ ! -z "$urlmap" ]; then
          echo "Checking URL map: $urlmap"
          # Check if this URL map has the keycloak path matcher
          if gcloud compute url-maps describe "$urlmap" --global --project=${self.triggers.project_id} --format="value(pathMatchers[].name)" | grep -q "keycloak-matcher"; then
            echo "Removing keycloak path matcher from URL map: $urlmap"
            gcloud compute url-maps remove-path-matcher "$urlmap" \
              --global \
              --path-matcher-name=keycloak-matcher \
              --project=${self.triggers.project_id} || true
          fi
        fi
      done
      
      # Also try to remove the backend service directly
      echo "Attempting to delete backend service directly..."
      gcloud compute backend-services delete ${self.triggers.backend_service_name} --global --quiet --project=${self.triggers.project_id} || true
EOT
  }
}