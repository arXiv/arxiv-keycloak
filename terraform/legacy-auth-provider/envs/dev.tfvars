# Development environment configuration
# This maps to the settings in legacy_auth_provider/Makefile and cloudbuild.yaml

gcp_project_id = "arxiv-development"
gcp_region     = "us-central1"
environment    = "development"

# Legacy Auth Provider image
legacy_auth_image = "gcr.io/arxiv-development/arxiv-keycloak/legacy-auth-provider:latest"

# Cloud Run service configuration (from Makefile lines 55-73)
container_port        = 8080
min_instances         = "1"
max_instances         = "1"
cpu_limit             = "1"
memory_limit          = "1Gi"
timeout_seconds       = 300
container_concurrency = 2

# Performance settings
cpu_boost        = "true"
session_affinity = "true"

# Secrets
# CLASSIC_DB_URI secret name (must exist before deployment)
classic_db_uri_secret_name = "browse-sqlalchemy-db-uri"

# Cloud SQL instance
cloudsql_instance = "arxiv-development:us-east4:arxiv-db-dev"

# API_SECRET_KEY (JWT) - Auto-generated if not provided
# Leave empty to auto-generate a secure random secret
# Or set via CLI: -var="api_secret_key=YOUR_SECRET"
# api_secret_key = ""

# SQLAlchemy settings
sqlalchemy_record_queries = "true"

# Allow unauthenticated access
allow_unauthenticated = true

# Additional environment variables (if needed)
additional_env_vars = {}
