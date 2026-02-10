output "service_name" {
  value       = google_cloud_run_service.oauth2_auth_provider.name
  description = "The name of the Cloud Run service"
}

output "oauth2_auth_provider_url" {
  value       = google_cloud_run_service.oauth2_auth_provider.status[0].url
  description = "The URL of the Legacy Auth Provider Cloud Run service"
}

output "service_account_email" {
  value       = google_service_account.oauth2_auth_sa.email
  description = "The email of the service account used by Legacy Auth Provider"
}

output "classic_db_uri_secret_name" {
  value       = var.classic_db_uri_secret_name
  description = "Name of the secret containing CLASSIC_DB_URI"
}

output "arxiv_user_client_secret_name" {
  value       = google_secret_manager_secret.arxiv_user_client_secret.secret_id
  description = "Name of the Secret Manager secret for ARXIV_USER_SECRET (OIDC client secret)"
}
