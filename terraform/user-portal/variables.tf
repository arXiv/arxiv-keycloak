variable "gcp_project_id" {
  description = "GCP Project ID corresponding to environment"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region for resource deployments"
  type        = string
}

variable "env" {
  description = "Deployment environment - DEV or PROD"
  type        = string
}

variable "image_path" {
  description = "Path to the container image in Artifact Registry"
  type        = string
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

variable "api_secret_key" {
  description = "JWT secret key for API authentication (leave empty to auto-generate)"
  type        = string
  sensitive   = true
  default     = ""
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
