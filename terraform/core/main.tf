# Core Infrastructure Configuration
# This configuration creates the main AWS resources for the Hoopstat Haus project

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Backend configuration - update these values after bootstrap
  backend "s3" {
    # bucket         = "hoopstat-haus-terraform-state-[suffix]"  # Update after bootstrap
    # key            = "core/terraform.tfstate"
    # region         = "us-east-1"
    # dynamodb_table = "hoopstat-haus-terraform-locks"
    # encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "hoopstat-haus"
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "efischer19/hoopstat-haus"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# S3 bucket for raw basketball data
resource "aws_s3_bucket" "raw_data" {
  bucket = "${var.project_name}-raw-data-${var.environment}"
  
  tags = {
    Name        = "Raw Basketball Data"
    Description = "Storage for raw NBA statistics and data from APIs"
    DataType    = "raw"
  }
}

# S3 bucket for processed basketball data
resource "aws_s3_bucket" "processed_data" {
  bucket = "${var.project_name}-processed-data-${var.environment}"
  
  tags = {
    Name        = "Processed Basketball Data"
    Description = "Storage for cleaned and processed basketball statistics"
    DataType    = "processed"
  }
}

# S3 bucket for backup data
resource "aws_s3_bucket" "backup" {
  bucket = "${var.project_name}-backup-${var.environment}"
  
  tags = {
    Name        = "Backup Data"
    Description = "Storage for data backups and archived datasets"
    DataType    = "backup"
  }
}

# S3 bucket configurations (apply to all data buckets)
locals {
  data_buckets = [
    aws_s3_bucket.raw_data,
    aws_s3_bucket.processed_data,
    aws_s3_bucket.backup
  ]
}

# Enable versioning on all data buckets
resource "aws_s3_bucket_versioning" "data_buckets" {
  count  = length(local.data_buckets)
  bucket = local.data_buckets[count.index].id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption on all data buckets
resource "aws_s3_bucket_server_side_encryption_configuration" "data_buckets" {
  count  = length(local.data_buckets)
  bucket = local.data_buckets[count.index].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access on all data buckets
resource "aws_s3_bucket_public_access_block" "data_buckets" {
  count  = length(local.data_buckets)
  bucket = local.data_buckets[count.index].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy for backup bucket
resource "aws_s3_bucket_lifecycle_configuration" "backup" {
  bucket = aws_s3_bucket.backup.id

  rule {
    id     = "backup_lifecycle"
    status = "Enabled"

    # Move to Infrequent Access after 30 days
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Move to Glacier after 90 days
    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Delete after 7 years
    expiration {
      days = 2555
    }
  }
}

# ECR repositories for container images
resource "aws_ecr_repository" "app_repositories" {
  for_each = toset(var.application_names)
  
  name                 = "${var.project_name}/${each.key}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${title(each.key)} Container Repository"
    Description = "ECR repository for ${each.key} application"
    Application = each.key
  }
}

# ECR lifecycle policies
resource "aws_ecr_lifecycle_policy" "app_repositories" {
  for_each   = aws_ecr_repository.app_repositories
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        selection = {
          tagStatus = "tagged"
          tagPrefixList = ["prod"]
          countType = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        selection = {
          tagStatus = "tagged"
          tagPrefixList = ["git-"]
          countType = "imageCountMoreThan"
          countNumber = 20
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 3
        selection = {
          tagStatus = "untagged"
          countType = "sinceImagePushed"
          countUnit = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# IAM role for data pipeline applications
resource "aws_iam_role" "data_pipeline" {
  name = "${var.project_name}-data-pipeline-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = var.github_oidc_provider_arn
        }
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repository}:*"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "Data Pipeline Role"
    Description = "IAM role for data pipeline applications"
  }
}

# IAM policy for data pipeline S3 access
resource "aws_iam_role_policy" "data_pipeline_s3" {
  name = "DataPipelineS3Access"
  role = aws_iam_role.data_pipeline.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.raw_data.arn,
          "${aws_s3_bucket.raw_data.arn}/*",
          aws_s3_bucket.processed_data.arn,
          "${aws_s3_bucket.processed_data.arn}/*",
          aws_s3_bucket.backup.arn,
          "${aws_s3_bucket.backup.arn}/*"
        ]
      }
    ]
  })
}

# IAM role for GitHub Actions deployment
resource "aws_iam_role" "github_actions_deploy" {
  name = "${var.project_name}-github-actions-deploy-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = var.github_oidc_provider_arn
        }
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repository}:*"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "GitHub Actions Deploy Role"
    Description = "IAM role for GitHub Actions deployment workflows"
  }
}

# IAM policy for GitHub Actions ECR access
resource "aws_iam_role_policy" "github_actions_ecr" {
  name = "GitHubActionsECRAccess"
  role = aws_iam_role.github_actions_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchDeleteImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = "*"
      }
    ]
  })
}

# Outputs
output "s3_bucket_raw_data" {
  description = "Name of the S3 bucket for raw data"
  value       = aws_s3_bucket.raw_data.bucket
}

output "s3_bucket_processed_data" {
  description = "Name of the S3 bucket for processed data"
  value       = aws_s3_bucket.processed_data.bucket
}

output "s3_bucket_backup" {
  description = "Name of the S3 bucket for backup data"
  value       = aws_s3_bucket.backup.bucket
}

output "ecr_repositories" {
  description = "ECR repository URLs for applications"
  value = {
    for k, v in aws_ecr_repository.app_repositories : k => v.repository_url
  }
}

output "data_pipeline_role_arn" {
  description = "ARN of the IAM role for data pipeline applications"
  value       = aws_iam_role.data_pipeline.arn
}

output "github_actions_deploy_role_arn" {
  description = "ARN of the IAM role for GitHub Actions deployment"
  value       = aws_iam_role.github_actions_deploy.arn
}

# Environment variables for applications (formatted for easy copy-paste)
output "environment_variables" {
  description = "Environment variables for application configuration"
  value = {
    AWS_REGION                    = var.aws_region
    AWS_S3_BUCKET_RAW_DATA       = aws_s3_bucket.raw_data.bucket
    AWS_S3_BUCKET_PROCESSED_DATA = aws_s3_bucket.processed_data.bucket
    AWS_S3_BUCKET_BACKUP         = aws_s3_bucket.backup.bucket
  }
}