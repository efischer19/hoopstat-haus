# GitHub Actions IAM Role Configuration

## Overview

The GitHub Actions IAM role (`hoopstat-haus-github-actions`) must be created manually outside of Terraform to avoid a circular dependency during the bootstrap process. This document specifies the exact configuration required for this role.

## Role Configuration

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

The role needs the following permissions to deploy and manage the infrastructure:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::hoopstat-haus-prod-data",
        "arn:aws:s3:::hoopstat-haus-prod-data/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:GetAuthorizationToken",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    }
  ]
}
```

## Purpose of Each Permission Set

### S3 Permissions
- **Target**: The main application data bucket (`hoopstat-haus-prod-data`)
- **Use**: Storing and retrieving application artifacts, data files, and build outputs
- **Actions**: Full object lifecycle management within the project bucket

### ECR Permissions
- **Target**: All ECR repositories (using `*` due to ECR access patterns)
- **Use**: Building, pushing, and pulling Docker container images
- **Actions**: Complete container registry operations for CI/CD pipeline

### CloudWatch Logs Permissions
- **Target**: All log groups (using `*` for operational flexibility)
- **Use**: Creating and writing to log groups for application monitoring
- **Actions**: Full logging capabilities for observability infrastructure

## Manual Creation Steps

1. **Prerequisites**: Ensure the GitHub OIDC provider exists in your AWS account
2. **Create Role**: Use the trust policy above to create the role
3. **Attach Policy**: Create and attach an inline policy with the permissions above
4. **Verify**: Test that GitHub Actions can assume the role successfully

## Bootstrap Process

Once this role is created manually:
1. GitHub Actions can assume the role
2. Terraform can manage all other infrastructure resources
3. The bootstrap dependency is resolved

## Why This Approach?

This manual approach resolves the circular dependency where:
- Terraform needs the GitHub Actions role to deploy infrastructure
- But the GitHub Actions role was defined in the Terraform infrastructure

By managing this one role outside of Terraform, we enable a clean bootstrap process while keeping all other infrastructure as code.