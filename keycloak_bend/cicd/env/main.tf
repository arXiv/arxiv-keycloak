locals {
  dns_hostnames = ["${var.environment_name}.${var.domain_name}"]
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
resource "google_certificate_manager_dns_authorization" "abd_arxiv_org_auth" {
  project = var.gcp_project_id
  name   = "${var.environment_name}-auth"
  domain = "${var.environment_name}.${var.domain_name}"
}

resource "google_dns_record_set" "cert_auth_record" {
  project      = var.gcp_project_id
  name         = "${google_certificate_manager_dns_authorization.abd_arxiv_org_auth.dns_resource_record.0.name}"
  type         = "${google_certificate_manager_dns_authorization.abd_arxiv_org_auth.dns_resource_record.0.type}"
  ttl          = 300
  managed_zone = google_dns_managed_zone.default.name
  rrdatas      = ["${google_certificate_manager_dns_authorization.abd_arxiv_org_auth.dns_resource_record.0.data}"]
}

resource "google_dns_managed_zone" "default" {
  project     = var.gcp_project_id
  name        = "${var.environment_name}-${replace(var.domain_name, ".", "-")}"  # e.g., "xyz-arxivd-org"
  dns_name    = "${var.domain_name}."  # e.g., "arxivd.org."
  description = "DNS zone for ${var.environment_name} environment"
}

resource "google_compute_url_map" "default" {
  project         = var.gcp_project_id
  name            = "${var.environment_name}-lb"
  default_service = google_compute_backend_service.default.self_link
}

resource "google_compute_managed_ssl_certificate" "default" {
  project = var.gcp_project_id
  name    = "${var.environment_name}-ssl-cert"
  managed {
    domains = ["${var.environment_name}.${var.domain_name}"]
  }
}

resource "google_compute_target_https_proxy" "default" {
  project          = var.gcp_project_id
  name             = "${var.environment_name}-https-proxy"
  url_map          = google_compute_url_map.default.self_link
  ssl_certificates = [google_compute_managed_ssl_certificate.default.self_link]
  depends_on = [
    google_compute_managed_ssl_certificate.default
  ]
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

resource "null_resource" "cleanup_network_dependencies" {
  depends_on = [google_compute_network.default]
  
  triggers = {
    network_name = google_compute_network.default.name
    project_id = var.gcp_project_id
    url_map_name = google_compute_url_map.default.name  # Use the resource name directly
  }

  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
      # Remove all firewall rules that use this network
      echo "Cleaning up firewall rules for network: ${self.triggers.network_name}"
      gcloud compute firewall-rules list --filter="network:${self.triggers.network_name}" --format="value(name)" --project=${self.triggers.project_id} | while read rule; do
        if [ ! -z "$rule" ]; then
          echo "Deleting firewall rule: $rule"
          gcloud compute firewall-rules delete "$rule" --quiet --project=${self.triggers.project_id} || true
        fi
      done
      
      # Remove any remaining backend services that might reference this network
      echo "Cleaning up backend services for network: ${self.triggers.network_name}"
      gcloud compute backend-services list --filter="network:${self.triggers.network_name}" --format="value(name)" --project=${self.triggers.project_id} | while read backend; do
        if [ ! -z "$backend" ]; then
          echo "Checking backend service: $backend"
          gcloud compute backend-services describe "$backend" --global --project=${self.triggers.project_id} --format="value(backends[].group)" | grep -q "${self.triggers.network_name}" && {
            echo "Deleting backend service: $backend"
            gcloud compute backend-services delete "$backend" --global --quiet --project=${self.triggers.project_id} || true
          }
        fi
      done

      # Remove only the specific URL map for this environment
      echo "Cleaning up URL map: ${self.triggers.url_map_name}"
      gcloud compute url-maps describe "${self.triggers.url_map_name}" --global --project=${self.triggers.project_id} >/dev/null 2>&1 && {
        echo "Deleting URL map: ${self.triggers.url_map_name}"
        gcloud compute url-maps delete "${self.triggers.url_map_name}" --global --quiet --project=${self.triggers.project_id} || true
      } || {
        echo "URL map ${self.triggers.url_map_name} not found or already deleted"
      }
EOT
  }
}
