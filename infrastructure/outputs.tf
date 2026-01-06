output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.main.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.main.arn
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.main.repository_url
}

output "ecr_repository_arn" {
  description = "ARN of the ECR repository"
  value       = aws_ecr_repository.main.arn
}

# Note: GitHub Actions admin IAM role output removed due to circular dependency.
# Admin role is managed outside of Terraform to enable bootstrap process.

# GitHub Actions operations role (managed in Terraform)
output "github_actions_operations_role_arn" {
  description = "ARN of the GitHub Actions operations IAM role"
  value       = aws_iam_role.github_actions_operations.arn
}

output "github_actions_operations_role_name" {
  description = "Name of the GitHub Actions operations IAM role"
  value       = aws_iam_role.github_actions_operations.name
}

# ============================================================================
# CloudWatch Observability Outputs (ADR-018)
# ============================================================================

output "log_group_names" {
  description = "Names of the created CloudWatch log groups"
  value = {
    applications   = aws_cloudwatch_log_group.applications.name
    data_pipeline  = aws_cloudwatch_log_group.data_pipeline.name
    infrastructure = aws_cloudwatch_log_group.infrastructure.name
  }
}

output "log_group_arns" {
  description = "ARNs of the created CloudWatch log groups"
  value = {
    applications   = aws_cloudwatch_log_group.applications.arn
    data_pipeline  = aws_cloudwatch_log_group.data_pipeline.arn
    infrastructure = aws_cloudwatch_log_group.infrastructure.arn
  }
}



output "lambda_logging_role_arn" {
  description = "ARN of the IAM role for Lambda logging"
  value       = aws_iam_role.lambda_logging.arn
}

output "lambda_logging_role_name" {
  description = "Name of the IAM role for Lambda logging"
  value       = aws_iam_role.lambda_logging.name
}

# ============================================================================
# Medallion Architecture S3 Bucket Outputs
# ============================================================================

output "medallion_s3_buckets" {
  description = "Information about the Medallion Architecture S3 buckets"
  value = {
    bronze = {
      name = aws_s3_bucket.bronze.bucket
      arn  = aws_s3_bucket.bronze.arn
    }
    silver = {
      name = aws_s3_bucket.silver.bucket
      arn  = aws_s3_bucket.silver.arn
    }
    gold = {
      name = aws_s3_bucket.gold.bucket
      arn  = aws_s3_bucket.gold.arn
    }
    access_logs = {
      name = aws_s3_bucket.access_logs.bucket
      arn  = aws_s3_bucket.access_logs.arn
    }
  }
}

output "medallion_iam_roles" {
  description = "IAM roles for Medallion Architecture data access"
  value = {
    bronze_data_access = {
      name = aws_iam_role.bronze_data_access.name
      arn  = aws_iam_role.bronze_data_access.arn
    }
    silver_data_access = {
      name = aws_iam_role.silver_data_access.name
      arn  = aws_iam_role.silver_data_access.arn
    }
    gold_data_access = {
      name = aws_iam_role.gold_data_access.name
      arn  = aws_iam_role.gold_data_access.arn
    }
  }
}

# ============================================================================
# Lambda Function Outputs
# ============================================================================

output "lambda_functions" {
  description = "Information about deployed Lambda functions"
  value = {
    silver_processing = {
      function_name = aws_lambda_function.silver_processing.function_name
      function_arn  = aws_lambda_function.silver_processing.arn
      invoke_arn    = aws_lambda_function.silver_processing.invoke_arn
    }
    gold_processing = {
      function_name = aws_lambda_function.gold_processing.function_name
      function_arn  = aws_lambda_function.gold_processing.arn
      invoke_arn    = aws_lambda_function.gold_processing.invoke_arn
    }
  }
}

output "lambda_execution_role" {
  description = "Lambda execution role information"
  value = {
    name = aws_iam_role.lambda_execution.name
    arn  = aws_iam_role.lambda_execution.arn
  }
}

# ============================================================================
# Gold Layer S3 Bucket Output (ADR-028)
# ============================================================================

output "gold_bucket" {
  description = "Gold layer S3 bucket for Parquet storage and served/ JSON artifacts"
  value = {
    name = aws_s3_bucket.gold.bucket
    arn  = aws_s3_bucket.gold.arn
  }
}

# ============================================================================
# CloudFront Distribution Outputs for Public JSON Artifacts
# ============================================================================

output "cloudfront_distribution" {
  description = "CloudFront distribution for public JSON artifacts"
  value = {
    id          = aws_cloudfront_distribution.gold_served.id
    arn         = aws_cloudfront_distribution.gold_served.arn
    domain_name = aws_cloudfront_distribution.gold_served.domain_name
    status      = aws_cloudfront_distribution.gold_served.status
  }
}

output "public_artifact_urls" {
  description = "Public URLs for accessing JSON artifacts"
  value = {
    cloudfront_base_url = "https://${aws_cloudfront_distribution.gold_served.domain_name}"
    s3_direct_base_url  = "https://${aws_s3_bucket.gold.bucket}.s3.${var.aws_region}.amazonaws.com/served"
    example_player_url  = "https://${aws_cloudfront_distribution.gold_served.domain_name}/player_daily/2024-11-15/2544.json"
    example_team_url    = "https://${aws_cloudfront_distribution.gold_served.domain_name}/team_daily/2024-11-15/1610612747.json"
    example_index_url   = "https://${aws_cloudfront_distribution.gold_served.domain_name}/index/latest.json"
  }
}