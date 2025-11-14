terraform {
  required_version = "~> 1.13"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.2"
    }
  }
  backend "gcs" {
    prefix = "keycloak-audit-pubsub"
  }
}

provider "google" {
  project = var.gcp_project_id # default inherited by all resources
  region  = var.gcp_region     # default inherited by all resources
}


resource "google_pubsub_topic" "keycloak-arxiv-events" {
  name = "keycloak-arxiv-events"
}

# Service account for Keycloak event publishing (requires JSON key)
# This SA is used by the Keycloak Pub/Sub audit event SPI
resource "google_service_account" "keycloak_pubsub_sa" {
  account_id   = "keycloak-pubsub-event-sa"
  display_name = "Keycloak Pub/Sub Event Publisher"
  description  = "Service account for Keycloak to publish audit events to Pub/Sub"
}

# Grant Pub/Sub Publisher role on the topic
resource "google_pubsub_topic_iam_member" "keycloak_publisher" {
  project = var.gcp_project_id
  topic   = google_pubsub_topic.keycloak-arxiv-events.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.keycloak_pubsub_sa.email}"
}

# Create service account key (JSON)
resource "google_service_account_key" "keycloak_pubsub_key" {
  service_account_id = google_service_account.keycloak_pubsub_sa.name
}

# Store base64-encoded key in Secret Manager
resource "google_secret_manager_secret" "keycloak_pubsub_credentials" {
  secret_id = "keycloak-pubsub-event-sa"

  replication {
    auto {}
  }

  labels = {
    purpose = "keycloak-pubsub-credentials"
  }
}

resource "google_secret_manager_secret_version" "keycloak_pubsub_credentials" {
  secret      = google_secret_manager_secret.keycloak_pubsub_credentials.id
  secret_data = google_service_account_key.keycloak_pubsub_key.private_key
  # Note: private_key is already base64-encoded by Google
}
