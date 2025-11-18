output "service_name" {
  value       = google_cloud_run_service.legacy_auth_provider.name
  description = "The name of the Cloud Run service"
}

output "legacy_auth_provider_url" {
  value       = google_cloud_run_service.legacy_auth_provider.status[0].url
  description = "The URL of the Legacy Auth Provider Cloud Run service"
}

output "service_account_email" {
  value       = google_service_account.legacy_auth_sa.email
  description = "The email of the service account used by Legacy Auth Provider"
}

output "classic_db_uri_secret_name" {
  value       = var.classic_db_uri_secret_name
  description = "Name of the secret containing CLASSIC_DB_URI"
}

output "api_secret_key_secret_name" {
  value       = google_secret_manager_secret.api_secret_key.secret_id
  description = "Name of the secret containing API_SECRET_KEY (JWT)"
}

output "api_secret_key_secret_id" {
  value       = google_secret_manager_secret.api_secret_key.id
  description = "Full ID of the secret containing API_SECRET_KEY (JWT)"
}
