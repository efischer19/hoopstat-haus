# Terraform Import Guide

This document provides the manual steps required to import existing AWS resources into the Terraform state. These resources were created outside of Terraform and need to be imported before `terraform apply` can succeed.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform initialized in the infrastructure directory
- Access to the AWS account where resources exist

## Required Imports

The following AWS resources already exist and must be imported into Terraform state:

### 1. GitHub OIDC Provider (if it exists)

First, check if the OIDC provider exists:
```bash
aws iam list-open-id-connect-providers
```

If you see `https://token.actions.githubusercontent.com` in the output, the provider exists and the Terraform data source will work correctly. No import is needed for data sources.

If the provider does not exist, you need to create it first following the instructions in [SETUP.md](./SETUP.md).

### 2. IAM Role: hoopstat-haus-github-actions

```bash
terraform import aws_iam_role.github_actions hoopstat-haus-github-actions
```

### 3. IAM Role: hoopstat-haus-lambda-logging

```bash
terraform import aws_iam_role.lambda_logging hoopstat-haus-lambda-logging
```

### 4. S3 Bucket: hoopstat-haus-prod-data

```bash
terraform import aws_s3_bucket.main hoopstat-haus-prod-data
```

### 5. ECR Repository: hoopstat-haus/prod

```bash
terraform import aws_ecr_repository.main hoopstat-haus/prod
```

## Import Procedure

1. **Navigate to infrastructure directory:**
   ```bash
   cd infrastructure
   ```

2. **Ensure Terraform is initialized:**
   ```bash
   terraform init
   ```

3. **Run each import command:**
   Execute the import commands above one by one. Each command should complete successfully before proceeding to the next.

4. **Verify the import:**
   ```bash
   terraform plan
   ```
   
   After successful imports, `terraform plan` should show minimal changes, primarily related to:
   - Additional resource attributes not present in existing resources
   - Terraform-managed tags and configurations
   - Related resources that don't exist yet (S3 bucket policies, ECR lifecycle policies, etc.)

## Expected Behavior After Import

Once all resources are imported:

- ✅ `terraform plan` should complete without errors
- ✅ `terraform apply` should only create missing related resources (policies, configurations, etc.)
- ✅ No existing resources should be destroyed or recreated
- ✅ GitHub Actions workflows should be able to deploy infrastructure changes

## Troubleshooting

### Import Fails with "Resource Not Found"
- Verify the resource exists in AWS console
- Check that you're using the correct AWS region (us-east-1)
- Ensure your AWS credentials have permission to read the resource

### Import Fails with "Resource Already Exists in State"
- The resource has already been imported
- Run `terraform state list` to see what's already in state
- Skip to the next import command

### Plan Shows Unexpected Changes After Import
- This is normal for the first import
- Review the changes to ensure they're adding configurations, not destroying resources
- If destructive changes are shown, stop and investigate before applying

## Security Note

These import operations only affect Terraform state management and do not modify the actual AWS resources. The existing resources will continue to function normally throughout the import process.