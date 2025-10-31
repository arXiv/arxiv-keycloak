terraform {
  backend "gcs" {
    # Bucket and prefix must be provided during init using -backend-config
    # Example for dev:
    # terraform init -backend-config="bucket=arxiv-terraform-state-dev" -backend-config="prefix=dev-env"
    #
    # Example for a new "mike" environment:
    # terraform init -backend-config="bucket=arxiv-terraform-state-dev" -backend-config="prefix=mike-env"
  }
}