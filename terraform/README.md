# Hoopstat Haus AWS Infrastructure

This directory contains Terraform configurations for managing AWS infrastructure for the Hoopstat Haus project.

## Directory Structure

```
terraform/
├── bootstrap/          # Initial AWS setup (S3 state, OIDC provider)
├── core/              # Core infrastructure (S3, ECR, IAM)
├── modules/           # Reusable Terraform modules
└── environments/      # Environment-specific configurations
```

## Prerequisites

1. AWS CLI installed and configured
2. Terraform installed (version >= 1.0)
3. GitHub repository secrets configured
4. AWS IAM permissions for Terraform operations

## Initial Setup

### 1. Bootstrap AWS Resources

The bootstrap configuration creates the foundational AWS resources needed before Terraform can manage its own state:

```bash
cd terraform/bootstrap
terraform init
terraform plan
terraform apply
```

This creates:
- S3 bucket for Terraform state
- DynamoDB table for state locking
- IAM OIDC Identity Provider for GitHub Actions

### 2. Configure Core Infrastructure

After bootstrapping, configure the main infrastructure:

```bash
cd terraform/core
terraform init
terraform plan
terraform apply
```

This creates:
- S3 buckets for data storage
- ECR repositories for container images
- IAM roles and policies for applications

## State Management

Terraform state is stored in AWS S3 with DynamoDB locking (see ADR-016). The state configuration is:

- **S3 Bucket**: `hoopstat-haus-terraform-state-[random-id]`
- **DynamoDB Table**: `hoopstat-haus-terraform-locks`
- **State Key**: `[environment]/[component]/terraform.tfstate`

## Security

- All infrastructure follows least-privilege access principles
- IAM roles use GitHub OIDC for keyless authentication
- S3 buckets have encryption enabled by default
- VPC and security groups restrict network access

## Maintenance

- State backups are automated through S3 versioning
- Infrastructure changes require code review
- Weekly verification through GitHub Actions workflow