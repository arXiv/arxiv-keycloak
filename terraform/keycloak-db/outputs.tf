output "instance_name" {
  value = google_sql_database_instance.auth_db.name
}

output "private_ip_address" {
  value = google_sql_database_instance.auth_db.private_ip_address
}

output "public_ip_address" {
  value = google_sql_database_instance.auth_db.public_ip_address
}

output "connection_name" {
  value = google_sql_database_instance.auth_db.connection_name
}

output "database_name" {
  value = google_sql_database.auth_database.name
}

output "keycloak_user_name" {
  value       = google_sql_user.keycloak_user.name
  description = "Name of the keycloak database user"
  sensitive = true
}

output "db_password_secret_name" {
  value       = google_secret_manager_secret.db_password.secret_id
  description = "Name of the Secret Manager secret containing the database admin user password"
}

output "db_password_secret_id" {
  value       = google_secret_manager_secret.db_password.id
  description = "Full resource ID of the database admin password secret"
}

output "keycloak_password_secret_name" {
  value       = google_secret_manager_secret.keycloak_password.secret_id
  description = "Name of the Secret Manager secret containing the keycloak user password"
}

output "keycloak_password_secret_id" {
  value       = google_secret_manager_secret.keycloak_password.id
  description = "Keycloak database access secret ID"
}

output "server_ca_cert" {
  value       = google_sql_database_instance.auth_db.server_ca_cert[0].cert
  description = "Cloud SQL server CA certificate (PEM format) - use this for SSL connections"
  sensitive   = true
}

output "authdb_certs_secret_name" {
  value       = google_secret_manager_secret.authdb_certs.secret_id
  description = "Name of the Secret Manager secret containing the database SSL certificate script (used by keycloak-service)"
}

output "authdb_certs_secret_id" {
  value       = google_secret_manager_secret.authdb_certs.id
  description = "Full resource ID of the authdb-certs secret"
}
