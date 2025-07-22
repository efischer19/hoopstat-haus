# Infrastructure

This directory contains the Terraform configuration for managing the cloud infrastructure of the Hoopstat Haus project.

## Overview

The infrastructure is managed using Terraform and deployed via GitHub Actions. The setup follows the principles outlined in our ADRs:

- **ADR-007**: Uses GitHub Actions for CI/CD workflows
- **ADR-009**: Targets AWS as the cloud provider  
- **ADR-010**: Uses Terraform for Infrastructure as Code
- **ADR-011**: Uses GitHub OIDC with AWS IAM Roles for secure authentication

## Architecture

The infrastructure includes:

- **S3 Bucket**: Primary storage for application data and artifacts
- **ECR Repository**: Container registry for Docker images
- **IAM Roles**: Least-privilege access roles for different services
- **OIDC Provider**: GitHub OIDC integration for keyless authentication
- **CloudWatch Observability** (ADR-018): Log groups, metrics, alarms, and monitoring
- **SNS Topics**: Alert routing for critical and warning notifications

## Deployment Workflow

### Automatic Deployment
- **Plan on PR**: When a PR is opened that modifies infrastructure files, a Terraform plan is automatically generated and posted as a comment
- **Apply on Merge**: When changes are merged to the main branch, Terraform apply is automatically executed

### Manual Deployment
- Manual deployment can be triggered via the GitHub Actions "workflow_dispatch" event
- Useful for emergency fixes or one-off infrastructure changes

## Security

- No long-lived AWS credentials are stored in GitHub
- Authentication uses GitHub OIDC with temporary tokens
- IAM roles follow the principle of least privilege
- S3 bucket includes encryption and access controls
- ECR repository includes image scanning and lifecycle policies

## Usage

### Local Development
For local testing (not recommended for production changes):

```bash
cd infrastructure
terraform init
terraform plan
```

### Making Infrastructure Changes
1. Create a new branch
2. Modify the Terraform configuration files
3. Open a PR - this will trigger a Terraform plan
4. Review the plan output in the PR comments
5. Merge the PR - this will trigger Terraform apply

**Note:** If this is the first deployment, you may need to import existing resources first. See [IMPORT.md](./IMPORT.md) for instructions.

### ECR Integration
The infrastructure includes a fully configured ECR repository (`hoopstat-haus/prod`) that:
- Automatically scans images for vulnerabilities on push
- Applies lifecycle policies to manage storage costs
- Integrates with GitHub Actions for automated CI/CD
- See [ECR Image Management Guide](../docs/ECR_IMAGE_MANAGEMENT.md) for detailed usage

## File Structure

- `main.tf` - Main Terraform configuration
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `versions.tf` - Provider and Terraform version constraints
- `.terraform-version` - Terraform version specification
- `IMPORT.md` - Guide for importing existing AWS resources
- `SETUP.md` - One-time setup instructions