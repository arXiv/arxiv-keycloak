output "keycloak_backend_service_id" {
  value = google_compute_region_backend_service.keycloak_backend.id
}

output "keycloak_cloud_run_url" {
  description = "The direct URL to the Keycloak Cloud Run service."
  value       = google_cloud_run_service.keycloak.status[0].url
}

output "keycloak_lb_url" {
  description = "The URL to the Keycloak admin console through the load balancer."
  value       = "http://${data.terraform_remote_state.env.outputs.load_balancer_ip_address}/auth/admin/"
}
