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

# Additional environment variables (if needed)
additional_env_vars = {
  KEYCLOAK_SERVER_URL = "https://keycloak-service-874717964009.us-central1.run.app"

  ARXIV_USER_SECRET: ${KEYCLOAK_TEST_CLIENT_SECRET}
  CLASSIC_SESSION_HASH: ${CLASSIC_SESSION_HASH}
  KEYCLOAK_ADMIN_SECRET: ${KC_ADMIN_PASSWORD}

  CLASSIC_COOKIE_NAME: tapir_session

  SESSION_DURATION: ${CLASSIC_SESSION_DURATION}
  # Keycloak SSL is running with self-signed cert
  OIDC_SERVER_SSL_VERIFY = "false"
  #
  # This is the almighty admin client (admin-cli) secret
  #
  #
  # Do not set DOMAIN - this is to designate the cookie domain and for
  # local run, having this is harmful.
  # In production, this is probably set to .arxiv.org
  # DOMAIN: localhost
  #
  # API bearer token
  AAA_API_SECRET_KEY: ${AAA_API_TOKEN}
  AUTH_SESSION_COOKIE_NAME: "ARXIVNG_SESSION_ID"
}
