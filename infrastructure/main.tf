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

# Data source for GitHub OIDC provider (managed outside Terraform)
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

# Note: GitHub Actions IAM role is managed outside of Terraform
# to avoid circular dependency during bootstrap process.
# The role should be created manually with the following permissions:
#
# Required permissions for hoopstat-haus-github-actions role:
# - S3: GetObject, PutObject, DeleteObject, ListBucket on the main bucket
# - S3: GetObject, PutObject, DeleteObject, ListBucket on medallion architecture buckets
#   (hoopstat-haus-bronze, hoopstat-haus-silver, hoopstat-haus-gold, hoopstat-haus-access-logs)
# - ECR: BatchCheckLayerAvailability, GetDownloadUrlForLayer, BatchGetImage, 
#        GetAuthorizationToken, PutImage, InitiateLayerUpload, UploadLayerPart, CompleteLayerUpload
# - CloudWatch Logs: CreateLogGroup, CreateLogStream, PutLogEvents, DescribeLogGroups, DescribeLogStreams

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
    Purpose   = "Business-ready aggregated datasets for MCP server"
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

    # No storage class transitions - frequently accessed by MCP server
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
          Federated = data.aws_iam_openid_connect_provider.github.arn
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
          Federated = data.aws_iam_openid_connect_provider.github.arn
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
          Federated = data.aws_iam_openid_connect_provider.github.arn
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
    Purpose   = "Business analytics and MCP server integration"
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
# Player Daily Aggregator Lambda Function
# ============================================================================

# IAM Role for Player Daily Aggregator Lambda
resource "aws_iam_role" "player_daily_aggregator" {
  name = "${var.project_name}-player-daily-aggregator"

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
    Purpose = "Player daily statistics aggregation ETL job"
  }
}

# IAM Policy for Player Daily Aggregator Lambda
resource "aws_iam_policy" "player_daily_aggregator" {
  name        = "${var.project_name}-player-daily-aggregator"
  description = "IAM policy for Player Daily Aggregator Lambda function"

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
          "${aws_cloudwatch_log_group.data_pipeline.arn}:*"
        ]
      },
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
      }
    ]
  })
}

# Attach the policy to the role
resource "aws_iam_role_policy_attachment" "player_daily_aggregator" {
  role       = aws_iam_role.player_daily_aggregator.name
  policy_arn = aws_iam_policy.player_daily_aggregator.arn
}

# Attach AWS managed basic execution role
resource "aws_iam_role_policy_attachment" "player_daily_aggregator_basic" {
  role       = aws_iam_role.player_daily_aggregator.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda function for Player Daily Aggregator
resource "aws_lambda_function" "player_daily_aggregator" {
  function_name = "${var.project_name}-player-daily-aggregator"
  role          = aws_iam_role.player_daily_aggregator.arn

  # Deployment package will be managed separately via GitHub Actions
  filename         = "/tmp/player-daily-aggregator-placeholder.zip"
  source_code_hash = "placeholder"

  handler = "player_daily_aggregator.lambda_handler.lambda_handler"
  runtime = "python3.12"
  timeout = 900 # 15 minutes
  
  memory_size = 1024 # MB

  environment {
    variables = {
      LOG_LEVEL = "INFO"
      AWS_REGION = var.aws_region
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.player_daily_aggregator,
    aws_iam_role_policy_attachment.player_daily_aggregator_basic,
    aws_cloudwatch_log_group.data_pipeline,
  ]

  tags = {
    Purpose = "Silver to Gold ETL - Player daily statistics aggregation"
  }

  # Create placeholder zip file
  provisioner "local-exec" {
    command = "echo 'placeholder' > /tmp/placeholder.py && zip -j /tmp/player-daily-aggregator-placeholder.zip /tmp/placeholder.py"
  }
}

# CloudWatch Log Group for Lambda function
resource "aws_cloudwatch_log_group" "player_daily_aggregator" {
  name              = "/aws/lambda/${aws_lambda_function.player_daily_aggregator.function_name}"
  retention_in_days = var.log_retention_days.data_pipeline

  tags = {
    Purpose = "Player daily aggregator Lambda logs"
  }
}

# S3 Bucket Notification for Silver Layer
resource "aws_s3_bucket_notification" "silver_layer_notifications" {
  bucket = aws_s3_bucket.silver.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.player_daily_aggregator.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "player_games/"
    filter_suffix       = ".parquet"
  }

  depends_on = [aws_lambda_permission.allow_silver_bucket]
}

# Lambda permission for S3 to invoke the function
resource "aws_lambda_permission" "allow_silver_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.player_daily_aggregator.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.silver.arn
}
