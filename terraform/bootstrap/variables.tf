variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "github_repository" {
  description = "GitHub repository in format owner/repo"
  type        = string
  default     = "efischer19/hoopstat-haus"
}