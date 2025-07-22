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

# IAM Policy for GitHub Actions
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
          aws_s3_bucket.main.arn,
          "${aws_s3_bucket.main.arn}/*"
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