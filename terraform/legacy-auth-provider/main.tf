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
    prefix = "legacy-auth-provider"
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Generate JWT secret if not provided
resource "random_password" "api_secret_key" {
  count   = var.api_secret_key == "" ? 1 : 0
  length  = 32
  special = true
}

# Secret for API Secret Key (JWT)
resource "google_secret_manager_secret" "api_secret_key" {
  secret_id = "jwt_secret"
  project   = var.gcp_project_id

  replication {
    auto {}
  }

  labels = {
    service     = "legacy-auth-provider"
    purpose     = "jwt-signing-key"
    environment = var.environment
  }
}

resource "google_secret_manager_secret_version" "api_secret_key" {
  secret      = google_secret_manager_secret.api_secret_key.id
  secret_data = var.api_secret_key != "" ? var.api_secret_key : random_password.api_secret_key[0].result
}

# Service account for Legacy Auth Provider
resource "google_service_account" "legacy_auth_sa" {
  account_id   = "legacy-auth-provider"
  display_name = "${var.environment} Legacy Auth Provider Service Account"
  project      = var.gcp_project_id
}

# Grant access to secrets
resource "google_project_iam_member" "legacy_auth_sa_secret_accessor" {
  project = var.gcp_project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.legacy_auth_sa.email}"
}

# Cloud Run service
resource "google_cloud_run_service" "legacy_auth_provider" {
  name     = "legacy-auth-provider"
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
      }
    }

    spec {
      service_account_name  = google_service_account.legacy_auth_sa.email
      container_concurrency = var.container_concurrency
      timeout_seconds       = var.timeout_seconds

      containers {
        image = var.legacy_auth_image

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
          name  = "PORT"
          value = tostring(var.container_port)
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

        # Secret: API Secret Key (JWT)
        env {
          name = "API_SECRET_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.api_secret_key.secret_id
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
resource "google_cloud_run_service_iam_member" "legacy_auth_invoker" {
  service  = google_cloud_run_service.legacy_auth_provider.name
  location = google_cloud_run_service.legacy_auth_provider.location
  role     = "roles/run.invoker"
  member   = var.allow_unauthenticated ? "allUsers" : "serviceAccount:${google_service_account.legacy_auth_sa.email}"
}
