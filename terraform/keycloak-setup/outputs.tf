output "setup_job_name" {
  description = "Name of the Cloud Run setup job"
  value       = google_cloud_run_v2_job.keycloak_setup.name
}

output "setup_job_id" {
  description = "ID of the Cloud Run setup job"
  value       = google_cloud_run_v2_job.keycloak_setup.id
}

output "setup_service_account_email" {
  description = "Email of the service account used by the setup job"
  value       = google_service_account.keycloak_setup_sa.email
}

output "trigger_command" {
  description = "Command to manually trigger the setup job"
  value       = "gcloud run jobs execute ${google_cloud_run_v2_job.keycloak_setup.name} --region ${var.gcp_region} --project ${var.gcp_project_id}"
}
