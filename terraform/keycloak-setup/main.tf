terraform {
  required_version = "~> 1.13"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.2"
    }
  }
  backend "gcs" {
    prefix = "keycloak-setup"
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Generate arXiv user OAuth2 client secret
resource "random_password" "arxiv_user_secret" {
  length  = 32
  special = true
}

# Secret for arXiv user OAuth2 client secret
resource "google_secret_manager_secret" "arxiv_user_secret" {
  secret_id = "keycloak-arxiv-user-secret-${var.environment}"
  project   = var.gcp_project_id

  replication {
    auto {}
  }

  labels = {
    service     = "keycloak"
    purpose     = "client-secret"
    environment = var.environment
  }
}

resource "google_secret_manager_secret_version" "arxiv_user_secret" {
  secret      = google_secret_manager_secret.arxiv_user_secret.id
  secret_data = random_password.arxiv_user_secret.result
}

# Service Account for the setup job
resource "google_service_account" "keycloak_setup_sa" {
  account_id   = "kcup-${var.environment}"
  display_name = "${var.environment} Keycloak Setup Job Service Account"
  project      = var.gcp_project_id
}

# Grant Secret Manager access to the setup job SA
resource "google_project_iam_member" "setup_sa_secret_accessor" {
  project = var.gcp_project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.keycloak_setup_sa.email}"
}

# Cloud Run Job for Keycloak realm setup
resource "google_cloud_run_v2_job" "keycloak_setup" {
  name     = "keycloak-realm-setup-${var.environment}"
  location = var.gcp_region
  project  = var.gcp_project_id

  # Ensure IAM permissions are granted before creating the job
  depends_on = [google_project_iam_member.setup_sa_secret_accessor]

  template {
    template {
      service_account = google_service_account.keycloak_setup_sa.email
      timeout         = "1800s" # 30 minutes
      max_retries     = 1

      containers {
        image = var.setup_job_image

        env {
          name  = "KC_URL"
          value = var.keycloak_url
        }

        env {
          name = "KC_ADMIN_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = var.keycloak_admin_password_secret_name
              version = "latest"
            }
          }
        }

        env {
          name = "ARXIV_USER_SECRET"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.arxiv_user_secret.secret_id
              version = "latest"
            }
          }
        }

        env {
          name = "LEGACY_AUTH_API_TOKEN"
          value_source {
            secret_key_ref {
              secret  = var.legacy_auth_api_token_secret_name
              version = "latest"
            }
          }
        }

        env {
          name  = "LEGACY_AUTH_URI"
          value = var.legacy_auth_uri
        }

        env {
          name  = "REALM_NAME"
          value = var.realm_name
        }

        env {
          name = "REALM_CONFIG_SOURCE"
          # Fetch realm config from GitHub raw URL
          # Format: https://raw.githubusercontent.com/arXiv/arxiv-keycloak/{branch}/keycloak_bend/realms/{filename}
          value = "https://raw.githubusercontent.com/arXiv/arxiv-keycloak/${var.realm_config_github_branch}/keycloak_bend/realms/${var.realm_config_filename != "" ? var.realm_config_filename : "arxiv-realm-gcp-${var.environment}.json"}"
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      launch_stage,
    ]
  }
}

# Optional: Automatically trigger the job after creation/update
resource "null_resource" "trigger_setup_job" {
  count = var.auto_trigger_setup ? 1 : 0

  triggers = {
    job_id            = google_cloud_run_v2_job.keycloak_setup.id
    realm_config_hash = filesha256(var.realm_config_file_path)
    keycloak_url      = var.keycloak_url
  }

  provisioner "local-exec" {
    command = <<-EOT
      gcloud run jobs execute ${google_cloud_run_v2_job.keycloak_setup.name} \
        --region ${var.gcp_region} \
        --project ${var.gcp_project_id} \
        --wait
    EOT
  }

  depends_on = [
    google_cloud_run_v2_job.keycloak_setup,
    google_secret_manager_secret_version.realm_config,
    google_secret_manager_secret_version.arxiv_user_secret,
  ]
}
