provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Get current AWS account ID for constructing ARNs
data "aws_caller_identity" "current" {}

# Local values for computed ARNs
locals {
  # GitHub OIDC provider ARN (managed outside Terraform)
  github_oidc_provider_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"
}


# Note: GitHub Actions admin IAM role is managed outside of Terraform
# to avoid circular dependency during bootstrap process.
# The admin role (hoopstat-haus-github-actions) is used exclusively for infrastructure operations.
# 
# The operations role (hoopstat-haus-operations) defined below is used for day-to-day CI/CD operations
# and has least-privilege permissions that explicitly deny administrative actions.
#
# This two-role model separates infrastructure administration from runtime operations.

# S3 Bucket for application data and artifacts
resource "aws_s3_bucket" "main" {
  bucket = "${var.project_name}-${var.environment}-data"

  tags = {
    Name = "${var.project_name}-main-bucket"
  }
}

# S3 Bucket versioning
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 Bucket public access block
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ECR Repository for container images
resource "aws_ecr_repository" "main" {
  name                 = "${var.project_name}/${var.environment}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-ecr-repo"
  }
}

# ECR Lifecycle Policy
resource "aws_ecr_lifecycle_policy" "main" {
  repository = aws_ecr_repository.main.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Delete untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ============================================================================
# Lambda IAM Role for CloudWatch Logging (ADR-018)
# ============================================================================

# IAM role for Lambda functions to write to CloudWatch logs
resource "aws_iam_role" "lambda_logging" {
  name = "${var.project_name}-lambda-logging"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Purpose = "Lambda CloudWatch logging permissions"
  }
}

# IAM policy for Lambda CloudWatch logging
resource "aws_iam_policy" "lambda_logging" {
  name        = "${var.project_name}-lambda-logging"
  description = "IAM policy for Lambda function CloudWatch logging"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.applications.arn}:*",
          "${aws_cloudwatch_log_group.data_pipeline.arn}:*"
        ]
      }
    ]
  })
}

# Attach the policy to the role
resource "aws_iam_role_policy_attachment" "lambda_logging" {
  role       = aws_iam_role.lambda_logging.name
  policy_arn = aws_iam_policy.lambda_logging.arn
}

# Attach AWS managed basic execution role
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_logging.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ============================================================================
# CloudWatch Log Groups and Monitoring (ADR-018)
# ============================================================================

# CloudWatch Log Groups for different application types
resource "aws_cloudwatch_log_group" "applications" {
  name              = "/hoopstat-haus/applications"
  retention_in_days = var.log_retention_days.applications

  tags = {
    LogType = "applications"
    Purpose = "General application logging"
  }
}

resource "aws_cloudwatch_log_group" "data_pipeline" {
  name              = "/hoopstat-haus/data-pipeline"
  retention_in_days = var.log_retention_days.data_pipeline

  tags = {
    LogType = "data-pipeline"
    Purpose = "Data processing job logs with performance metrics"
  }
}

resource "aws_cloudwatch_log_group" "infrastructure" {
  name              = "/hoopstat-haus/infrastructure"
  retention_in_days = var.log_retention_days.infrastructure

  tags = {
    LogType = "infrastructure"
    Purpose = "System and infrastructure logs"
  }
}



# ============================================================================
# Medallion Architecture S3 Buckets (Bronze/Silver/Gold)
# ============================================================================

# S3 Bucket for Bronze Layer (Raw/Landing Zone)
resource "aws_s3_bucket" "bronze" {
  bucket = "${var.project_name}-bronze"

  tags = {
    Name      = "${var.project_name}-bronze-bucket"
    DataLayer = "bronze"
    Purpose   = "Raw data landing zone"
    Retention = "2-years"
  }
}

