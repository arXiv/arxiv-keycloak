terraform {
  required_version = "~> 1.13"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.2"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = "~> 1.22"
    }
  }
  backend "gcs" {
    prefix = "keycloak-auth-db"
  }
}

provider "google" {
  project = var.gcp_project_id # default inherited by all resources
  region  = var.gcp_region     # default inherited by all resources
}

# Configure postgresql provider to connect via the postgres superuser
# This provider will be used to manage database permissions
#
# Connection modes:
# 1. Direct connection: Uses public or private IP (var.use_cloud_sql_proxy = false)
# 2. Cloud SQL Proxy: Uses localhost:5432 (var.use_cloud_sql_proxy = true)
#    - Required for CI/CD environments (GitHub Actions, Cloud Build, etc.)
#    - Start proxy before terraform apply: cloud-sql-proxy <instance-connection-name>
provider "postgresql" {
  host            = var.use_cloud_sql_proxy ? "localhost" : (var.ipv4_enabled ? google_sql_database_instance.auth_db.public_ip_address : google_sql_database_instance.auth_db.private_ip_address)
  port            = 5432
  database        = var.database_name
  username        = "postgres"
  password        = google_secret_manager_secret_version.postgres_password.secret_data
  sslmode         = var.use_cloud_sql_proxy ? "disable" : "require"
  connect_timeout = 15
  superuser       = false
}

# Reserve a private IP address range for the VPC peering connection.
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "private-ip-alloc-for-services"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = var.private_network
}

# Create a private services connection (VPC peering).
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = var.private_network
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}

# Keep generating the random password when needed
resource "random_password" "keycloak_password" {
  count   = var.keycloak_password == "" ? 1 : 0
  length  = 32
  special = true
}

# Postgresql Auth DB

resource "google_sql_database_instance" "auth_db" {
  depends_on = [
    google_service_networking_connection.private_vpc_connection,
  ]
  name             = var.instance_name
  database_version = "POSTGRES_17"
  region           = var.gcp_region

  settings {
    tier = var.tier
    edition = var.environment == "prod" || var.environment == "staging" ? "ENTERPRISE_PLUS" : "ENTERPRISE"
    availability_type = var.environment == "prod" || var.environment == "staging" ? "REGIONAL" : "ZONAL"
    disk_size = var.disk_size
    disk_type = "PD_SSD"

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "02:00"
      location                       = var.gcp_region
    }

    ip_configuration {
      ipv4_enabled    = var.ipv4_enabled
      private_network = var.private_network
      #require_ssl     = var.require_ssl
      # No authorized_networks - use Cloud SQL Proxy for secure access
    }

    database_flags {
      name  = "log_statement"
      value = "all"
    }
  }

  deletion_protection = var.deletion_protection
}

resource "google_sql_database" "auth_database" {
  name     = var.database_name
  instance = google_sql_database_instance.auth_db.name
}

# Create the Secret Manager secret
resource "google_secret_manager_secret" "keycloak_password" {
  secret_id = "keycloak_password"
  project   = var.gcp_project_id

  replication {
    auto {}
  }

  labels = {
    database = var.instance_name
    purpose  = "keycloak_password"
  }
}

# Create the secret version with the password (either provided or generated)
resource "google_secret_manager_secret_version" "keycloak_password" {
  secret      = google_secret_manager_secret.keycloak_password.id
  secret_data = var.keycloak_password != "" ? var.keycloak_password : random_password.keycloak_password[0].result
}

# Use the created secret for the database user
resource "google_sql_user" "keycloak_user" {
  name     = var.keycloak_user
  instance = google_sql_database_instance.auth_db.name
  password = google_secret_manager_secret_version.keycloak_password.secret_data
}

# Set up postgres superuser password for admin operations
resource "random_password" "postgres_password" {
  count   = 1
  length  = 32
  special = true
}

