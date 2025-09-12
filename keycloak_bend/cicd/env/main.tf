locals {
  dns_hostnames = ["${var.environment_name}.arxiv.org"]
}

resource "google_compute_network" "default" {
  project                 = var.gcp_project_id
  name                    = "${var.environment_name}-network"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "proxy_only" {
  project       = var.gcp_project_id
  name          = "${var.environment_name}-proxy-only-subnet"
  ip_cidr_range = "10.129.0.0/20"
  region        = var.gcp_region
  network       = google_compute_network.default.self_link
  purpose       = "REGIONAL_MANAGED_PROXY"
  role          = "ACTIVE"
}

resource "google_compute_global_address" "default" {
  project = var.gcp_project_id
  name    = "${var.environment_name}-load-balancer-ip"
}

resource "google_compute_backend_service" "default" {
  project               = var.gcp_project_id
  name                  = "${var.environment_name}-backend-service"
  protocol              = "HTTP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  health_checks         = [google_compute_health_check.default.self_link]
}


resource "google_compute_url_map" "default" {
  project         = var.gcp_project_id
  name            = "${var.environment_name}-lb"
  default_service = google_compute_backend_service.default.self_link
}

resource "google_compute_target_https_proxy" "default" {
  project          = var.gcp_project_id
  name             = "${var.environment_name}-https-proxy"
  url_map          = google_compute_url_map.default.self_link
  ssl_certificates = [var.ssl_certificate_name]
}

resource "google_compute_global_forwarding_rule" "default" {
  project                 = var.gcp_project_id
  name                    = "${var.environment_name}-https-forwarding-rule"
  ip_protocol             = "TCP"
  port_range              = "443"
  load_balancing_scheme   = "EXTERNAL_MANAGED"
  target                  = google_compute_target_https_proxy.default.self_link
  ip_address              = google_compute_global_address.default.address
}

resource "google_compute_health_check" "default" {
  project               = var.gcp_project_id
  name                  = "${var.environment_name}-health-check"
  check_interval_sec    = 5
  timeout_sec           = 5
  unhealthy_threshold   = 2
  healthy_threshold     = 2

  http_health_check {
    port         = 80
    request_path = "/"
  }
}