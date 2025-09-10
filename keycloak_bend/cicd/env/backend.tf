terraform {
  backend "gcs" {
    bucket = var.terraform_state_bucket
  }
}