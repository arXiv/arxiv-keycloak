output "keycloak_backend_service_id" {
  value = google_compute_backend_service.keycloak_backend.id
}

output "keycloak_cloud_run_url" {
  description = "The direct URL to the Keycloak Cloud Run service."
  value       = "${google_cloud_run_service.keycloak.status[0].url}/admin/master/console"
}

output "keycloak_lb_url" {
  description = "The URL to the Keycloak admin console through the load balancer."
  value       = "https://${data.terraform_remote_state.env.outputs.dns_hostnames[0]}/admin/master/console"
}

output "keycloak_lb_http_url" {
  description = "The HTTP URL to the Keycloak admin console through the load balancer."
  value       = "http://${data.terraform_remote_state.env.outputs.load_balancer_ip_address}/admin/master/console"
}