# S3 Bucket versioning for Bronze layer
resource "aws_s3_bucket_versioning" "bronze" {
  bucket = aws_s3_bucket.bronze.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket encryption for Bronze layer
resource "aws_s3_bucket_server_side_encryption_configuration" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 Bucket public access block for Bronze layer
resource "aws_s3_bucket_public_access_block" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Bronze Layer Lifecycle Policy
resource "aws_s3_bucket_lifecycle_configuration" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    id     = "bronze_primary_data"
    status = "Enabled"

    # Apply to all objects by default
    filter {}

    # Transition to Intelligent Tiering after 30 days
    transition {
      days          = 30
      storage_class = "INTELLIGENT_TIERING"
    }

    # Delete primary data after 2 years (730 days)
    expiration {
      days = 730
    }

    # Delete incomplete multipart uploads after 7 days
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  rule {
    id     = "bronze_error_logs"
    status = "Enabled"

    filter {
      prefix = "errors/"
    }

    # Delete error logs after 30 days
    expiration {
      days = 30
    }
  }

  rule {
    id     = "bronze_api_metadata"
    status = "Enabled"

    filter {
      prefix = "api-metadata/"
    }

    # Delete API metadata after 90 days
    expiration {
      days = 90
    }
  }
}

# S3 Bucket for Silver Layer (Cleaned/Conformed)
resource "aws_s3_bucket" "silver" {
  bucket = "${var.project_name}-silver"

  tags = {
    Name      = "${var.project_name}-silver-bucket"
    DataLayer = "silver"
    Purpose   = "Cleaned and conformed data with schema enforcement"
    Retention = "3-years"
  }
}

# S3 Bucket versioning for Silver layer
resource "aws_s3_bucket_versioning" "silver" {
  bucket = aws_s3_bucket.silver.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket encryption for Silver layer
resource "aws_s3_bucket_server_side_encryption_configuration" "silver" {
  bucket = aws_s3_bucket.silver.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 Bucket public access block for Silver layer
resource "aws_s3_bucket_public_access_block" "silver" {
  bucket = aws_s3_bucket.silver.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Silver Layer Lifecycle Policy
resource "aws_s3_bucket_lifecycle_configuration" "silver" {
  bucket = aws_s3_bucket.silver.id

  rule {
    id     = "silver_primary_data"
    status = "Enabled"

    # Apply to all objects by default
    filter {}

    # Transition to Standard-IA after 90 days
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    # Delete primary data after 3 years (1095 days)
    expiration {
      days = 1095
    }

    # Delete incomplete multipart uploads after 7 days
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  rule {
    id     = "silver_data_quality"
    status = "Enabled"

    filter {
      prefix = "data_quality/"
    }

    # Delete data quality logs after 90 days
    expiration {
      days = 90
    }
  }

  rule {
    id     = "silver_quarantine"
    status = "Enabled"

    filter {
      prefix = "quarantine/"
    }

    # Delete quarantined data after 30 days
    expiration {
      days = 30
    }
  }
}

# ============================================================================
# S3 Tables for Gold Layer Analytics (ADR-026)
# ============================================================================

# S3 Tables Bucket for Gold Layer Apache Iceberg analytics
resource "aws_s3tables_table_bucket" "gold_tables" {
  name = "${var.project_name}-gold-tables"
}

# S3 Tables Namespace for basketball analytics
resource "aws_s3tables_namespace" "basketball_analytics" {
  namespace        = "basketball_analytics"
  table_bucket_arn = aws_s3tables_table_bucket.gold_tables.arn
}

# Player Analytics Table with Apache Iceberg schema
resource "aws_s3tables_table" "player_analytics" {
  name             = "player_analytics"
  namespace        = aws_s3tables_namespace.basketball_analytics.namespace
  table_bucket_arn = aws_s3tables_table_bucket.gold_tables.arn
  format           = "ICEBERG"

  metadata {
    iceberg {
      schema {
        field {
          name     = "player_id"
          type     = "int"
          required = true
        }
        field {
          name     = "game_date"
          type     = "date"
          required = true
        }
        field {
          name     = "season"
          type     = "string"
          required = true
        }
        field {
          name     = "team_id"
          type     = "int"
          required = true
        }
        field {
          name     = "points"
          type     = "int"
          required = false
        }
        field {
          name     = "rebounds"
          type     = "int"
          required = false
        }
        field {
          name     = "assists"
          type     = "int"
          required = false
        }
        field {
          name     = "true_shooting_pct"
          type     = "double"
          required = false
        }
        field {
          name     = "player_efficiency_rating"
          type     = "double"
          required = false
        }
        field {
          name     = "usage_rate"
          type     = "double"
          required = false
        }
        field {
          name     = "effective_field_goal_pct"
          type     = "double"
          required = false
        }
        field {
          name     = "defensive_rating"
          type     = "double"
          required = false
        }
        field {
          name     = "offensive_rating"
          type     = "double"
          required = false
        }
      }
    }
  }
}

# Team Analytics Table with Apache Iceberg schema
resource "aws_s3tables_table" "team_analytics" {
  name             = "team_analytics"
  namespace        = aws_s3tables_namespace.basketball_analytics.namespace
  table_bucket_arn = aws_s3tables_table_bucket.gold_tables.arn
  format           = "ICEBERG"

  metadata {
    iceberg {
      schema {
        field {
          name     = "team_id"
          type     = "int"
          required = true
        }
        field {
          name     = "game_date"
          type     = "date"
          required = true
        }
        field {
          name     = "season"
          type     = "string"
          required = true
        }
        field {
          name     = "opponent_team_id"
          type     = "int"
          required = true
        }
        field {
          name     = "offensive_rating"
          type     = "double"
          required = false
        }
        field {
          name     = "defensive_rating"
          type     = "double"
          required = false
        }
        field {
          name     = "net_rating"
          type     = "double"
          required = false
        }
        field {
          name     = "pace"
          type     = "double"
          required = false
        }
        field {
          name     = "effective_field_goal_pct"
          type     = "double"
          required = false
        }
        field {
          name     = "true_shooting_pct"
          type     = "double"
          required = false
        }
        field {
          name     = "turnover_rate"
          type     = "double"
          required = false
        }
        field {
          name     = "rebound_rate"
          type     = "double"
          required = false
        }
      }
    }
  }
}



# S3 bucket for access logs
resource "aws_s3_bucket" "access_logs" {
  bucket = "${var.project_name}-access-logs"

  tags = {
    Name    = "${var.project_name}-access-logs-bucket"
    Purpose = "S3 access logs for medallion architecture buckets"
  }
}

# S3 Bucket encryption for access logs
resource "aws_s3_bucket_server_side_encryption_configuration" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 Bucket public access block for access logs
resource "aws_s3_bucket_public_access_block" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Access logs lifecycle policy
resource "aws_s3_bucket_lifecycle_configuration" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id

  rule {
    id     = "access_logs_lifecycle"
    status = "Enabled"

    # Apply to all objects by default
    filter {}

    # Delete access logs after 90 days
    expiration {
      days = 90
    }

    # Delete incomplete multipart uploads after 7 days
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# S3 Bucket Logging for Bronze Layer
resource "aws_s3_bucket_logging" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  target_bucket = aws_s3_bucket.access_logs.id
  target_prefix = "bronze/"
}

# S3 Bucket Logging for Silver Layer
resource "aws_s3_bucket_logging" "silver" {
  bucket = aws_s3_bucket.silver.id

  target_bucket = aws_s3_bucket.access_logs.id
  target_prefix = "silver/"
}



# ============================================================================
# GitHub Actions Operations Role (ADR-011)
# ============================================================================

# IAM role for GitHub Actions day-to-day operations (separate from admin role)
resource "aws_iam_role" "github_actions_operations" {
  name = "${var.project_name}-operations"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = local.github_oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repo}:*"
          }
        }
      }
    ]
  })

  tags = {
    Name    = "${var.project_name}-operations-role"
    Purpose = "GitHub Actions day-to-day operations with least-privilege access"
    Type    = "operations"
  }
}

