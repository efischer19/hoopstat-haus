# AWS Lambda Deployment Infrastructure

This document describes the AWS Lambda deployment infrastructure for containerized applications in the Hoopstat Haus project.

## Overview

The infrastructure supports deploying containerized Python applications as AWS Lambda functions with automated CI/CD integration. This implementation follows the established ADRs:

- **ADR-009**: AWS as cloud provider
- **ADR-010**: Terraform for Infrastructure as Code
- **ADR-011**: GitHub OIDC for authentication

## Architecture

### Lambda Functions

The infrastructure provisions 2 Lambda functions for existing containerized applications:

| Function Name | Purpose | Timeout | Memory | Log Group |
|---------------|---------|---------|--------|-----------|
| `hoopstat-haus-bronze-ingestion` | Data ingestion to bronze layer | 5min | 256MB | `/hoopstat-haus/data-pipeline` |
| `hoopstat-haus-mcp-server` | MCP server API | 30s | 256MB | `/hoopstat-haus/applications` |

### IAM Roles and Permissions

#### Lambda Execution Role (`hoopstat-haus-lambda-execution`)

Grants Lambda functions access to:
- **CloudWatch Logs**: Create log streams and put log events
- **S3 Buckets**: Read/write access to medallion architecture buckets (bronze, silver, gold)
- **ECR**: Pull container images for deployment

#### Environment Variables

Each Lambda function is configured with:
- `LOG_LEVEL`: Set to "INFO"
- `APP_NAME`: Application identifier
- `AWS_REGION`: AWS region
- Bucket-specific variables (e.g., `BRONZE_BUCKET`, `SILVER_BUCKET`, `GOLD_BUCKET`)

### Monitoring and Observability

#### CloudWatch Alarms

The infrastructure includes comprehensive monitoring:

1. **Error Alarms** (`lambda-errors-{app}`): Triggers on any function errors
2. **Duration Alarms** (`lambda-duration-{app}`): Monitors execution time (83% of timeout threshold)
3. **Throttle Alarms** (`lambda-throttles-{app}`): Detects function throttling

#### Logging Integration

- Functions log to existing CloudWatch log groups
- JSON log format for structured logging (per ADR-015)
- Log retention policies already configured in infrastructure

## Deployment Process

### Automated Deployment (GitHub Actions)

The deployment workflow (`.github/workflows/deploy.yml`) automatically:

1. **Detects Changes**: Identifies modified apps with Dockerfiles
2. **Verifies Images**: Ensures container images exist in ECR
3. **Updates Functions**: Deploys new container images to Lambda
4. **Tests Deployment**: Performs health checks for API services
5. **Monitors Status**: Waits for functions to become active

### Manual Deployment

You can also deploy manually using the GitHub Actions workflow dispatch:

```bash
# Via GitHub CLI
gh workflow run deploy.yml \
  --field application=bronze-ingestion \
  --field environment=prod \
  --field image_tag=latest

# Via GitHub UI
# Go to Actions > Deploy Applications > Run workflow
```

### Image Tagging Convention

Container images in ECR follow the pattern:
```
{ECR_REPOSITORY}:{APP_NAME}-{IMAGE_TAG}
```

Example:
```
123456789012.dkr.ecr.us-east-1.amazonaws.com/hoopstat-haus/prod:bronze-ingestion-abc123
```

## Cost Optimization

### Memory and Timeout Configuration

Function configurations are optimized for cost:

- **API Services** (mcp-server): 30s timeout, minimal memory
- **Data Ingestion** (bronze-ingestion): Balanced configuration

### Lifecycle Management

- **Image URI Changes**: Ignored in Terraform (managed by CI/CD)
- **ECR Lifecycle**: Automatic cleanup of old images
- **CloudWatch Logs**: Retention policies limit storage costs

## Security

### Least Privilege Access

- Lambda execution role has minimal required permissions
- Bucket access limited to specific medallion layers
- No internet access beyond AWS services

### Container Security

- Functions run using official Python base images
- Non-root user in production containers
- Security scanning enabled in ECR

## Configuration Management

### Terraform Variables

Key configuration options in `variables.tf`:

```hcl
variable "lambda_config" {
  description = "Configuration for Lambda functions"
  type = object({
    bronze_ingestion = object({
      timeout     = number
      memory_size = number
    })
    mcp_server = object({
      timeout     = number
      memory_size = number
    })
  })
}
```

### Environment-Specific Overrides

Override defaults using Terraform variables:

```bash
terraform plan -var="lambda_config.bronze_ingestion.timeout=600"
```

## Testing

### Infrastructure Validation

Run the test suite to validate configuration:

```bash
cd infrastructure/tests
python3 lambda_deployment_test.py
```

### Function Testing

The deployment workflow includes:
- **Health Checks**: Basic import verification
- **Test Invocations**: For API services only
- **Status Monitoring**: Function active state verification

## Troubleshooting

### Common Issues

1. **Image Not Found**: Ensure container image exists in ECR with correct tag
2. **Permission Denied**: Verify Lambda execution role has required permissions
3. **Timeout Errors**: Check function timeout settings and CloudWatch logs
4. **Memory Issues**: Monitor memory usage and adjust allocation

### Monitoring

Use CloudWatch dashboards to monitor:
- Function invocation counts and errors
- Duration and memory utilization
- Throttling and concurrent executions

### Debugging

Access function logs via:
```bash
aws logs tail /hoopstat-haus/applications --follow
aws logs tail /hoopstat-haus/data-pipeline --follow
```

## Future Enhancements

### Planned Improvements

1. **Auto-scaling**: Configure reserved concurrency based on usage patterns
2. **Dead Letter Queues**: Add error handling for failed executions
3. **API Gateway**: Add HTTP endpoints for web-accessible functions
4. **VPC Integration**: Enable VPC access for database connections
5. **Secrets Management**: Integrate AWS Secrets Manager for sensitive config

### Migration Path

The infrastructure supports easy migration to other compute platforms:
- Container images can be deployed to ECS Fargate
- Functions can be converted to long-running services
- Monitoring and logging patterns are reusable

## References

- [AWS Lambda Container Image Support](https://docs.aws.amazon.com/lambda/latest/dg/lambda-images.html)
- [Terraform AWS Lambda Function](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function)
- [CloudWatch Lambda Monitoring](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchmetrics.html)