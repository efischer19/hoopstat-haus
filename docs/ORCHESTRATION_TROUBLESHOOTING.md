# Daily Orchestration Troubleshooting Guide

This guide provides troubleshooting procedures for the daily orchestration pipeline that automatically processes data from Bronze → Silver → Gold layers using S3 events and SQS queues.

## Architecture Overview

```
Daily Cron (Local) → Bronze Lambda → S3 Event → SQS Queue → Silver Lambda → S3 Event → SQS Queue → Gold Lambda → S3 Tables
```

## Quick Health Check

Use the provided test script to check the overall health of the orchestration pipeline:

```bash
# Run full health check
./scripts/test-orchestration.sh

# Check just infrastructure components
./scripts/test-orchestration.sh check

# Check SQS queue depths
./scripts/test-orchestration.sh queues

# Check recent logs
./scripts/test-orchestration.sh logs

# Test Lambda functions
./scripts/test-orchestration.sh lambdas
```

## Common Issues and Solutions

### 1. Bronze Ingestion Not Running

**Symptoms:**
- No new files in Bronze S3 bucket
- Cron job not executing

**Diagnosis:**
```bash
# Check crontab
crontab -l

# Check cron logs (varies by system)
tail -f /var/log/cron
# or
tail -f /var/log/syslog | grep CRON

# Check bronze ingestion logs
tail -f ~/bronze-ingestion-local/logs/bronze-ingestion-$(date +%Y%m%d).log
```

**Solutions:**
- Verify cron service is running: `sudo systemctl status cron`
- Check AWS credentials: `aws sts get-caller-identity`
- Re-run setup: `apps/bronze-ingestion/setup-local.sh`
- Test manual execution: `~/bronze-ingestion-local/run-daily.sh`

### 2. Silver Processing Not Triggered

**Symptoms:**
- New bronze files exist but no silver processing
- High SQS queue depth for silver-processing-queue

**Diagnosis:**
```bash
# Check S3 bucket notification configuration
aws s3api get-bucket-notification-configuration --bucket hoopstat-haus-bronze

# Check SQS queue for messages
aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name hoopstat-haus-silver-processing-queue --output text) \
  --attribute-names All

# Check Lambda function status
aws lambda get-function --function-name hoopstat-haus-silver-processing
```

**Solutions:**
- Verify S3 event filters match bronze file patterns: `raw/box_scores/date=*/data.json`
- Check SQS queue policy allows S3 to send messages
- Verify Lambda event source mapping is active
- Check Lambda function CloudWatch logs for errors

### 3. Gold Analytics Not Triggered

**Symptoms:**
- Silver files exist but gold processing not running
- High SQS queue depth for gold-analytics-queue

**Diagnosis:**
```bash
# Check silver bucket notifications
aws s3api get-bucket-notification-configuration --bucket hoopstat-haus-silver

# Check gold analytics queue
aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name hoopstat-haus-gold-analytics-queue --output text) \
  --attribute-names All

# Check Lambda function
aws lambda get-function --function-name hoopstat-haus-gold-analytics
```

**Solutions:**
- Verify S3 event filters match silver file patterns: `silver/*.parquet`
- Check SQS queue policy configuration
- Verify Lambda event source mapping configuration
- Review Lambda function logs

### 4. High SQS Queue Depths

**Symptoms:**
- CloudWatch alarms for queue depth
- Processing backlog

**Diagnosis:**
```bash
# Check queue attributes
aws sqs get-queue-attributes \
  --queue-url YOUR_QUEUE_URL \
  --attribute-names ApproximateNumberOfVisibleMessages,ApproximateNumberOfNotVisibleMessages

# Check Lambda concurrency
aws lambda get-function-concurrency --function-name YOUR_FUNCTION_NAME
```

**Solutions:**
- Increase Lambda reserved concurrency
- Check for Lambda errors causing message reprocessing
- Verify visibility timeout matches Lambda timeout
- Monitor dead letter queues for failed messages

### 5. Messages in Dead Letter Queues

**Symptoms:**
- CloudWatch alarms for dead letter queue messages
- Processing failures

**Diagnosis:**
```bash
# Check dead letter queue messages
aws sqs receive-message \
  --queue-url $(aws sqs get-queue-url --queue-name hoopstat-haus-silver-processing-dlq --output text) \
  --max-number-of-messages 1

# Check Lambda error logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/hoopstat-haus-silver-processing \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern "ERROR"
```