# ECR permissions for container operations
# Includes DescribeRepositories permission which is required alongside DescribeImages
# for deployment workflows to verify image existence before updating Lambda functions
resource "aws_iam_role_policy" "github_actions_operations_ecr" {
  name = "${var.project_name}-operations-ecr"
  role = aws_iam_role.github_actions_operations.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:DescribeImages",
          "ecr:DescribeRepositories",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = aws_ecr_repository.main.arn
      }
    ]
  })
}

# S3 object operations for medallion architecture buckets
resource "aws_iam_role_policy" "github_actions_operations_s3" {
  name = "${var.project_name}-operations-s3"
  role = aws_iam_role.github_actions_operations.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.main.arn,
          aws_s3_bucket.bronze.arn,
          aws_s3_bucket.silver.arn,
          aws_s3_bucket.access_logs.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${aws_s3_bucket.main.arn}/*",
          "${aws_s3_bucket.bronze.arn}/*",
          "${aws_s3_bucket.silver.arn}/*",
          "${aws_s3_bucket.access_logs.arn}/*"
        ]
      }
    ]
  })
}

# CloudWatch Logs permissions for application logging
resource "aws_iam_role_policy" "github_actions_operations_logs" {
  name = "${var.project_name}-operations-logs"
  role = aws_iam_role.github_actions_operations.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.applications.arn}:*",
          "${aws_cloudwatch_log_group.data_pipeline.arn}:*",
          "${aws_cloudwatch_log_group.infrastructure.arn}:*"
        ]
      }
    ]
  })
}

# Lambda operations permissions for GitHub Actions
resource "aws_iam_role_policy" "github_actions_operations_lambda" {
  name = "${var.project_name}-operations-lambda"
  role = aws_iam_role.github_actions_operations.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:UpdateFunctionCode",
          "lambda:GetFunction",
          "lambda:InvokeFunction",
          "lambda:GetFunctionConfiguration"
        ]
        Resource = [
          "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-silver-processing",
          "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-gold-analytics"
        ]
      }
    ]
  })
}

# Explicit denials for administrative actions
resource "aws_iam_role_policy" "github_actions_operations_denials" {
  name = "${var.project_name}-operations-denials"
  role = aws_iam_role.github_actions_operations.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Deny"
        Action = [
          # S3 bucket management
          "s3:CreateBucket",
          "s3:DeleteBucket",
          "s3:PutBucketPolicy",
          "s3:DeleteBucketPolicy",
          "s3:PutBucketVersioning",
          "s3:PutBucketEncryption",
          "s3:PutBucketLifecycle*",
          "s3:PutBucketLogging",
          "s3:PutBucketPublicAccessBlock",
          # ECR repository management
          "ecr:CreateRepository",
          "ecr:DeleteRepository",
          "ecr:PutRepositoryPolicy",
          "ecr:DeleteRepositoryPolicy",
          "ecr:PutLifecyclePolicy",
          "ecr:DeleteLifecyclePolicy",
          # IAM operations
          "iam:Create*",
          "iam:Delete*",
          "iam:Put*",
          "iam:Attach*",
          "iam:Detach*",
          "iam:Update*",
          # CloudWatch management operations
          "logs:CreateLogGroup",
          "logs:DeleteLogGroup",
          "logs:PutRetentionPolicy",
          "logs:DeleteRetentionPolicy",
          "logs:PutMetricFilter",
          "logs:DeleteMetricFilter",
          "cloudwatch:PutMetricAlarm",
          "cloudwatch:DeleteAlarms",
          "cloudwatch:PutMetricFilter",
          # Lambda function management (only updates allowed)
          "lambda:CreateFunction",
          "lambda:DeleteFunction",
          "lambda:UpdateFunctionConfiguration"
        ]
        Resource = "*"
      }
    ]
  })
}

# ============================================================================
# IAM Roles for Medallion Architecture Data Access
# ============================================================================

# IAM Role for Silver Layer Data Access
resource "aws_iam_role" "silver_data_access" {
  name = "${var.project_name}-silver-data-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = local.github_oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repo}:*"
          }
        }
      }
    ]
  })

  tags = {
    Name      = "${var.project_name}-silver-data-access-role"
    DataLayer = "silver"
    Purpose   = "Data transformation and quality validation"
  }
}

# IAM Policy for Silver Layer
resource "aws_iam_role_policy" "silver_data_access" {
  name = "${var.project_name}-silver-data-access-policy"
  role = aws_iam_role.silver_data_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.bronze.arn,
          "${aws_s3_bucket.bronze.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.silver.arn,
          "${aws_s3_bucket.silver.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.data_pipeline.arn}:*"
        ]
      }
    ]
  })
}

# IAM Role for Gold Layer Data Access
resource "aws_iam_role" "gold_data_access" {
  name = "${var.project_name}-gold-data-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = local.github_oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repo}:*"
          }
        }
      }
    ]
  })

  tags = {
    Name      = "${var.project_name}-gold-data-access-role"
    DataLayer = "gold"
    Purpose   = "Business analytics for S3 Tables integration"
  }
}

# IAM Policy for Gold Layer (S3 Tables and legacy S3)
resource "aws_iam_role_policy" "gold_data_access" {
  name = "${var.project_name}-gold-data-access-policy"
  role = aws_iam_role.gold_data_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.silver.arn,
          "${aws_s3_bucket.silver.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          # S3 Tables permissions for Gold analytics
          "s3tables:GetTable",
          "s3tables:GetTableData",
          "s3tables:GetTableMetadata",
          "s3tables:PutTableData",
          "s3tables:UpdateTableData",
          "s3tables:DeleteTableData",
          "s3tables:CreateTable",
          "s3tables:UpdateTable",
          "s3tables:ListTables",
          "s3tables:GetTableBucket",
          "s3tables:ListTableBuckets"
        ]
        Resource = [
          "arn:aws:s3tables:${var.aws_region}:${data.aws_caller_identity.current.account_id}:bucket/${aws_s3tables_table_bucket.gold_tables.name}",
          "arn:aws:s3tables:${var.aws_region}:${data.aws_caller_identity.current.account_id}:bucket/${aws_s3tables_table_bucket.gold_tables.name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.data_pipeline.arn}:*",
          "${aws_cloudwatch_log_group.s3_tables.arn}:*"
        ]
      }
    ]
  })
}

# ============================================================================
# IAM Role for Bronze Layer Data Access (Local Execution)
# ============================================================================

# IAM Role for Bronze Layer Data Access
resource "aws_iam_role" "bronze_data_access" {
  name = "${var.project_name}-bronze-data-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = local.github_oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repo}:*"
          }
        }
      }
    ]
  })

  tags = {
    Name      = "${var.project_name}-bronze-data-access-role"
    DataLayer = "bronze"
    Purpose   = "Local bronze ingestion from external data sources"
  }
}

# IAM Policy for Bronze Layer
resource "aws_iam_role_policy" "bronze_data_access" {
  name = "${var.project_name}-bronze-data-access-policy"
  role = aws_iam_role.bronze_data_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.bronze.arn,
          "${aws_s3_bucket.bronze.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.data_pipeline.arn}:*"
        ]
      }
    ]
  })
}

# ============================================================================
# Lambda Functions and IAM Roles for Containerized Applications
# ============================================================================

# IAM Role for Lambda Function Execution with S3 and ECR access
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-lambda-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Purpose = "Lambda function execution with S3 and CloudWatch access"
  }
}

# IAM policy for Lambda execution (S3, S3 Tables, CloudWatch, ECR access)
resource "aws_iam_policy" "lambda_execution" {
  name        = "${var.project_name}-lambda-execution"
  description = "IAM policy for Lambda function execution with S3, S3 Tables, and CloudWatch access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.applications.arn}:*",
          "${aws_cloudwatch_log_group.data_pipeline.arn}:*",
          "${aws_cloudwatch_log_group.s3_tables.arn}:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.main.arn,
          "${aws_s3_bucket.main.arn}/*",
          aws_s3_bucket.bronze.arn,
          "${aws_s3_bucket.bronze.arn}/*",
          aws_s3_bucket.silver.arn,
          "${aws_s3_bucket.silver.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          # S3 Tables permissions for Gold layer processing
          "s3tables:GetTable",
          "s3tables:GetTableData",
          "s3tables:GetTableMetadata",
          "s3tables:PutTableData",
          "s3tables:UpdateTableData",
          "s3tables:DeleteTableData",
          "s3tables:ListTables",
          "s3tables:GetTableBucket"
        ]
        Resource = [
          "arn:aws:s3tables:${var.aws_region}:${data.aws_caller_identity.current.account_id}:bucket/${aws_s3tables_table_bucket.gold_tables.name}",
          "arn:aws:s3tables:${var.aws_region}:${data.aws_caller_identity.current.account_id}:bucket/${aws_s3tables_table_bucket.gold_tables.name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = [
          aws_ecr_repository.main.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach the custom policy to the Lambda execution role
resource "aws_iam_role_policy_attachment" "lambda_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.lambda_execution.arn
}

# Attach AWS managed basic execution role for Lambda
resource "aws_iam_role_policy_attachment" "lambda_basic_execution_role" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda function configurations for different applications
# Note: These functions will be created with placeholder image URIs
# The actual deployment will update the function code with built images

# Silver Processing Lambda Function
resource "aws_lambda_function" "silver_processing" {
  function_name = "${var.project_name}-silver-processing"
  role          = aws_iam_role.lambda_execution.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.main.repository_url}:silver-processing-latest"

  timeout     = var.lambda_config.silver_processing.timeout
  memory_size = var.lambda_config.silver_processing.memory_size

  environment {
    variables = {
      LOG_LEVEL     = "INFO"
      APP_NAME      = "silver-processing"
      BRONZE_BUCKET = aws_s3_bucket.bronze.bucket
      SILVER_BUCKET = aws_s3_bucket.silver.bucket
    }
  }

  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.data_pipeline.name
  }

  tags = {
    Application = "silver-processing"
    Type        = "data-pipeline"
  }

  # Lifecycle rule to ignore image_uri changes (managed by deployment workflow)
  lifecycle {
    ignore_changes = [image_uri]
  }
}

# Gold Processing Lambda Function
resource "aws_lambda_function" "gold_processing" {
  function_name = "${var.project_name}-gold-analytics"
  role          = aws_iam_role.lambda_execution.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.main.repository_url}:gold-analytics-latest"

  timeout     = var.lambda_config.gold_processing.timeout
  memory_size = var.lambda_config.gold_processing.memory_size

  environment {
    variables = {
      LOG_LEVEL      = "INFO"
      APP_NAME       = "gold-analytics"
      SILVER_BUCKET  = aws_s3_bucket.silver.bucket
      GOLD_TABLE_ARN = aws_s3tables_table_bucket.gold_tables.arn
    }
  }

  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.data_pipeline.name
  }

  tags = {
    Application = "gold-analytics"
    Type        = "data-pipeline"
  }

  # Lifecycle rule to ignore image_uri changes (managed by deployment workflow)
  lifecycle {
    ignore_changes = [image_uri]
  }
}




# ============================================================================
# S3 Tables CloudWatch Log Group (ADR-026)
# ============================================================================

# CloudWatch Log Group for S3 Tables analytics operations monitoring
resource "aws_cloudwatch_log_group" "s3_tables" {
  name              = "/hoopstat-haus/s3-tables"
  retention_in_days = var.log_retention_days.data_pipeline

  tags = {
    LogType = "s3-tables"
    Purpose = "S3 Tables analytics operations monitoring"
  }
}



# ============================================================================
# S3 Event Notifications for Silver Processing
# ============================================================================

# Lambda permission for S3 to invoke silver-processing function
resource "aws_lambda_permission" "s3_invoke_silver_processing" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.silver_processing.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.bronze.arn
}

# S3 bucket notification for bronze bucket to trigger silver processing
resource "aws_s3_bucket_notification" "bronze_bucket_notification" {
  bucket = aws_s3_bucket.bronze.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.silver_processing.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw/box_scores/date="
    filter_suffix       = "/data.json"
  }

  depends_on = [aws_lambda_permission.s3_invoke_silver_processing]
}

# ============================================================================
# S3 Event Notifications for Gold Processing
# ============================================================================

# Lambda permission for S3 to invoke gold-processing function
resource "aws_lambda_permission" "s3_invoke_gold_processing" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.gold_processing.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.silver.arn
}

# S3 bucket notification for silver bucket to trigger gold processing
resource "aws_s3_bucket_notification" "silver_bucket_notification" {
  bucket = aws_s3_bucket.silver.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.gold_processing.arn
    events              = ["s3:ObjectCreated:*"]
    # Support both current silver output format (date=) and future format (season=)
    filter_prefix = "silver/"
    filter_suffix = ".json"
  }

  depends_on = [aws_lambda_permission.s3_invoke_gold_processing]
}

# ============================================================================
# Physical Devices IAM Resources
# ============================================================================

# IAM User for Production Raspberry Pi
resource "aws_iam_user" "prod_pi" {
  name = "hoopstat-prod-pi"
  tags = {
    Description = "User for Raspberry Pi in production closet"
  }
}

# Policy for Production Pi
# Grants permission to pull from ECR and write to the Bronze bucket
resource "aws_iam_policy" "prod_pi_policy" {
  name        = "hoopstat-prod-pi-policy"
  description = "Policy for Raspberry Pi to pull images and write to bronze bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ECRAuth"
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Sid    = "ECRPull"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = aws_ecr_repository.main.arn
      },
      {
        Sid    = "BronzeBucketAccess"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.bronze.arn,
          "${aws_s3_bucket.bronze.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "prod_pi_attach" {
  user       = aws_iam_user.prod_pi.name
  policy_arn = aws_iam_policy.prod_pi_policy.arn
}