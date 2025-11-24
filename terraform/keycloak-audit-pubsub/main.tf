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

# Subscription to the Keycloak events topic
resource "google_pubsub_subscription" "keycloak_arxiv_events_sub" {
  name  = "keycloak-arxiv-events-sub"
  topic = google_pubsub_topic.keycloak-arxiv-events.name
}

# Service account for consuming Keycloak events
resource "google_service_account" "keycloak_event_subscriber_sa" {
  account_id   = "keycloak-event-subscriber-sa"
  display_name = "Keycloak Event Subscriber"
  description  = "Service account for consuming Keycloak audit events from Pub/Sub"
}

# Create service account key for subscriber
resource "google_service_account_key" "keycloak_subscriber_key" {
  service_account_id = google_service_account.keycloak_event_subscriber_sa.name
}

# Store subscriber key in Secret Manager
resource "google_secret_manager_secret" "keycloak_subscriber_credentials" {
  secret_id = "keycloak-event-subscriber-sa"

  replication {
    auto {}
  }

  labels = {
    purpose = "keycloak-subscriber-credentials"
  }
}

resource "google_secret_manager_secret_version" "keycloak_subscriber_credentials" {
  secret      = google_secret_manager_secret.keycloak_subscriber_credentials.id
  secret_data = google_service_account_key.keycloak_subscriber_key.private_key
}

# Grant Cloud Function Invoker role
resource "google_project_iam_member" "subscriber_cloudfunctions_invoker" {
  project = var.gcp_project_id
  role    = "roles/cloudfunctions.invoker"
  member  = "serviceAccount:${google_service_account.keycloak_event_subscriber_sa.email}"
}

# Grant Pub/Sub Subscriber role
resource "google_project_iam_member" "subscriber_pubsub_subscriber" {
  project = var.gcp_project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.keycloak_event_subscriber_sa.email}"
}

# Grant Service Account Token Creator role
resource "google_project_iam_member" "subscriber_token_creator" {
  project = var.gcp_project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:${google_service_account.keycloak_event_subscriber_sa.email}"
}
