terraform {
  backend "gcs" {
    # Bucket name will be provided via -backend-config during terraform init
    bucket = var.terraform_state_bucket

    # Bucket and prefix must be provided during init using -backend-config
    # Example for dev:
    # terraform init -backend-config="bucket=arxiv-terraform-state-dev" -backend-config="prefix=dev-keycloak"
    #
    # Example for a new "mike" environment:
    # terraform init -backend-config="bucket=arxiv-terraform-state-dev" -backend-config="prefix=mike-keycloak"
  }
}