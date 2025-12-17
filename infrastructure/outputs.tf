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
    access_logs = {
      name = aws_s3_bucket.access_logs.bucket
      arn  = aws_s3_bucket.access_logs.arn
    }
  }
}

output "medallion_iam_roles" {
  description = "IAM roles for Medallion Architecture data access"
  value = {
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
    bronze_ingestion = {
      function_name = aws_lambda_function.bronze_ingestion.function_name
      function_arn  = aws_lambda_function.bronze_ingestion.arn
      invoke_arn    = aws_lambda_function.bronze_ingestion.invoke_arn
    }
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
# S3 Tables Outputs (ADR-026)
# ============================================================================

output "s3_tables_gold_analytics" {
  description = "S3 Tables configuration for Gold layer analytics with public read access"
  value = {
    table_bucket = {
      name = aws_s3tables_table_bucket.gold_tables.name
      arn  = aws_s3tables_table_bucket.gold_tables.arn
    }
    namespace = {
      name = aws_s3tables_namespace.basketball_analytics.namespace
    }
    tables = {
      player_analytics = {
        name = aws_s3tables_table.player_analytics.name
        arn  = aws_s3tables_table.player_analytics.arn
      }
      team_analytics = {
        name = aws_s3tables_table.team_analytics.name
        arn  = aws_s3tables_table.team_analytics.arn
      }
    }
    region = var.aws_region
    public_access = {
      enabled            = true
      policy_description = "Anonymous read access for MCP clients"
    }
    mcp_server_config = {
      command = "uvx"
      args    = ["awslabs.s3-tables-mcp-server@latest", "--allow-read"]
      env = {
        AWS_REGION       = var.aws_region
        S3_TABLES_BUCKET = aws_s3tables_table_bucket.gold_tables.name
        # No AWS credentials needed for public access
      }
    }
    example_queries = [
      "Show me LeBron's efficiency this week",
      "What's the Lakers defensive rating this month?",
      "Top 10 players by True Shooting % yesterday",
      "Compare team offensive ratings for the 2023-24 season"
    ]
    adr_reference = "ADR-026"
  }
}