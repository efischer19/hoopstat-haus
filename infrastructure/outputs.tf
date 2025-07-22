# ============================================================================
# S3 Medallion Architecture Outputs
# ============================================================================

output "bronze_bucket_name" {
  description = "Name of the Bronze layer S3 bucket"
  value       = aws_s3_bucket.bronze.bucket
}

output "bronze_bucket_arn" {
  description = "ARN of the Bronze layer S3 bucket"
  value       = aws_s3_bucket.bronze.arn
}

output "silver_bucket_name" {
  description = "Name of the Silver layer S3 bucket"
  value       = aws_s3_bucket.silver.bucket
}

output "silver_bucket_arn" {
  description = "ARN of the Silver layer S3 bucket"
  value       = aws_s3_bucket.silver.arn
}

output "gold_bucket_name" {
  description = "Name of the Gold layer S3 bucket"
  value       = aws_s3_bucket.gold.bucket
}

output "gold_bucket_arn" {
  description = "ARN of the Gold layer S3 bucket"
  value       = aws_s3_bucket.gold.arn
}

output "access_logs_bucket_name" {
  description = "Name of the S3 access logs bucket"
  value       = aws_s3_bucket.access_logs.bucket
}

output "access_logs_bucket_arn" {
  description = "ARN of the S3 access logs bucket"
  value       = aws_s3_bucket.access_logs.arn
}

# Data layer IAM role outputs
output "bronze_layer_role_arn" {
  description = "ARN of the Bronze layer access IAM role"
  value       = aws_iam_role.bronze_layer_access.arn
}

output "bronze_layer_role_name" {
  description = "Name of the Bronze layer access IAM role"
  value       = aws_iam_role.bronze_layer_access.name
}

output "silver_layer_role_arn" {
  description = "ARN of the Silver layer access IAM role"
  value       = aws_iam_role.silver_layer_access.arn
}

output "silver_layer_role_name" {
  description = "Name of the Silver layer access IAM role"
  value       = aws_iam_role.silver_layer_access.name
}

output "gold_layer_role_arn" {
  description = "ARN of the Gold layer access IAM role"
  value       = aws_iam_role.gold_layer_access.arn
}

output "gold_layer_role_name" {
  description = "Name of the Gold layer access IAM role"
  value       = aws_iam_role.gold_layer_access.name
}

output "mcp_server_role_arn" {
  description = "ARN of the MCP server access IAM role"
  value       = aws_iam_role.mcp_server_access.arn
}

output "mcp_server_role_name" {
  description = "Name of the MCP server access IAM role"
  value       = aws_iam_role.mcp_server_access.name
}

# Legacy bucket outputs (backward compatibility)
output "s3_bucket_name" {
  description = "Name of the S3 bucket (legacy)"
  value       = aws_s3_bucket.main.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket (legacy)"
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