# Development environment configuration

gcp_project_id = "arxiv-development"
gcp_region     = "us-central1"

# Database instance configuration
instance_name = "authdb"
tier          = "db-g1-small"
disk_size     = 10                  # GB

# Network configuration
# Set to false to use private IP only (recommended with VPC)
ipv4_enabled = true
private_network = "projects/arxiv-production/global/networks/default"

# Security configuration
# Require SSL/TLS connections with trusted client certificates
require_ssl = true

# Database and users
database_name = "keycloak"

# Passwords
# keycloak_password: Leave empty to auto-generate. Pass via CLI if needed:
#   -var="keycloak_password=YOUR_PASSWORD"

# Protection
deletion_protection = true  # Set to true for production
