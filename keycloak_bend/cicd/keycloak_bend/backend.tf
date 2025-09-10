terraform {
  backend "gcs" {
    # Bucket name will be provided via -backend-config during terraform init
    bucket = var.terraform_state_bucket
  }
}