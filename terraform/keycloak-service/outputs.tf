output "keycloak_url" {
  value       = var.enable_https && length(var.domain_names) > 0 ? "https://${var.domain_names[0]}" : "http://${google_compute_global_address.keycloak_ip.address}"
  description = "The public URL of the Keycloak service"
}

output "keycloak_https_url" {
  value       = var.enable_https && length(var.domain_names) > 0 ? "https://${var.domain_names[0]}" : null
  description = "The HTTPS URL of the Keycloak service (when HTTPS is enabled)"
}

output "keycloak_http_url" {
  value       = "http://${google_compute_global_address.keycloak_ip.address}"
  description = "The HTTP URL of the Keycloak service"
}

output "keycloak_ip" {
  value       = google_compute_global_address.keycloak_ip.address
  description = "The public IP address of the Keycloak service"
}

output "keycloak_service_name" {
  value       = google_cloud_run_service.keycloak.name
  description = "The name of the Cloud Run service"
}

output "keycloak_service_url" {
  value       = google_cloud_run_service.keycloak.status[0].url
  description = "The direct URL of the Cloud Run service"
}

output "service_account_email" {
  value       = google_service_account.keycloak_sa.email
  description = "The email of the service account used by Keycloak"
}

output "keycloak_db_password_secret_name" {
  value       = var.keycloak_db_password_secret_name
  description = "Name of the secret containing keycloak database password (from keycloak-db module)"
}

output "domain_names" {
  value       = var.domain_names
  description = "Configured domain names for the service"
}