resource "google_secret_manager_secret" "postgres_password" {
  secret_id = "${var.instance_name}-postgres-password"
  project   = var.gcp_project_id

  replication {
    auto {}
  }

  labels = {
    database = var.instance_name
    purpose  = "postgres-superuser-password"
  }
}

resource "google_secret_manager_secret_version" "postgres_password" {
  secret      = google_secret_manager_secret.postgres_password.id
  secret_data = random_password.postgres_password[0].result
}

resource "google_sql_user" "postgres" {
  name     = "postgres"
  instance = google_sql_database_instance.auth_db.name
  password = google_secret_manager_secret_version.postgres_password.secret_data
}

# Create client SSL certificate for secure database connections
resource "google_sql_ssl_cert" "client_cert" {
  common_name = "keycloak-client-cert"
  instance    = google_sql_database_instance.auth_db.name
}

# Grant minimal permissions to keycloak_user for database bootstrap
# Keycloak will automatically create all its tables/sequences on first startup
# This is the standard approach: create user + grant bootstrap permissions + let app handle schema

# Grant database-level permissions
resource "postgresql_grant" "keycloak_database" {
  depends_on = [
    google_sql_user.keycloak_user,
    google_sql_user.postgres,
    google_sql_database.auth_database
  ]

  database    = var.database_name
  role        = var.keycloak_user
  object_type = "database"
  privileges  = ["CREATE", "CONNECT", "TEMPORARY"]
}

# Grant schema-level permissions on public schema
resource "postgresql_grant" "keycloak_schema" {
  depends_on = [
    google_sql_user.keycloak_user,
    google_sql_user.postgres,
    google_sql_database.auth_database
  ]

  database    = var.database_name
  role        = var.keycloak_user
  schema      = "public"
  object_type = "schema"
  privileges  = ["CREATE", "USAGE"]
}

# Generate shell script that outputs SSL certificates for keycloak-service
locals {
  # Shell script that extracts database SSL certificates
  # This is mounted by keycloak-service and executed at startup
  # Includes: server CA, client cert, client key (PEM), and client key (binary DER format)

  db_certs_script = <<-EOF
#!/bin/bash
# Auto-generated by Terraform (keycloak-db module)
# This script outputs Cloud SQL SSL certificates for keycloak-service

# Server CA certificate (for validating server)
cat > server-ca.pem <<'CERT_EOF'
${google_sql_database_instance.auth_db.server_ca_cert[0].cert}
CERT_EOF

# Client certificate (for client authentication)
cat > client-cert.pem <<'CERT_EOF'
${google_sql_ssl_cert.client_cert.cert}
CERT_EOF

# Client private key (PEM format)
cat > client-key.pem <<'KEY_EOF'
${google_sql_ssl_cert.client_cert.private_key}
KEY_EOF

# Convert PEM private key to DER format (required by JDBC)
# Using client-key.pem fails with JDBC - PEM is unsupported for client key
# Only convert if openssl is available
if command -v openssl &> /dev/null; then
  openssl pkcs8 -topk8 -inform PEM -outform DER -in client-key.pem -out client-key.key -nocrypt || echo "Warning: OpenSSL conversion failed"
else
  echo "Warning: openssl not available, skipping DER conversion"
  echo "JDBC connection may fail without client-key.key in DER format"
fi

# Set appropriate permissions
chmod 644 server-ca.pem client-cert.pem client-key.pem 2>/dev/null || true
[ -f client-key.key ] && chmod 600 client-key.key

echo "Database SSL certificates extracted to $(pwd)"
ls -la *.pem *.key 2>/dev/null || ls -la *.pem
EOF
}

# Secret Manager secret for database SSL certificates
resource "google_secret_manager_secret" "authdb_certs" {
  secret_id = "authdb-certs"
  project   = var.gcp_project_id

  replication {
    auto {}
  }

  labels = {
    database = var.instance_name
    purpose  = "ssl-certificates"
  }
}

resource "google_secret_manager_secret_version" "authdb_certs" {
  secret      = google_secret_manager_secret.authdb_certs.id
  secret_data = local.db_certs_script
}