variable "gcp_project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "environment_name" {
  description = "The name of the environment (e.g., dev, prod)."
  type        = string
}

variable "gcp_region" {
  description = "The GCP region to deploy resources in."
  type        = string
  default     = "us-central1"
}

variable "terraform_state_bucket" {
  description = "The GCS bucket to store the Terraform state file."
  type        = string
}

variable "keycloak_cloud_run_service_name" {
  description = "The name of the Keycloak Cloud Run service."
  type        = string
  default     = "keycloak-service" # Default from keycloak_service.yaml
}

variable "min_scale" {
  description = "Minimum number of instances for Cloud Run."
  type        = number
  default     = 1
}

variable "max_scale" {
  description = "Maximum number of instances for Cloud Run."
  type        = number
  default     = 1
}

variable "db_addr" {
  description = "Database address for Keycloak."
  type        = string
  default     = ""
}

variable "proxy_mode" {
  description = "Proxy mode for Keycloak."
  type        = string
  default     = "--proxy-headers=forwarded"
}

variable "kc_bootstrap_admin_username" {
  description = "Keycloak bootstrap admin username."
  type        = string
  default     = "admin"
}

variable "bootstrap" {
  description = "Enable Keycloak bootstrap."
  type        = string
  default     = "no"
}

variable "log_output_format" {
  description = "Log output format for Keycloak."
  type        = string
  default     = "--log-console-output=json"
}

variable "kc_port" {
  description = "Keycloak container port."
  type        = string
  default     = "8080"
}

variable "grpc_log_level" {
  description = "gRPC log level for Keycloak."
  type        = string
  default     = "DEBUG"
}

variable "grpc_trace" {
  description = "gRPC trace settings for Keycloak."
  type        = string
  default     = "tcp,http,api"
}

variable "arxiv_user_registration_url" {
  description = "URL for arXiv user registration."
  type        = string
  default     = ""
}

# variable "kc_hostname" {
#   description = "Keycloak hostname."
#   type        = string
#   default     = ""
# } 