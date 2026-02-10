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
    prefix = "oauth2-authenticator"
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}


# data "terraform_remote_state" "keycloak" {
#   backend = "gcs"
#   config = {
#     bucket = var.tf_keycloak_bucket  # The bucket where Keycloak's state is stored
#     prefix = "keycloak"                   # The prefix used in Keycloak's backend config
#   }
# }

# # Now you can use the Keycloak URL output
# # Assuming the Keycloak module outputs it as "keycloak_url"
# locals {
#   keycloak_url = data.terraform_remote_state.keycloak.outputs.keycloak_url
# }


# Generate JWT secret if not provided
resource "random_password" "arxiv_user_client_secret" {
  count   = var.arxiv_user_client_secret == "" ? 1 : 0
  length  = 32
  special = true
}

# Secret for API Secret Key (JWT)
resource "google_secret_manager_secret" "arxiv_user_client_secret" {
  secret_id = "arxiv_user_client_secret"
  project   = var.gcp_project_id

  replication {
    auto {}
  }

  labels = {
    service     = "oauth2-authenticator"
    purpose     = "oauth2-arxiv-user-client-secret"
    environment = var.environment
  }
}

# Service account for OAuth2 authenticator
resource "google_service_account" "oauth2_auth_sa" {
  account_id   = "oauth2-authenticator"
  display_name = "${var.environment} OAuth2 Authenticator Service Account"
  project      = var.gcp_project_id
}

# Grant access to secrets
resource "google_project_iam_member" "oauth2_auth_sa_secret_accessor" {
  project = var.gcp_project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.oauth2_auth_sa.email}"
}

# Grant Cloud SQL Client access
resource "google_project_iam_member" "oauth2_auth_sa_cloudsql_client" {
  project = var.gcp_project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.oauth2_auth_sa.email}"
}

# Grant Cloud SQL Viewer access
resource "google_project_iam_member" "oauth2_auth_sa_cloudsql_viewer" {
  project = var.gcp_project_id
  role    = "roles/cloudsql.viewer"
  member  = "serviceAccount:${google_service_account.oauth2_auth_sa.email}"
}

# Cloud Run service
resource "google_cloud_run_service" "oauth2_auth_provider" {
  name     = "oauth2-authenticator"
  location = var.gcp_region
  project  = var.gcp_project_id

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"         = var.min_instances
        "autoscaling.knative.dev/maxScale"         = var.max_instances
        "run.googleapis.com/cloudsql-instances"    = var.cloudsql_instance
        "run.googleapis.com/cpu-boost"             = var.cpu_boost
        "run.googleapis.com/session-affinity"      = var.session_affinity
        "run.googleapis.com/execution-environment" = "gen2"
        "client.knative.dev/user-image"            = var.image_digest
      }
    }

    spec {
      service_account_name  = google_service_account.oauth2_auth_sa.email
      container_concurrency = var.container_concurrency
      timeout_seconds       = var.timeout_seconds

      containers {
        image = var.oauth2_auth_image

        ports {
          container_port = var.container_port
        }

        resources {
          limits = {
            cpu    = var.cpu_limit
            memory = var.memory_limit
          }
        }

        env {
          name  = "SQLALCHEMY_RECORD_QUERIES"
          value = var.sqlalchemy_record_queries
        }

        env {
          name  = "SQLALCHEMY_TRACK_MODIFICATIONS"
          value = "False"
        }

        # Secret: Database URI
        env {
          name = "CLASSIC_DB_URI"
          value_from {
            secret_key_ref {
              name = var.classic_db_uri_secret_name
              key  = "latest"
            }
          }
        }

        # Secret: OIDC arxiv-user client secret
        env {
          name = "ARXIV_USER_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.arxiv_user_client_secret.secret_id
              key  = "latest"
            }
          }
        }

        # Additional environment variables
        dynamic "env" {
          for_each = var.additional_env_vars
          content {
            name  = env.key
            value = env.value
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

# Allow unauthenticated access
resource "google_cloud_run_service_iam_member" "oauth2_auth_invoker" {
  service  = google_cloud_run_service.oauth2_auth_provider.name
  location = google_cloud_run_service.oauth2_auth_provider.location
  role     = "roles/run.invoker"
  member   = var.allow_unauthenticated ? "allUsers" : "serviceAccount:${google_service_account.oauth2_auth_sa.email}"
}
