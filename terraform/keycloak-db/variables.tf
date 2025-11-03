variable "gcp_project_id" {
  type        = string
  description = "arxiv-development, arxiv-production"
}

variable "gcp_region" {
  type        = string
  description = "us-central1"
}

variable "instance_name" {
  type        = string
  description = "Name of the database instance"
}

variable "tier" {
  type        = string
  description = "Database tier (e.g., db-custom-2-4096)"
  default     = "db-f1-micro"
}

variable "disk_size" {
  type        = number
  description = "Disk size in GB"
  default     = 10
}

variable "ipv4_enabled" {
  type        = bool
  description = "Enable IPv4 for the database"
  default     = true
}

variable "private_network" {
  type        = string
  description = "Private network for the database"
  default     = null
}

variable "database_name" {
  type        = string
  description = "Name of the database to create"
}

variable "db_username" {
  type        = string
  description = "Database user name"
}

variable "db_password" {
  type        = string
  description = "Database user password. Leave empty to auto-generate a secure random password. Password is stored in Secret Manager."
  default     = ""
  sensitive   = true
}

variable "deletion_protection" {
  type        = bool
  description = "Enable deletion protection"
  default     = false
}

variable "require_ssl" {
  type        = bool
  description = "Require SSL/TLS connections with trusted client certificates"
  default     = true
}
