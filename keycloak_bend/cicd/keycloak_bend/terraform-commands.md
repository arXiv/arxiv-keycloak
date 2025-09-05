# Terraform Commands for arXiv Keycloak Infrastructure

## Prerequisites

### 1. Create State Buckets
```bash
# Create development state bucket
gsutil mb gs://arxiv-terraform-state-dev

# Create production state bucket  
gsutil mb gs://arxiv-terraform-state-prod

# Enable versioning on both buckets (recommended for state file history)
gsutil versioning set on gs://arxiv-terraform-state-dev
gsutil versioning set on gs://arxiv-terraform-state-prod

# Set appropriate permissions (replace with your service account)
gsutil iam ch serviceAccount:terraform-dev-sa@arxiv-development.iam.gserviceaccount.com:objectAdmin gs://arxiv-terraform-state-dev
gsutil iam ch serviceAccount:terraform-prod-sa@arxiv-production.iam.gserviceaccount.com:objectAdmin gs://arxiv-terraform-state-prod
```

### 2. Create Service Accounts
```bash
# Create development service account
gcloud iam service-accounts create terraform-dev-sa \
  --display-name="Terraform Development Service Account" \
  --description="Service account for Terraform infrastructure management in development environment" \
  --project=arxiv-development

# Create production service account
gcloud iam service-accounts create terraform-prod-sa \
  --display-name="Terraform Production Service Account" \
  --description="Service account for Terraform infrastructure management in production environment" \
  --project=arxiv-production
```

### 3. Grant Required Permissions
```bash
# Development environment permissions
gcloud projects add-iam-policy-binding arxiv-development \
  --member="serviceAccount:terraform-dev-sa@arxiv-development.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding arxiv-development \
  --member="serviceAccount:terraform-dev-sa@arxiv-development.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding arxiv-development \
  --member="serviceAccount:terraform-dev-sa@arxiv-development.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Production environment permissions
gcloud projects add-iam-policy-binding arxiv-production \
  --member="serviceAccount:terraform-prod-sa@arxiv-production.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding arxiv-production \
  --member="serviceAccount:terraform-prod-sa@arxiv-production.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding arxiv-production \
  --member="serviceAccount:terraform-prod-sa@arxiv-production.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

## Development Environment Commands

### Initialize Terraform for Development
```bash
# Navigate to the terraform directory
cd keycloak_bend/cicd/keycloak_bend

# Initialize with development state bucket
terraform init -backend-config="bucket=arxiv-terraform-state-dev"

# Verify backend configuration
terraform init -backend-config="bucket=arxiv-terraform-state-dev" -reconfigure
```

### Plan Development Infrastructure
```bash
# Plan changes for development environment
terraform plan -var-file="dev.tfvars"

# Plan with detailed output
terraform plan -var-file="dev.tfvars" -detailed-exitcode

# Plan and save to file for review
terraform plan -var-file="dev.tfvars" -out=dev.tfplan
```

### Apply Development Infrastructure
```bash
# Apply changes to development environment
terraform apply -var-file="dev.tfvars"

# Apply with auto-approve (for CI/CD)
terraform apply -var-file="dev.tfvars" -auto-approve

# Apply from saved plan file
terraform apply dev.tfplan
```

### Development Environment Management
```bash
# Show current state
terraform show

# List all resources
terraform state list

# Get specific resource details
terraform state show google_cloud_run_service.keycloak

# Import existing resource (if needed)
terraform import google_cloud_run_service.keycloak locations/us-central1/namespaces/arxiv-development/services/keycloak

# Remove resource from state (without destroying)
terraform state rm google_cloud_run_service.keycloak

# Refresh state from actual infrastructure
terraform refresh -var-file="dev.tfvars"
```

## Production Environment Commands

### Initialize Terraform for Production
```bash
# Initialize with production state bucket
terraform init -backend-config="bucket=arxiv-terraform-state-prod"

# Verify backend configuration
terraform init -backend-config="bucket=arxiv-terraform-state-prod" -reconfigure
```

### Plan Production Infrastructure
```bash
# Plan changes for production environment
terraform plan -var-file="prod.tfvars"

