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

variable "cloudfront_aliases" {
  description = "Optional custom domain names (CNAMEs) for the CloudFront distribution, e.g. [\"hoopstat.haus\", \"www.hoopstat.haus\"]."
  type        = list(string)
  default     = []
}

variable "cloudfront_acm_certificate_arn" {
  description = "Optional ACM certificate ARN for the CloudFront distribution (must be in us-east-1). When empty, CloudFront default certificate is used."
  type        = string
  default     = ""
}

variable "cloudfront_enable_www_redirect" {
  description = "When true, redirects www.<apex> to the apex domain at the edge (viewer-request)."
  type        = bool
  default     = true
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
    silver_processing = {
      timeout     = 300  # 5 minutes for data processing
      memory_size = 1024 # 1GB for data processing workloads
    }
    gold_processing = {
      timeout     = 300  # 5 minutes for complex aggregations
      memory_size = 1024 # 1GB matching silver-processing
    }
  }
}

