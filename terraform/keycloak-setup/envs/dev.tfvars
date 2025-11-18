# Development environment configuration
# This configures the Keycloak realm setup job for the development environment

gcp_project_id = "arxiv-development"
gcp_region     = "us-central1"
environment    = "development"

# Keycloak service URL - UPDATE THIS with actual Cloud Run service URL
# Get from: cd ../keycloak-service && terraform output keycloak_url
# Example: "https://keycloak-xxxxx-uc.a.run.app"
# The actual URL is given as an input.
keycloak_url = "https://keycloak-should-come-in-deploy-step-uc.a.run.app"

# Path to realm configuration file (relative to module root)
realm_config_file_path = "../../keycloak_bend/realms/arxiv-realm-gcp-dev.json"

# Docker image for setup job
# This should be built by the GitHub Actions workflow
setup_job_image = "gcr.io/arxiv-development/arxiv-keycloak/keycloak-setup:latest"

# Keycloak admin password secret (created by keycloak-service module)
keycloak_admin_password_secret_name = "keycloak-admin-password"

# Secrets - DO NOT commit these values!
# Set via environment variables:
#   export TF_VAR_arxiv_user_secret="your-secret"
# Or pass via CLI:
#   terraform apply -var-file=envs/dev.tfvars \
#     -var="arxiv_user_secret=YOUR_SECRET"

# arxiv_user_secret = ""  # OAuth2 client secret for arxiv-user client

# Legacy auth provider outputs (from legacy-auth-provider module)
# These MUST come from the legacy-auth-provider module outputs
# Do NOT hardcode these values - pass via CLI:
#   terraform apply -var-file=envs/dev.tfvars \
#     -var="legacy_auth_api_token_secret_name=$(cd ../legacy-auth-provider && terraform output -raw api_secret_key_secret_name)" \
#     -var="legacy_auth_uri=$(cd ../legacy-auth-provider && terraform output -raw service_url)" \
#     -var="arxiv_user_secret=YOUR_SECRET"
# Example values:
#   legacy_auth_api_token_secret_name = "legacy_auth_api_token"
#   legacy_auth_uri = "https://legacy-auth-provider-xxxxx-uc.a.run.app"

# Realm name to configure
realm_name = "arxiv"

# Auto-trigger setup job after terraform apply
# Set to true only for initial setup or when you want automatic configuration
# For safety, keep false and trigger manually with:
#   gcloud run jobs execute keycloak-realm-setup-development --region us-central1 --project arxiv-development
auto_trigger_setup = false
