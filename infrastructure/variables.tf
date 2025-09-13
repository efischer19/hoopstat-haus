variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "hoopstat-haus"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}


variable "log_retention_days" {
  description = "CloudWatch log retention periods by log type"
  type = object({
    applications   = number
    data_pipeline  = number
    infrastructure = number
  })
  default = {
    applications   = 30
    data_pipeline  = 90
    infrastructure = 14
  }
}

variable "github_repo" {
  description = "GitHub repository in format owner/repo for OIDC integration"
  type        = string
  default     = "efischer19/hoopstat-haus"
}

variable "lambda_config" {
  description = "Configuration for Lambda functions"
  type = object({
    bronze_ingestion = object({
      timeout     = number
      memory_size = number
    })
    silver_processing = object({
      timeout     = number
      memory_size = number
    })
    gold_processing = object({
      timeout     = number
      memory_size = number
    })
  })
  default = {
    bronze_ingestion = {
      timeout     = 300 # 5 minutes for data ingestion
      memory_size = 256
    }
    silver_processing = {
      timeout     = 300  # 5 minutes for data processing
      memory_size = 1024 # 1GB for data processing workloads
    }
    gold_processing = {
      timeout     = 600  # 10 minutes for analytics calculations
      memory_size = 2048 # 2GB for S3 Tables and analytics processing
    }
  }
}

