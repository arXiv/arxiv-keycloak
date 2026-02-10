variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region for Cloud Run service"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (development, production, etc.)"
  type        = string
}

variable "oauth2_auth_image" {
  description = "Docker image for Legacy Auth Provider"
  type        = string
  default     = "gcr.io/arxiv-development/arxiv-keycloak/legacy-auth-provider:latest"
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8080
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = string
  default     = "1"
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = string
  default     = "1"
}

variable "cpu_limit" {
  description = "CPU limit"
  type        = string
  default     = "1"
}

variable "memory_limit" {
  description = "Memory limit"
  type        = string
  default     = "1Gi"
}

variable "timeout_seconds" {
  description = "Request timeout in seconds"
  type        = number
  default     = 300
}

variable "container_concurrency" {
  description = "Maximum concurrent requests per container"
  type        = number
  default     = 2
}

variable "cpu_boost" {
  description = "Enable CPU boost"
  type        = string
  default     = "true"
}

variable "session_affinity" {
  description = "Enable session affinity"
  type        = string
  default     = "true"
}

variable "classic_db_uri_secret_name" {
  description = "Secret Manager secret name for CLASSIC_DB_URI"
  type        = string
  default     = "browse-sqlalchemy-db-uri"
}

variable "sqlalchemy_record_queries" {
  description = "Enable SQLAlchemy query recording"
  type        = string
  default     = "true"
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to the service"
  type        = bool
  default     = true
}

variable "additional_env_vars" {
  description = "Additional environment variables"
  type        = map(string)
  default     = {}
}

variable "cloudsql_instance" {
  description = "Cloud SQL instance connection name (format: project:region:instance)"
  type        = string
}

variable "image_digest" {
  description = "Docker image digest to force new revision on image changes"
  type        = string
  default     = ""
}

variable "arxiv_user_client_secret" {
  description = "OIDC arXiv client secret"
  type        = string
  sensitive   = true
  default     = ""
}

variable "tf_keycloak_bucket" {
  description = "Terraform Keycloak bucket"
  type        = string
  sensitive   = true
  default     = ""
}

# Secret env vars (pass via -var= or TF_VAR_* in CI; cannot use ${VAR} in .tfvars)
variable "classic_session_hash" {
  description = "CLASSIC_SESSION_HASH for the container"
  type        = string
  sensitive   = true
  default     = ""
}

variable "kc_admin_password" {
  description = "KEYCLOAK_ADMIN_SECRET (admin client secret)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "classic_session_duration" {
  description = "SESSION_DURATION for the container"
  type        = string
  sensitive   = true
  default     = ""
}

variable "aaa_api_token" {
  description = "AAA_API_SECRET_KEY (API bearer token)"
  type        = string
  sensitive   = true
  default     = ""
}

