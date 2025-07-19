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
  default     = "production"
  
  validation {
    condition     = var.environment == "production"
    error_message = "Only production environment is supported per ADR-012."
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention periods by log type"
  type = object({
    applications  = number
    data_pipeline = number
    infrastructure = number
  })
  default = {
    applications   = 30
    data_pipeline  = 90
    infrastructure = 14
  }
}

variable "alert_email" {
  description = "Email address for alert notifications"
  type        = string
  default     = ""
}