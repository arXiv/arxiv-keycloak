variable "gcp_project_id" {
  description = "The GCP Project ID."
  type        = string
}

variable "gcp_region" {
  description = "The GCP Region."
  type        = string
}

variable "db_addr" {
  description = "The database address for Keycloak."
  type        = string
}

variable "proxy_mode" {
  description = "The proxy mode for Keycloak."
  type        = string
}

variable "kc_bootstrap_admin_username" {
  description = "The bootstrap admin username for Keycloak."
  type        = string
}

variable "bootstrap" {
  description = "Bootstrap setting for Keycloak."
  type        = string
}

variable "log_output_format" {
  description = "Log output format for Keycloak."
  type        = string
}

variable "kc_port" {
  description = "Keycloak port."
  type        = string
}

variable "grpc_log_level" {
  description = "gRPC log level."
  type        = string
}

variable "grpc_trace" {
  description = "gRPC trace settings."
  type        = string
}

variable "arxiv_user_registration_url" {
  description = "Arxiv user registration URL."
  type        = string
}

variable "kc_hostname" {
  description = "Keycloak hostname."
  type        = string
}

variable "min_scale" {
  description = "Minimum number of instances for autoscaling."
  type        = number
}

variable "max_scale" {
  description = "Maximum number of instances for autoscaling."
  type        = number
}

variable "terraform_state_bucket" {
  description = "GCS bucket name for storing Terraform state."
  type        = string
} 