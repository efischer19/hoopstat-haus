# CloudWatch Observability Infrastructure

This directory contains Terraform infrastructure for AWS CloudWatch observability as defined in ADR-017.

## Overview

The infrastructure provides:
- **CloudWatch Log Groups** with appropriate retention policies
- **Metric Filters** to extract performance metrics from JSON logs (ADR-015)
- **CloudWatch Alarms** for error rates, timeouts, and performance anomalies
- **SNS Topics** for alert routing by severity
- **IAM Roles** for Lambda function logging permissions

## Quick Start

1. **Install Terraform** (version >= 1.0)

2. **Initialize Terraform**:
   ```bash
   cd infrastructure/observability
   terraform init
   ```

3. **Review the plan**:
   ```bash
   terraform plan
   ```

4. **Apply the infrastructure**:
   ```bash
   terraform apply
   ```

## Configuration

### Required Variables

- `aws_region`: AWS region (default: "us-east-1")
- `project_name`: Project name (default: "hoopstat-haus")
- `environment`: Environment name (must be "production" per ADR-012)

### Optional Variables

- `alert_email`: Email address for SNS notifications
- `log_retention_days`: Retention periods by log type

### Example Usage

```bash
terraform apply -var="alert_email=admin@example.com"
```

## Log Groups

| Log Group | Purpose | Retention |
|-----------|---------|-----------|
| `/hoopstat-haus/applications` | General application logs | 30 days |
| `/hoopstat-haus/data-pipeline` | Data processing jobs | 90 days |
| `/hoopstat-haus/infrastructure` | System logs | 14 days |

## Metric Extraction (ADR-015 Integration)

The infrastructure automatically extracts metrics from JSON logs:

- **ExecutionDuration**: From `duration_in_seconds` field
- **RecordsProcessed**: From `records_processed` field  
- **ErrorCount**: From log level "ERROR"

### Example Log Entry

```json
{
  "timestamp": "2025-01-27T14:30:45.123Z",
  "level": "INFO",
  "message": "Data pipeline job completed",
  "job_name": "daily_stats",
  "duration_in_seconds": 45.67,
  "records_processed": 15420,
  "correlation_id": "job-20250127-143000-abc123"
}
```

## Default Alarms

| Alarm | Threshold | Severity | Description |
|-------|-----------|----------|-------------|
| High Error Rate | >5 errors in 5min | Critical | Application error monitoring |
| Lambda Timeout | >15 minutes | Critical | Function timeout detection |
| Execution Time Anomaly | >5 minutes avg | Warning | Performance degradation |

## Alert Routing

- **Critical**: Immediate response required
- **Warning**: Investigation within 24 hours
- **Info**: Dashboard visibility only

## Testing

Run the infrastructure tests:

```bash
cd tests/infrastructure
python -m pytest test_observability.py -v
```

## Integration with Lambda Functions

Use the created IAM role for Lambda functions:

```python
# Example Lambda function configuration
import json
import logging
import time

# Configure JSON logging per ADR-015
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    start_time = time.time()
    
    try:
        # Your Lambda logic here
        records_processed = process_data(event)
        
        # Log completion with ADR-015 fields
        duration = time.time() - start_time
        logger.info(json.dumps({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": "INFO",
            "message": "Lambda execution completed",
            "function_name": context.function_name,
            "duration_in_seconds": round(duration, 3),
            "records_processed": records_processed,
            "correlation_id": context.aws_request_id
        }))
        
        return {"statusCode": 200, "body": "Success"}
        
    except Exception as e:
        logger.error(json.dumps({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": "ERROR", 
            "message": f"Lambda execution failed: {str(e)}",
            "function_name": context.function_name,
            "correlation_id": context.aws_request_id
        }))
        raise
```

## Outputs

The infrastructure provides these outputs for integration:

- `log_group_names`: CloudWatch log group names
- `log_group_arns`: CloudWatch log group ARNs
- `sns_topic_arns`: SNS topic ARNs for alerts
- `lambda_logging_role_arn`: IAM role ARN for Lambda logging

## Cost Optimization

- Log retention periods are optimized for different use cases
- Metric filters only extract essential metrics
- Alarms use reasonable thresholds to avoid alert fatigue
- SNS notifications only for actionable alerts