# Bootstrap Terraform Configuration
# This configuration creates the foundational AWS resources needed for Terraform state management
# and GitHub Actions OIDC authentication.

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "hoopstat-haus"
      Environment = "bootstrap"
      ManagedBy   = "terraform"
      Repository  = "efischer19/hoopstat-haus"
    }
  }
}

# Random suffix for unique resource names
resource "random_id" "suffix" {
  byte_length = 4
}

# S3 bucket for Terraform state storage
resource "aws_s3_bucket" "terraform_state" {
  bucket = "hoopstat-haus-terraform-state-${random_id.suffix.hex}"
  
  tags = {
    Name        = "Terraform State Storage"
    Description = "S3 bucket for storing Terraform state files"
  }
}

# S3 bucket versioning for state file backup
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket public access block
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB table for Terraform state locking
resource "aws_dynamodb_table" "terraform_locks" {
  name           = "hoopstat-haus-terraform-locks"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "Terraform State Locks"
    Description = "DynamoDB table for Terraform state locking"
  }
}

# GitHub OIDC Identity Provider
resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com",
  ]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = {
    Name        = "GitHub Actions OIDC"
    Description = "OIDC Identity Provider for GitHub Actions"
  }
}

# Data source to get current AWS account ID
data "aws_caller_identity" "current" {}

# IAM role for GitHub Actions (general purpose)
resource "aws_iam_role" "github_actions" {
  name = "GitHubActions-HoopstatHaus"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:efischer19/hoopstat-haus:*"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "GitHub Actions Role"
    Description = "IAM role for GitHub Actions workflows"
  }
}

# Basic policy for GitHub Actions role (minimal permissions)
resource "aws_iam_role_policy" "github_actions_basic" {
  name = "GitHubActionsBasic"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sts:GetCallerIdentity",
          "sts:TagSession"
        ]
        Resource = "*"
      }
    ]
  })
}

# Output values for use in other configurations
output "terraform_state_bucket" {
  description = "Name of the S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.bucket
}

output "terraform_locks_table" {
  description = "Name of the DynamoDB table for Terraform state locks"
  value       = aws_dynamodb_table.terraform_locks.name
}

output "github_actions_role_arn" {
  description = "ARN of the IAM role for GitHub Actions"
  value       = aws_iam_role.github_actions.arn
}

output "oidc_provider_arn" {
  description = "ARN of the GitHub OIDC Identity Provider"
  value       = aws_iam_openid_connect_provider.github_actions.arn
}

output "aws_account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}