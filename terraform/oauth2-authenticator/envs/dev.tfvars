# Development environment configuration
# This maps to the settings in legacy_auth_provider/Makefile and cloudbuild.yaml

gcp_project_id = "arxiv-development"
gcp_region     = "us-central1"
environment    = "development"

# Legacy Auth Provider image
oauth2_auth_image = "gcr.io/arxiv-development/arxiv-keycloak/oauth2-authenticator:latest"

# Cloud Run service configuration (from Makefile lines 55-73)
container_port        = 8080
min_instances         = "1"
max_instances         = "1"
cpu_limit             = "1"
memory_limit          = "1Gi"
timeout_seconds       = 300
container_concurrency = 2

# Performance settings
# cpu_boost        = "true"
session_affinity = "true"

# Secrets
# CLASSIC_DB_URI secret name (must exist before deployment)
# THIS NEEDS TO BE FULL ACCESS, NOT READ ONLY
# hitching on modapi db access
classic_db_uri_secret_name = "modapi_db_uri"

# Cloud SQL instance
cloudsql_instance = "arxiv-development:us-east4:arxiv-db-dev"


# SQLAlchemy settings
sqlalchemy_record_queries = "true"

# Allow unauthenticated access
allow_unauthenticated = true

tf_keycloak_bucket = "dev-arxiv-terraform-state"

# Additional environment variables (non-secret only).
# Terraform .tfvars cannot use ${ENV_VAR}; use literal values here.
# Secrets (CLASSIC_SESSION_HASH, KEYCLOAK_ADMIN_SECRET, SESSION_DURATION, AAA_API_SECRET_KEY)
# are passed via -var= or TF_VAR_* and merged in main.tf.
# ARXIV_USER_SECRET is set from Secret Manager in main.tf.
additional_env_vars = {
  KEYCLOAK_SERVER_URL       = "https://keycloak-service-874717964009.us-central1.run.app"
  CLASSIC_COOKIE_NAME       = "tapir_session"
  OIDC_SERVER_SSL_VERIFY    = "false"
  AUTH_SESSION_COOKIE_NAME = "ARXIVNG_SESSION_ID"
}
