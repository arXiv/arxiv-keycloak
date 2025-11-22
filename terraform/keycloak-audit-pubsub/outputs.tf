output "topic_name" {
  value = basename(google_pubsub_topic.keycloak-arxiv-events.name)
}

output "topic_id" {
  value = basename(google_pubsub_topic.keycloak-arxiv-events.id)
}

output "pubsub_credentials_secret_name" {
  value       = google_secret_manager_secret.keycloak_pubsub_credentials.secret_id
  description = "Secret Manager secret name for GCP_CREDENTIALS environment variable"
}

output "service_account_email" {
  value       = google_service_account.keycloak_pubsub_sa.email
  description = "Email of the Pub/Sub publisher service account"
}

output "subscriber_credentials_secret_name" {
  value       = google_secret_manager_secret.keycloak_subscriber_credentials.secret_id
  description = "Secret Manager secret name for subscriber service account credentials"
}
