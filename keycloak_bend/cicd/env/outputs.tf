output "load_balancer_ip_address" {
  description = "The IP address of the load balancer."
  value       = google_compute_address.default.address
}

output "network_self_link" {
  description = "The self-link of the VPC network."
  value       = google_compute_network.default.self_link
}

output "backend_service_self_link" {
  description = "The self-link of the default regional backend service."
  value       = google_compute_region_backend_service.default.self_link
}

output "default_url_map_self_link" {
  description = "The self-link of the default regional URL map."
  value       = google_compute_region_url_map.default.self_link
}

output "default_http_proxy_self_link" {
  description = "The self-link of the default regional HTTP proxy."
  value       = google_compute_region_target_http_proxy.default.self_link
}

output "default_forwarding_rule_self_link" {
  description = "The self-link of the default regional forwarding rule."
  value       = google_compute_forwarding_rule.default.self_link
}

output "load_balancer_name" {
  description = "The name of the load balancer URL map."
  value       = google_compute_region_url_map.default.name
}
