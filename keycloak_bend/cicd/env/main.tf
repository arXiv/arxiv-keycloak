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
  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_address" "default" {
  project = var.gcp_project_id
  name    = "${var.environment_name}-load-balancer-ip"
  region  = var.gcp_region
}

resource "google_compute_region_backend_service" "default" {
  project     = var.gcp_project_id
  name        = "${var.environment_name}-backend-service"
  region      = var.gcp_region
  protocol    = "HTTP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  health_checks = [google_compute_region_health_check.default.self_link]
}

resource "google_compute_region_url_map" "default" {
  project        = var.gcp_project_id
  name           = "${var.environment_name}-lb"
  region         = var.gcp_region
  default_service = google_compute_region_backend_service.default.self_link
}

resource "google_compute_region_target_http_proxy" "default" {
  project = var.gcp_project_id
  name    = "${var.environment_name}-default-http-proxy"
  region  = var.gcp_region
  url_map = google_compute_region_url_map.default.self_link
  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_forwarding_rule" "default" {
  project             = var.gcp_project_id
  name                = "${var.environment_name}-forwarding-rule"
  region              = var.gcp_region
  network             = google_compute_network.default.self_link
  ip_protocol         = "TCP"
  port_range          = "80"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  target              = google_compute_region_target_http_proxy.default.self_link
  ip_address          = google_compute_address.default.address
  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_region_health_check" "default" {
  project = var.gcp_project_id
  name    = "${var.environment_name}-health-check"
  region  = var.gcp_region
  check_interval_sec = 5
  timeout_sec        = 5
  unhealthy_threshold = 2
  healthy_threshold   = 2

  http_health_check {
    port = 80
    request_path = "/"
  }
}
