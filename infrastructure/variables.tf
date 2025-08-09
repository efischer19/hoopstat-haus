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
    example_calculator_app = object({
      timeout     = number
      memory_size = number
    })
    nba_season_backfill = object({
      timeout     = number
      memory_size = number
    })
    bronze_ingestion = object({
      timeout     = number
      memory_size = number
    })
    mcp_server = object({
      timeout     = number
      memory_size = number
    })
  })
  default = {
    example_calculator_app = {
      timeout     = 30
      memory_size = 128
    }
    nba_season_backfill = {
      timeout     = 900 # 15 minutes for data processing
      memory_size = 512
    }
    bronze_ingestion = {
      timeout     = 300 # 5 minutes for data ingestion
      memory_size = 256
    }
    mcp_server = {
      timeout     = 30
      memory_size = 256
    }
  }
}

