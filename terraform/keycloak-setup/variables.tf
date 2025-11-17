variable "gcp_project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-east1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "realm_config_file_path" {
  description = "Path to the realm configuration JSON file (relative to module root)"
  type        = string
  default     = "../../keycloak_bend/realms/arxiv-realm-gcp-dev.json"
}

variable "setup_job_image" {
  description = "Docker image for the Keycloak setup job"
  type        = string
  default     = "gcr.io/arxiv-development/arxiv-keycloak/keycloak-setup:latest"
}

variable "keycloak_url" {
  description = "URL of the Keycloak service"
  type        = string
}

variable "keycloak_admin_password_secret_name" {
  description = "Name of the Secret Manager secret containing the Keycloak admin password"
  type        = string
  default     = "keycloak-admin-password"
}

variable "arxiv_user_secret" {
  description = "OAuth2 client secret for the arxiv-user client"
  type        = string
  sensitive   = true
}

variable "legacy_auth_api_token_secret_name" {
  description = "Secret Manager secret name for legacy auth API token (from legacy-auth-provider module output: api_secret_key_secret_name)"
  type        = string
  default     = "jwt_secret"
}

variable "legacy_auth_uri" {
  description = "URI for the legacy authentication provider (from legacy-auth-provider module output: service_url)"
  type        = string
  default     = ""
}

variable "realm_name" {
  description = "Name of the Keycloak realm to configure"
  type        = string
  default     = "arxiv"
}

variable "auto_trigger_setup" {
  description = "Automatically trigger the setup job after creation/update"
  type        = bool
  default     = false
}
