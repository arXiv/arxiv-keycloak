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

variable "domain_name" {
  description = "The domain name for the environment (e.g., arxivd.org, arxiv.org)."
  type        = string
}
