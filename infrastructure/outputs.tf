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

output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions IAM role"
  value       = aws_iam_role.github_actions.arn
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