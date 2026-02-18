terraform {
  required_version = "~> 1.13"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.2"
    }
  }
  backend "gcs" {
    prefix = "user-portal"
  }
}

provider "google" {
  project = var.gcp_project_id # default inherited by all resources
  region  = var.gcp_region     # default inherited by all resources
}

### service account ###

resource "google_service_account" "account" {
  account_id   = "user-portal"
  display_name = "Service account to deploy admin ui cloud run instance"
}

resource "google_project_iam_member" "logs_writer" {
  project = var.gcp_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.account.email}"
}

resource "google_project_iam_member" "service_account_user" {
  project = var.gcp_project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.account.email}"
}

### cloud run instance ###  (legacy cloud run service)
resource "google_cloud_run_v2_service" "user_portal" {
  name     = "user-portal"
  location = var.gcp_region

  template {
    containers {
      image = var.image_path
      ports {
        container_port = var.container_port
      }
      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "legacy_auth_invoker" {
  service  = google_cloud_run_service.legacy_auth_provider.name
  location = google_cloud_run_service.legacy_auth_provider.location
  role     = "roles/run.invoker"
  member   = var.allow_unauthenticated ? "allUsers" : "serviceAccount:${google_service_account.legacy_auth_sa.email}"
}
