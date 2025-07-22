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

# GitHub OIDC Provider - use existing provider
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

# IAM Role for GitHub Actions
resource "aws_iam_role" "github_actions" {
  name = "${var.project_name}-github-actions"

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
    Name = "${var.project_name}-github-actions-role"
  }
}

# IAM Policy for GitHub Actions - Updated for medallion architecture
resource "aws_iam_role_policy" "github_actions" {
  name = "${var.project_name}-github-actions-policy"
  role = aws_iam_role.github_actions.id

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
          # Legacy bucket (backward compatibility)
          aws_s3_bucket.main.arn,
          "${aws_s3_bucket.main.arn}/*",
          # Medallion architecture buckets
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
          "ecr:BatchGetImage",
          "ecr:GetAuthorizationToken",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })
}

# ============================================================================
# Data Layer Specific IAM Roles for Least-Privilege Access
# ============================================================================

# Bronze Layer Access Role (for data ingestion services)
resource "aws_iam_role" "bronze_layer_access" {
  name = "${var.project_name}-bronze-layer-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = ["lambda.amazonaws.com", "ecs-tasks.amazonaws.com"]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name      = "${var.project_name}-bronze-access-role"
    DataLayer = "bronze"
    Purpose   = "Data ingestion and raw data writing"
  }
}

# Bronze Layer IAM Policy (write-only for raw data ingestion)
resource "aws_iam_role_policy" "bronze_layer_access" {
  name = "${var.project_name}-bronze-layer-policy"
  role = aws_iam_role.bronze_layer_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:ListBucket"
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

# Silver Layer Access Role (for data transformation services)
resource "aws_iam_role" "silver_layer_access" {
  name = "${var.project_name}-silver-layer-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = ["lambda.amazonaws.com", "ecs-tasks.amazonaws.com"]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name      = "${var.project_name}-silver-access-role"
    DataLayer = "silver"
    Purpose   = "Data transformation and cleaning"
  }
}

# Silver Layer IAM Policy (read bronze, write silver)
resource "aws_iam_role_policy" "silver_layer_access" {
  name = "${var.project_name}-silver-layer-policy"
  role = aws_iam_role.silver_layer_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.bronze.arn,
          "${aws_s3_bucket.bronze.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:ListBucket"
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

# Gold Layer Access Role (for aggregation and MCP server integration)
resource "aws_iam_role" "gold_layer_access" {
  name = "${var.project_name}-gold-layer-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = ["lambda.amazonaws.com", "ecs-tasks.amazonaws.com"]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name      = "${var.project_name}-gold-access-role"
    DataLayer = "gold"
    Purpose   = "Business aggregation and MCP server integration"
  }
}

# Gold Layer IAM Policy (read silver, write gold)
resource "aws_iam_role_policy" "gold_layer_access" {
  name = "${var.project_name}-gold-layer-policy"
  role = aws_iam_role.gold_layer_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.silver.arn,
          "${aws_s3_bucket.silver.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:GetObject",
          "s3:ListBucket"
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
          "${aws_cloudwatch_log_group.applications.arn}:*",
          "${aws_cloudwatch_log_group.data_pipeline.arn}:*"
        ]
      }
    ]
  })
}

# MCP Server Read-Only Access Role (for serving data from Gold layer)
resource "aws_iam_role" "mcp_server_access" {
  name = "${var.project_name}-mcp-server-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = ["lambda.amazonaws.com", "ecs-tasks.amazonaws.com"]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name      = "${var.project_name}-mcp-server-role"
    DataLayer = "gold"
    Purpose   = "MCP server read-only access to processed data"
  }
}

# MCP Server IAM Policy (read-only access to Gold layer)
resource "aws_iam_role_policy" "mcp_server_access" {
  name = "${var.project_name}-mcp-server-policy"
  role = aws_iam_role.mcp_server_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
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
          "${aws_cloudwatch_log_group.applications.arn}:*"
        ]
      }
    ]
  })
}

# ============================================================================
# S3 Medallion Architecture Buckets (Bronze/Silver/Gold Data Layers)
# ============================================================================

# Bronze Layer: Raw data landing zone
resource "aws_s3_bucket" "bronze" {
  bucket = "${var.project_name}-bronze"

  tags = {
    Name      = "${var.project_name}-bronze-bucket"
    DataLayer = "bronze"
    Purpose   = "Raw data landing zone"
  }
}

# Silver Layer: Cleaned and conformed data
resource "aws_s3_bucket" "silver" {
  bucket = "${var.project_name}-silver"

  tags = {
    Name      = "${var.project_name}-silver-bucket"
    DataLayer = "silver"
    Purpose   = "Cleaned and conformed data"
  }
}

# Gold Layer: Business-ready aggregated data
resource "aws_s3_bucket" "gold" {
  bucket = "${var.project_name}-gold"

  tags = {
    Name      = "${var.project_name}-gold-bucket"
    DataLayer = "gold"
    Purpose   = "Business-ready aggregated data"
  }
}

