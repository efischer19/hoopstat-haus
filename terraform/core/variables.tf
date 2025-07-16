variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., prod, dev, staging)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Name of the project (used in resource naming)"
  type        = string
  default     = "hoopstat-haus"
}

variable "github_repository" {
  description = "GitHub repository in format owner/repo"
  type        = string
  default     = "efischer19/hoopstat-haus"
}

variable "github_oidc_provider_arn" {
  description = "ARN of the GitHub OIDC Identity Provider (from bootstrap)"
  type        = string
}

variable "application_names" {
  description = "List of application names for ECR repositories"
  type        = list(string)
  default = [
    "data-pipeline",
    "stats-api",
    "web-dashboard"
  ]
}