**Solutions:**
- Review Lambda function logs for error patterns
- Fix code issues and redeploy
- Manually reprocess messages if needed
- Purge dead letter queue after fixing issues

### 6. Lambda Function Errors

**Common Error Patterns:**

**ImportError/ModuleNotFoundError:**
```bash
# Check Lambda layer configuration
aws lambda get-function --function-name YOUR_FUNCTION_NAME --query 'Configuration.Layers'

# Verify container image is properly built and deployed
```

**Timeout Errors:**
```bash
# Check Lambda timeout configuration
aws lambda get-function-configuration --function-name YOUR_FUNCTION_NAME --query 'Timeout'

# Increase timeout if processing takes longer
aws lambda update-function-configuration --function-name YOUR_FUNCTION_NAME --timeout 300
```

**Memory Errors:**
```bash
# Check memory configuration
aws lambda get-function-configuration --function-name YOUR_FUNCTION_NAME --query 'MemorySize'

# Monitor memory usage in CloudWatch
```

**Permission Errors:**
```bash
# Check IAM role permissions
aws lambda get-function --function-name YOUR_FUNCTION_NAME --query 'Configuration.Role'

# Review IAM policy attached to the role
```

## Monitoring and Alerting

### CloudWatch Alarms

The infrastructure includes several CloudWatch alarms:

1. **Queue Depth Alarms**: Alert when SQS queues have >50 messages
2. **Dead Letter Queue Alarms**: Alert on any messages in DLQ
3. **Lambda Duration Alarms**: Alert on functions running >4.17 minutes
4. **Lambda Error Alarms**: Alert on function errors

### Key Metrics to Monitor

```bash
# SQS queue depths
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfVisibleMessages \
  --dimensions Name=QueueName,Value=hoopstat-haus-silver-processing-queue \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# Lambda invocation counts
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=hoopstat-haus-silver-processing \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Lambda error rates
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=hoopstat-haus-silver-processing \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## Manual Recovery Procedures

### Reprocessing Failed Data

If data processing fails, you can manually trigger reprocessing:

```bash
# Manually invoke silver processing for a specific date
aws lambda invoke \
  --function-name hoopstat-haus-silver-processing \
  --payload '{
    "Records": [{
      "eventSource": "aws:s3",
      "s3": {
        "bucket": {"name": "hoopstat-haus-bronze"},
        "object": {"key": "raw/box_scores/date=2024-01-15/data.json"}
      }
    }]
  }' \
  response.json

# Manually invoke gold analytics for a specific date
aws lambda invoke \
  --function-name hoopstat-haus-gold-analytics \
  --payload '{
    "Records": [{
      "eventSource": "aws:s3",
      "s3": {
        "bucket": {"name": "hoopstat-haus-silver"},
        "object": {"key": "silver/player_stats/season=2024-25/date=2024-01-15/data.parquet"}
      }
    }]
  }' \
  response.json
```

### Clearing Queue Backlogs

If queues get backed up:

```bash
# Purge messages from a queue (use with caution)
aws sqs purge-queue --queue-url YOUR_QUEUE_URL

# Temporarily increase Lambda concurrency
aws lambda put-provisioned-concurrency-config \
  --function-name YOUR_FUNCTION_NAME \
  --provisioned-concurrency-config ProvisionedConcurrencyValue=10

# Scale back after processing
aws lambda delete-provisioned-concurrency-config --function-name YOUR_FUNCTION_NAME
```

## Emergency Contacts and Escalation

- **Infrastructure Issues**: Check AWS CloudFormation/Terraform state
- **Code Issues**: Review recent commits in GitHub repository
- **Data Issues**: Verify source data availability and quality

## Useful Commands Reference

```bash
# Quick status check
./scripts/test-orchestration.sh check

# Monitor real-time logs
aws logs tail /aws/lambda/hoopstat-haus-silver-processing --follow

# Check queue depths
aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name hoopstat-haus-silver-processing-queue --output text) \
  --attribute-names ApproximateNumberOfVisibleMessages

# List recent S3 objects
aws s3 ls s3://hoopstat-haus-bronze/raw/box_scores/ --recursive | tail -10
aws s3 ls s3://hoopstat-haus-silver/silver/ --recursive | tail -10
```