# S3 Bucket versioning for all data layers
resource "aws_s3_bucket_versioning" "bronze" {
  bucket = aws_s3_bucket.bronze.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "silver" {
  bucket = aws_s3_bucket.silver.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "gold" {
  bucket = aws_s3_bucket.gold.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket encryption for all data layers
resource "aws_s3_bucket_server_side_encryption_configuration" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "silver" {
  bucket = aws_s3_bucket.silver.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "gold" {
  bucket = aws_s3_bucket.gold.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 Bucket public access block for all data layers
resource "aws_s3_bucket_public_access_block" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "silver" {
  bucket = aws_s3_bucket.silver.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "gold" {
  bucket = aws_s3_bucket.gold.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================================
# S3 Bucket Lifecycle Policies for Cost Optimization
# ============================================================================

# Bronze Layer: Transition raw data to cheaper storage classes
resource "aws_s3_bucket_lifecycle_configuration" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    id     = "bronze_lifecycle"
    status = "Enabled"

    # Transition to Intelligent Tiering after 30 days
    transition {
      days          = 30
      storage_class = "INTELLIGENT_TIERING"
    }

    # Transition to Standard IA after 90 days
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    # Transition to Glacier after 1 year for archival
    transition {
      days          = 365
      storage_class = "GLACIER"
    }

    # Clean up incomplete multipart uploads after 7 days
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }

    # Clean up delete markers after 30 days
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# Silver Layer: Keep accessible longer but transition to IA
resource "aws_s3_bucket_lifecycle_configuration" "silver" {
  bucket = aws_s3_bucket.silver.id

  rule {
    id     = "silver_lifecycle"
    status = "Enabled"

    # Transition to Standard IA after 90 days
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    # Transition to Glacier after 2 years for long-term storage
    transition {
      days          = 730
      storage_class = "GLACIER"
    }

    # Clean up incomplete multipart uploads after 7 days
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }

    # Clean up delete markers after 30 days
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# Gold Layer: Keep in Standard for frequent access by MCP server
resource "aws_s3_bucket_lifecycle_configuration" "gold" {
  bucket = aws_s3_bucket.gold.id

  rule {
    id     = "gold_lifecycle"
    status = "Enabled"

    # Only clean up incomplete uploads - keep data in Standard class
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }

    # Clean up delete markers after 30 days
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# S3 Bucket for application data and artifacts (legacy - kept for backward compatibility)
resource "aws_s3_bucket" "main" {
  bucket = "${var.project_name}-${var.environment}-data"

  tags = {
    Name   = "${var.project_name}-main-bucket"
    Status = "legacy"
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
# S3 Bucket Monitoring and Access Logging
# ============================================================================

# S3 Access Logging bucket (to store access logs for all data buckets)
resource "aws_s3_bucket" "access_logs" {
  bucket = "${var.project_name}-access-logs"

  tags = {
    Name    = "${var.project_name}-access-logs-bucket"
    Purpose = "S3 access logging for data buckets"
  }
}

# Access logs bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Access logs bucket public access block
resource "aws_s3_bucket_public_access_block" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Access logs bucket lifecycle (cleanup old logs after 90 days)
resource "aws_s3_bucket_lifecycle_configuration" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id

  rule {
    id     = "access_logs_cleanup"
    status = "Enabled"

    # Transition to IA after 30 days
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Delete logs after 90 days
    expiration {
      days = 90
    }

    # Clean up incomplete multipart uploads
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# S3 Bucket logging configuration for Bronze layer
resource "aws_s3_bucket_logging" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  target_bucket = aws_s3_bucket.access_logs.id
  target_prefix = "bronze-access-logs/"
}

# S3 Bucket logging configuration for Silver layer
resource "aws_s3_bucket_logging" "silver" {
  bucket = aws_s3_bucket.silver.id

  target_bucket = aws_s3_bucket.access_logs.id
  target_prefix = "silver-access-logs/"
}

# S3 Bucket logging configuration for Gold layer
resource "aws_s3_bucket_logging" "gold" {
  bucket = aws_s3_bucket.gold.id

  target_bucket = aws_s3_bucket.access_logs.id
  target_prefix = "gold-access-logs/"
}

# ============================================================================
# S3 CloudWatch Metrics and Alarms for Data Access Monitoring
# ============================================================================

# CloudWatch Metric Filter for S3 access patterns (parsed from access logs via Lambda would be ideal, but for now we'll use CloudTrail events)
resource "aws_cloudwatch_metric_alarm" "bronze_bucket_errors" {
  alarm_name          = "bronze-bucket-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4xxErrors"
  namespace           = "AWS/S3"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors Bronze bucket 4xx errors"

  dimensions = {
    BucketName = aws_s3_bucket.bronze.bucket
  }

  tags = {
    Severity    = "warning"
    Type        = "s3-access"
    DataLayer   = "bronze"
  }
}

resource "aws_cloudwatch_metric_alarm" "silver_bucket_errors" {
  alarm_name          = "silver-bucket-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4xxErrors"
  namespace           = "AWS/S3"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors Silver bucket 4xx errors"

  dimensions = {
    BucketName = aws_s3_bucket.silver.bucket
  }

  tags = {
    Severity    = "warning"
    Type        = "s3-access"
    DataLayer   = "silver"
  }
}

resource "aws_cloudwatch_metric_alarm" "gold_bucket_errors" {
  alarm_name          = "gold-bucket-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4xxErrors"
  namespace           = "AWS/S3"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors Gold bucket 4xx errors"

  dimensions = {
    BucketName = aws_s3_bucket.gold.bucket
  }

  tags = {
    Severity    = "warning"
    Type        = "s3-access"
    DataLayer   = "gold"
  }
}

# Monitor Gold bucket request rates (important for MCP server performance)
resource "aws_cloudwatch_metric_alarm" "gold_bucket_high_requests" {
  alarm_name          = "gold-bucket-high-request-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "AllRequests"
  namespace           = "AWS/S3"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1000"
  alarm_description   = "This metric monitors Gold bucket for unexpectedly high request rates"

  dimensions = {
    BucketName = aws_s3_bucket.gold.bucket
  }

  tags = {
    Severity    = "warning"
    Type        = "s3-performance"
    DataLayer   = "gold"
  }
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