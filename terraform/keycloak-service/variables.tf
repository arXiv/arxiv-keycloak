variable "gcp_project_id" {
  type        = string
  description = "arxiv-development, arxiv-production"
}

variable "gcp_region" {
  type        = string
  description = "us-central1"
}


variable "environment" {
  type        = string
  description = "Environment name (development, staging, production)"
}

variable "db_user" {
  type        = string
  description = "Keycloak database user"
  default     = "keycloak"
}

variable "keycloak_db_password" {
  type        = string
  description = "Password for keycloak database user. Leave empty to auto-generate. This will be passed to keycloak-db module and stored in Secret Manager."
  default     = ""
  sensitive   = true
}

variable "keycloak_image" {
  type        = string
  description = "Keycloak Docker image"
}

variable "auth_db_private_ip" {
  type        = string
  description = "Private IP of the auth database"
}

variable "auth_db_name" {
  type        = string
  description = "Name of the auth database"
}

variable "jdbc_params" {
  type        = string
  description = "JDBC connection parameters"
  default     = "sslmode=require"
}

variable "min_instances" {
  type        = string
  description = "Minimum number of Cloud Run instances"
  default     = "0"
}

variable "max_instances" {
  type        = string
  description = "Maximum number of Cloud Run instances"
  default     = "10"
}

variable "cpu_limit" {
  type        = string
  description = "CPU limit for the container"
  default     = "1000m"
}

variable "memory_limit" {
  type        = string
  description = "Memory limit for the container"
  default     = "2Gi"
}

variable "container_port" {
  type        = number
  description = "Port the container listens on"
  default     = 8080
}

variable "backend_timeout_sec" {
  type        = number
  description = "Backend service timeout in seconds"
  default     = 30
}

variable "enable_health_check" {
  type        = bool
  description = "Enable health check for the backend service"
  default     = true
}

variable "health_check_timeout" {
  type        = number
  description = "Health check timeout in seconds"
  default     = 5
}

variable "health_check_interval" {
  type        = number
  description = "Health check interval in seconds"
  default     = 30
}

variable "health_check_path" {
  type        = string
  description = "Health check path"
  default     = "/auth/health"
}

variable "additional_env_vars" {
  type        = map(string)
  description = "Additional environment variables for the container"
  default     = {}
}

variable "timeout_seconds" {
  type        = number
  description = "Request timeout in seconds"
  default     = 300
}

variable "container_concurrency" {
  type        = number
  description = "Maximum number of concurrent requests per container"
  default     = 80
}

variable "cpu_boost" {
  type        = bool
  description = "Enable CPU boost for startup"
  default     = false
}

variable "session_affinity" {
  type        = bool
  description = "Enable session affinity"
  default     = false
}

variable "vpc_egress" {
  type        = string
  description = "VPC egress setting (all-traffic or private-ranges-only)"
  default     = "private-ranges-only"
  validation {
    condition     = contains(["all-traffic", "private-ranges-only"], var.vpc_egress)
    error_message = "vpc_egress must be either 'all-traffic' or 'private-ranges-only'"
  }
}

variable "secrets" {
  type = map(object({
    secret_name = string
    version     = string
    mount_path  = optional(string)
  }))
  description = "Secrets to mount or expose as environment variables"
  default     = {}
}

variable "domain_names" {
  type        = list(string)
  description = "Domain names for the SSL certificate (e.g., ['auth.dev.arxiv.org'] or ['auth.arxiv.org'])"
  default     = []
}

variable "enable_https" {
  type        = bool
  description = "Enable HTTPS with Google-managed SSL certificate"
  default     = false
}
