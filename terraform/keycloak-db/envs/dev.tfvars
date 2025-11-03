# Development environment configuration

gcp_project_id = "arxiv-development"
gcp_region     = "us-central1"

# Database instance configuration
instance_name = "authdb"
tier          = "db-f1-micro"
disk_size     = 10                  # GB

# Network configuration
# Set to false to use private IP only (recommended with VPC)
ipv4_enabled = true
private_network = "projects/arxiv-development/global/networks/default"

# Security configuration
# Require SSL/TLS connections with trusted client certificates
require_ssl = true

# Database and users
database_name = "keycloak"
db_username   = "postgres"  # Main admin user

# Passwords
# db_password: Leave empty to auto-generate. Stored in {instance_name}-db-password secret.
# keycloak_password: Provided by keycloak-service module. Pass via CLI:
#   -var="keycloak_password=$(cd ../keycloak-service && terraform output -raw keycloak_db_password)"

# Protection
deletion_protection = true  # Set to true for production

