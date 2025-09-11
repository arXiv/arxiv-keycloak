output "load_balancer_ip_address" {
  description = "The IP address of the load balancer."
  value       = google_compute_global_address.default.address
}

output "network_self_link" {
  description = "The self-link of the VPC network."
  value       = google_compute_network.default.self_link
}

output "backend_service_self_link" {
  description = "The self-link of the default backend service."
  value       = google_compute_backend_service.default.self_link
}

output "default_url_map_self_link" {
  description = "The self-link of the default URL map."
  value       = google_compute_url_map.default.self_link
}

output "default_https_proxy_self_link" {
  description = "The self-link of the default HTTPS proxy."
  value       = google_compute_target_https_proxy.default.self_link
}

output "default_forwarding_rule_self_link" {
  description = "The self-link of the default forwarding rule."
  value       = google_compute_global_forwarding_rule.default.self_link
}

output "load_balancer_name" {
  description = "The name of the load balancer URL map."
  value       = google_compute_url_map.default.name
}

output "dns_hostnames" {
  description = "The DNS hostnames for this environment."
  value       = local.dns_hostnames
}
