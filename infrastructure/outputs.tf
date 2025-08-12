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