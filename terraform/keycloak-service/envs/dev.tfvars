# Development environment configuration
# This maps to the settings in keycloak_bend/dev-deploy.yaml

gcp_project_id = "arxiv-development"
gcp_region     = "us-central1"
environment    = "development"

# Database configuration
# These MUST come from the keycloak-db module outputs
# Do NOT hardcode these values - pass via CLI:
#   terraform apply \
#     -var="auth_db_private_ip=$(cd ../keycloak-db && terraform output -raw private_ip_address)" \
#     -var="auth_db_name=$(cd ../keycloak-db && terraform output -raw database_name)" \
#     -var="db_user=$(cd ../keycloak-db && terraform output -raw keycloak_user_name)"
# Example values:
#   auth_db_private_ip = "172.26.51.12"
#   auth_db_name       = "keycloak"
#   db_user            = "keycloak"

# Keycloak database user password - auto-generated and stored in Secret Manager
# Leave empty to auto-generate a secure random password
# keycloak_db_password = ""

# Keycloak image
keycloak_image = "us-central1-docker.pkg.dev/arxiv-development/arxiv-docker/keycloak-service:latest"

# Cloud Run service configuration
min_instances = "1"
max_instances = "1"
cpu_limit     = "1"
memory_limit  = "2Gi"
timeout_seconds = 300
container_concurrency = 80
container_port = 8080

# Performance settings
cpu_boost        = true
session_affinity = true
vpc_egress       = "private-ranges-only"

# Backend and health check configuration
backend_timeout_sec = 300
enable_health_check = true
health_check_timeout = 5
health_check_interval = 30
health_check_path = "/health/ready"

# Secrets (to be mounted)
secrets = {
  # Database SSL certificates
  # NOTE: This secret contains a shell script that outputs certificate files.
  # At startup, Keycloak runs: cd /home/keycloak/certs && sh /secrets/authdb-certs/db-certs-expand.sh
  # This is a workaround since Cloud Run doesn't support mounting multiple files from one secret.
  authdb_certs = {
    secret_name = "authdb-certs"
    version     = "latest"
    mount_path  = "/secrets/authdb-certs"
  }
}

# Keycloak startup mode: "start-dev" (development) or "start" (production)
keycloak_start                = "start-dev"
arxiv_user_registration_url   = "https://dev9.arxiv.org/user-account/register"

# Environment variables
additional_env_vars = {
  PROXY_MODE                    = "--proxy-headers=forwarded"
  KC_BOOTSTRAP_ADMIN_USERNAME   = "admin"
  BOOTSTRAP                     = "no"
  LOG_OUTPUT_FORMAT             = "--log-console-output=json"
  KC_PORT                       = "8080"
  GRPC_LOG_LEVEL                = "DEBUG"
  GRPC_TRACE                    = "tcp,http,api"
  # Keycloak audit event publishing to GCP Pub/Sub (via SPI plugin)
  GCP_EVENT_TOPIC_ID            = "keycloak-arxiv-events"
  GCP_ADMIN_EVENT_TOPIC_ID      = "keycloak-arxiv-events"
}

# HTTPS and SSL certificate configuration
# Enable HTTPS with Google-managed SSL certificate
enable_https = true
domain_names = ["auth.dev.arxiv.org"]

vpc_connector_name = "clourrunconnector"