# Plan with detailed output
terraform plan -var-file="prod.tfvars" -detailed-exitcode

# Plan and save to file for review
terraform plan -var-file="prod.tfvars" -out=prod.tfplan
```

### Apply Production Infrastructure
```bash
# Apply changes to production environment (manual approval)
terraform apply -var-file="prod.tfvars"

# Apply with auto-approve (for CI/CD)
terraform apply -var-file="prod.tfvars" -auto-approve

# Apply from saved plan file
terraform apply prod.tfplan
```

## Manual Environment Commands

### Deploy to Custom Environment (e.g., staging)
```bash
# Initialize with custom environment bucket
terraform init -backend-config="bucket=arxiv-terraform-state-staging"

# Plan for staging environment
terraform plan -var-file="staging.tfvars"

# Apply to staging environment
terraform apply -var-file="staging.tfvars"
```

## Utility Commands

### State Management
```bash
# List all resources in state
terraform state list

# Show specific resource
terraform state show google_cloud_run_service.keycloak

# Move resource in state (rename)
terraform state mv google_cloud_run_service.keycloak google_cloud_run_service.keycloak_new

# Remove resource from state
terraform state rm google_cloud_run_service.keycloak

# Import existing resource
terraform import google_cloud_run_service.keycloak locations/us-central1/namespaces/arxiv-development/services/keycloak
```

### Output and Information
```bash
# Show all outputs
terraform output

# Show specific output
terraform output keycloak_url

# Show current configuration
terraform show

# Validate configuration
terraform validate

# Format configuration files
terraform fmt -recursive

# Check for security issues
terraform plan -var-file="dev.tfvars" | grep -i "security\|warning\|error"
```

### Cleanup Commands
```bash
# Destroy all resources (DANGER!)
terraform destroy -var-file="dev.tfvars"

# Destroy specific resource
terraform destroy -target=google_cloud_run_service.keycloak -var-file="dev.tfvars"

# Remove .terraform directory (force re-initialization)
rm -rf .terraform .terraform.lock.hcl
```

## CI/CD Integration Commands

### Cloud Build Trigger Commands
```bash
# Trigger development deployment
gcloud builds submit \
  --config=keycloak_bend/cicd/cloudbuild-infra.yaml \
  --substitutions=_ENVIRONMENT=dev

# Trigger production deployment
gcloud builds submit \
  --config=keycloak_bend/cicd/cloudbuild-infra.yaml \
  --substitutions=_ENVIRONMENT=prod

# Trigger staging deployment
gcloud builds submit \
  --config=keycloak_bend/cicd/cloudbuild-infra.yaml \
  --substitutions=_ENVIRONMENT=staging
```

### Local Testing Commands
```bash
# Test configuration locally
terraform validate

# Test with different variable files
terraform plan -var-file="dev.tfvars"
terraform plan -var-file="prod.tfvars"

# Test backend configuration
terraform init -backend-config="bucket=arxiv-terraform-state-dev" -reconfigure
```

## Troubleshooting Commands

### Debug and Diagnostics
```bash
# Enable debug logging
export TF_LOG=DEBUG
terraform plan -var-file="dev.tfvars"

# Check provider versions
terraform version

# Validate configuration
terraform validate

# Check for unused variables
terraform plan -var-file="dev.tfvars" 2>&1 | grep -i "unused\|deprecated"

# Force unlock state (if locked)
terraform force-unlock <LOCK_ID>
```

### Common Issues
```bash
# Re-initialize if backend issues
rm -rf .terraform .terraform.lock.hcl
terraform init -backend-config="bucket=arxiv-terraform-state-dev"

# Refresh state if drift detected
terraform refresh -var-file="dev.tfvars"

# Import missing resources
terraform import google_cloud_run_service.keycloak locations/us-central1/namespaces/arxiv-development/services/keycloak
```

## Best Practices

1. **Always run plan before apply** in production
2. **Use versioned state buckets** for backup and recovery
3. **Separate state files** for different environments
4. **Use service accounts** with minimal required permissions
5. **Review changes** before applying in production
6. **Keep tfvars files** in version control (without secrets)
7. **Use terraform fmt** to maintain consistent formatting
8. **Regular state refresh** to detect drift
