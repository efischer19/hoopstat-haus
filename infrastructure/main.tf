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

# Metric filters to extract performance metrics from JSON logs per ADR-015
resource "aws_cloudwatch_log_metric_filter" "execution_duration" {
  name           = "execution-duration"
  log_group_name = aws_cloudwatch_log_group.data_pipeline.name
  pattern        = "[timestamp, level, message, job_name, duration_in_seconds = *, records_processed, ...]"

  metric_transformation {
    name      = "ExecutionDuration"
    namespace = "HoopstatHaus/DataPipeline"
    value     = "$duration_in_seconds"
    unit      = "Seconds"
  }
}

resource "aws_cloudwatch_log_metric_filter" "records_processed" {
  name           = "records-processed"
  log_group_name = aws_cloudwatch_log_group.data_pipeline.name
  pattern        = "[timestamp, level, message, job_name, duration_in_seconds, records_processed = *, ...]"

  metric_transformation {
    name      = "RecordsProcessed"
    namespace = "HoopstatHaus/DataPipeline"
    value     = "$records_processed"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_log_metric_filter" "error_count" {
  name           = "error-count"
  log_group_name = aws_cloudwatch_log_group.applications.name
  pattern        = "[timestamp, level=\"ERROR\", ...]"

  metric_transformation {
    name      = "ErrorCount"
    namespace = "HoopstatHaus/Applications"
    value     = "1"
    unit      = "Count"
  }
}

# ============================================================================
# CloudWatch Alarms (ADR-018) - Without SNS Integration
# ============================================================================

# CloudWatch Alarms for critical monitoring (notifications will be added later)
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ErrorCount"
  namespace           = "HoopstatHaus/Applications"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors application error rate"

  tags = {
    Severity = "critical"
    Type     = "error-rate"
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_timeout" {
  alarm_name          = "lambda-timeouts"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Maximum"
  threshold           = "900000" # 15 minutes in milliseconds
  alarm_description   = "This metric monitors Lambda function timeouts"

  tags = {
    Severity = "critical"
    Type     = "timeout"
  }
}

resource "aws_cloudwatch_metric_alarm" "execution_time_anomaly" {
  alarm_name          = "execution-time-anomaly"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ExecutionDuration"
  namespace           = "HoopstatHaus/DataPipeline"
  period              = "600"
  statistic           = "Average"
  threshold           = "300" # 5 minutes
  alarm_description   = "This metric monitors unusually long data pipeline execution times"

  tags = {
    Severity = "warning"
    Type     = "performance"
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

# S3 Bucket for Gold Layer (Business/Analytics-Ready)
resource "aws_s3_bucket" "gold" {
  bucket = "${var.project_name}-gold"

  tags = {
    Name      = "${var.project_name}-gold-bucket"
    DataLayer = "gold"
    Purpose   = "Business-ready aggregated datasets for analytics"
    Retention = "indefinite"
  }
}

# S3 Bucket versioning for Gold layer
resource "aws_s3_bucket_versioning" "gold" {
  bucket = aws_s3_bucket.gold.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket encryption for Gold layer
resource "aws_s3_bucket_server_side_encryption_configuration" "gold" {
  bucket = aws_s3_bucket.gold.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 Bucket public access block for Gold layer
resource "aws_s3_bucket_public_access_block" "gold" {
  bucket = aws_s3_bucket.gold.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Gold Layer Lifecycle Policy
resource "aws_s3_bucket_lifecycle_configuration" "gold" {
  bucket = aws_s3_bucket.gold.id

  rule {
    id     = "gold_lifecycle"
    status = "Enabled"

    # Apply to all objects by default
    filter {}

    # No storage class transitions - frequently accessed for analytics
    # Indefinite retention for business data

    # Delete incomplete multipart uploads after 7 days
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
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

# S3 Bucket Logging for Gold Layer
resource "aws_s3_bucket_logging" "gold" {
  bucket = aws_s3_bucket.gold.id

  target_bucket = aws_s3_bucket.access_logs.id
  target_prefix = "gold/"
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
          aws_s3_bucket.gold.arn,
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
          "${aws_s3_bucket.gold.arn}/*",
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
          "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-bronze-ingestion",
          "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-silver-processing"
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
    Purpose   = "Data ingestion and raw data access"
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
          "s3:GetObject",
          "s3:PutObject",
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

# IAM Policy for Gold Layer
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
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.gold.arn,
          "${aws_s3_bucket.gold.arn}/*"
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

# IAM policy for Lambda execution (S3, CloudWatch, ECR access)
resource "aws_iam_policy" "lambda_execution" {
  name        = "${var.project_name}-lambda-execution"
  description = "IAM policy for Lambda function execution with S3 and CloudWatch access"

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
          "${aws_s3_bucket.silver.arn}/*",
          aws_s3_bucket.gold.arn,
          "${aws_s3_bucket.gold.arn}/*"
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

# Bronze Ingestion Lambda Function
resource "aws_lambda_function" "bronze_ingestion" {
  function_name = "${var.project_name}-bronze-ingestion"
  role          = aws_iam_role.lambda_execution.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.main.repository_url}:bronze-ingestion-latest"

  timeout     = var.lambda_config.bronze_ingestion.timeout
  memory_size = var.lambda_config.bronze_ingestion.memory_size

  environment {
    variables = {
      LOG_LEVEL     = "INFO"
      APP_NAME      = "bronze-ingestion"
      BRONZE_BUCKET = aws_s3_bucket.bronze.bucket
    }
  }

  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.data_pipeline.name
  }

  tags = {
    Application = "bronze-ingestion"
    Type        = "data-pipeline"
  }

  # Lifecycle rule to ignore image_uri changes (managed by deployment workflow)
  lifecycle {
    ignore_changes = [image_uri]
  }
}

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

  # Simple error handling via CloudWatch logs and Lambda retries
}


# Lambda-specific CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = {
    bronze_ingestion  = aws_lambda_function.bronze_ingestion.function_name
    silver_processing = aws_lambda_function.silver_processing.function_name
  }

  alarm_name          = "lambda-errors-${each.key}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "This metric monitors Lambda function errors for ${each.key}"

  dimensions = {
    FunctionName = each.value
  }

  tags = {
    Severity    = "critical"
    Type        = "lambda-errors"
    Application = each.key
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  for_each = {
    bronze_ingestion = {
      function_name = aws_lambda_function.bronze_ingestion.function_name
      threshold     = 250000 # 4.17 minutes (83% of 5m timeout)
    }
    silver_processing = {
      function_name = aws_lambda_function.silver_processing.function_name
      threshold     = 250000 # 4.17 minutes (83% of 5m timeout)
    }
  }

  alarm_name          = "lambda-duration-${each.key}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = each.value.threshold
  alarm_description   = "This metric monitors Lambda function duration for ${each.key}"

  dimensions = {
    FunctionName = each.value.function_name
  }

  tags = {
    Severity    = "warning"
    Type        = "lambda-duration"
    Application = each.key
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  for_each = {
    bronze_ingestion  = aws_lambda_function.bronze_ingestion.function_name
    silver_processing = aws_lambda_function.silver_processing.function_name
  }

  alarm_name          = "lambda-throttles-${each.key}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors Lambda function throttles for ${each.key}"

  dimensions = {
    FunctionName = each.value
  }

  tags = {
    Severity    = "critical"
    Type        = "lambda-throttles"
    Application = each.key
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