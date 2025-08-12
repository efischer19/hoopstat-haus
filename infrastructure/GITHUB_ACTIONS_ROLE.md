# GitHub Actions IAM Roles Configuration

## Overview

The GitHub Actions workflows use a **two-role security model** that separates infrastructure administration from day-to-day operations:

1. **Infrastructure Administration Role** (`hoopstat-haus-github-actions`) - Externally managed
2. **Operations Role** (`hoopstat-haus-operations`) - Managed in Terraform

This separation implements the principle of least privilege and reduces the blast radius if CI/CD workflows are compromised.

## Infrastructure Administration Role

### Role: `hoopstat-haus-github-actions`

**Purpose**: Infrastructure deployment and administrative tasks
**Management**: Created manually outside of Terraform to avoid circular dependency
**Used By**: Infrastructure workflow (`infrastructure.yml`)

This role must be created manually outside of Terraform to avoid a circular dependency during the bootstrap process.

### Trust Policy

The role should trust the GitHub OIDC provider and allow the `efischer19/hoopstat-haus` repository to assume it:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::{ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:efischer19/hoopstat-haus:*"
        }
      }
    }
  ]
}
```

### Required Permissions Policy

The infrastructure admin role needs comprehensive permissions to deploy and manage the infrastructure:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow", 
      "Action": [
        "ecr:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## Operations Role

### Role: `hoopstat-haus-operations`

**Purpose**: Day-to-day application operations with least-privilege access
**Management**: Managed in Terraform (`infrastructure/main.tf`)
**Used By**: CI workflow (`ci.yml`) and deployment workflow (`deploy.yml`)

This role is automatically created by Terraform and has restricted permissions for runtime operations only.

### Permissions Summary

The operations role has access to:
- **ECR**: Push/pull container images to `hoopstat-haus/prod` repository
- **S3**: Object operations on medallion buckets (bronze/silver/gold/access_logs/main)
- **CloudWatch Logs**: Create log streams and write events to `/hoopstat-haus/*` log groups

The operations role **explicitly denies**:
- S3 bucket management (creation, deletion, policy changes)
- ECR repository management
- IAM operations
- CloudWatch management operations

### Automatic Configuration

When you run `terraform apply`, this role is automatically created with the correct:
- OIDC trust policy for GitHub Actions
- Least-privilege permissions for operations
- Explicit denials for administrative actions

## Role Usage by Workflow

| Workflow | Role Used | Purpose |
|----------|-----------|---------|
| `infrastructure.yml` | `hoopstat-haus-github-actions` | Deploy/modify infrastructure |
| `ci.yml` | `hoopstat-haus-operations` | Build and push container images |
| `deploy.yml` | `hoopstat-haus-operations` | Deploy applications |

## Manual Creation Steps (Admin Role Only)

The operations role is created automatically by Terraform. Only the admin role needs manual creation:

1. **Prerequisites**: Ensure the GitHub OIDC provider exists in your AWS account
2. **Create Role**: Use the trust policy above to create the `hoopstat-haus-github-actions` role
3. **Attach Policy**: Create and attach an inline policy with the administrative permissions above
4. **Deploy Infrastructure**: Run Terraform to create the operations role and other resources
5. **Verify**: Test that both infrastructure and CI/deploy workflows work correctly

## Bootstrap Process

The bootstrap sequence is:
1. Manually create `hoopstat-haus-github-actions` role
2. Infrastructure workflow uses admin role to deploy Terraform
3. Terraform creates `hoopstat-haus-operations` role automatically
4. CI/deploy workflows use the operations role for runtime tasks

## Security Benefits

This two-role model provides:
- **Least Privilege**: Operations workflows cannot modify infrastructure
- **Separation of Concerns**: Infrastructure changes require explicit admin role usage
- **Defense in Depth**: Compromised CI workflows cannot escalate privileges
- **Audit Trail**: Clear separation between administrative and operational actions