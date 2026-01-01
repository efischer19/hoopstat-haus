# Silver Processing Lambda Deployment Testing Guide

This guide provides instructions for testing the newly deployed silver-processing Lambda function and S3 trigger configuration.

## Infrastructure Deployment

The silver-processing Lambda deployment includes:

- **Lambda Function**: `hoopstat-haus-silver-processing`
  - Memory: 1024MB (suitable for data processing workloads)
  - Timeout: 5 minutes
  - Environment: `BRONZE_BUCKET`, `SILVER_BUCKET`, `LOG_LEVEL`, `APP_NAME`
  - Dead Letter Queue: `hoopstat-haus-silver-processing-dlq`

- **S3 Event Trigger**: Bronze bucket → Lambda
  - Events: `s3:ObjectCreated:*`
  - Filter prefix: `raw/box/`
  - Filter suffix: `/data.json`

- **IAM Permissions**: S3 read/write, CloudWatch logging, SQS (DLQ)

## Testing the End-to-End Flow

### Prerequisites
1. Terraform infrastructure deployed (`terraform apply`)
2. Docker image built and pushed to ECR
3. Lambda function deployed via GitHub Actions

### Manual Testing Steps

#### 1. Verify Lambda Function Exists
```bash
aws lambda get-function --function-name hoopstat-haus-silver-processing
```

#### 2. Check S3 Event Configuration
```bash
aws s3api get-bucket-notification-configuration \
  --bucket hoopstat-haus-bronze
```

Should show a Lambda configuration with the correct filters.

#### 3. Test with Sample Data

Upload a test file to trigger the Lambda:

```bash
# Create sample Bronze data
cat > sample_bronze_data.json << 'EOF'
{
  "game_id": 123,
  "game_date": "2024-01-01",
  "arena": "Test Arena",
  "home_team": {"id": 1, "name": "Test Lakers", "city": "Los Angeles"},
  "away_team": {"id": 2, "name": "Test Celtics", "city": "Boston"},
  "home_team_stats": {"points": 108},
  "away_team_stats": {"points": 102},
  "players": []
}
EOF

# Upload to Bronze bucket (this should trigger the Lambda)
aws s3 cp sample_bronze_data.json \
  s3://hoopstat-haus-bronze/raw/box/2024-01-01/data.json
```

#### 4. Monitor Lambda Execution

Check CloudWatch logs:
```bash
aws logs tail /hoopstat-haus/data-pipeline --follow
```

Check Lambda metrics:
```bash
aws lambda get-function --function-name hoopstat-haus-silver-processing \
  --query 'Configuration.LastModified'
```

#### 5. Verify Silver Output

Check if Silver data was created:
```bash
aws s3 ls s3://hoopstat-haus-silver/processed/box/date=2024-01-01/
```

#### 6. Test Error Handling

Upload invalid data to test DLQ:
```bash
# Upload invalid JSON
echo "invalid json" | aws s3 cp - \
  s3://hoopstat-haus-bronze/raw/box/2024-01-02/data.json
```

Check DLQ for failed messages:
```bash
aws sqs receive-message --queue-url $(aws sqs get-queue-url \
  --queue-name hoopstat-haus-silver-processing-dlq --output text)
```

## Testing Scenarios

### Positive Test Cases
- [ ] Valid Bronze data triggers Lambda successfully
- [ ] Silver data is created in correct S3 location
- [ ] CloudWatch logs show successful processing
- [ ] Lambda completes within timeout (< 5 minutes)

### Negative Test Cases  
- [ ] Invalid JSON triggers DLQ message
- [ ] Missing required fields handled gracefully
- [ ] Lambda timeout scenarios logged properly
- [ ] S3 permission errors handled correctly

### Filter Test Cases
- [ ] Files with correct prefix/suffix trigger Lambda
- [ ] Files outside filter pattern are ignored:
  - `raw/box/summary.json` (no date prefix)
  - `raw/box/2024-01-01/metadata.json` (wrong suffix)
  - `processed/box/date=2024-01-01/data.json` (wrong prefix)

## Monitoring and Observability

### CloudWatch Alarms
- `lambda-errors-silver-processing`: Monitors Lambda errors
- `lambda-duration-silver-processing`: Monitors execution time
- `lambda-throttles-silver-processing`: Monitors throttling

### Key Metrics to Monitor
- **Invocations**: Number of Lambda executions
- **Duration**: Execution time per invocation
- **Errors**: Failed executions
- **Throttles**: Rate limiting incidents
- **DLQ Messages**: Number of failed processing attempts

### Logs Analysis
```bash
# Filter for errors
aws logs filter-log-events \
  --log-group-name /hoopstat-haus/data-pipeline \
  --filter-pattern "ERROR"

# Filter for silver-processing
aws logs filter-log-events \
  --log-group-name /hoopstat-haus/data-pipeline \
  --filter-pattern "silver-processing"
```

## Troubleshooting

### Common Issues

1. **Lambda not triggered by S3 events**
   - Check S3 bucket notification configuration
   - Verify Lambda permissions for S3 invocation
   - Confirm file paths match filter criteria

2. **Lambda timeout errors**
   - Check data size and processing complexity
   - Consider increasing memory allocation
   - Optimize data processing logic

3. **Permission errors**
   - Verify IAM role has S3 read/write permissions
   - Check CloudWatch logging permissions
   - Confirm SQS DLQ permissions

4. **DLQ messages accumulating**
   - Investigate error patterns in CloudWatch logs
   - Review data quality issues
   - Consider implementing retry logic

### Recovery Procedures

1. **Reprocess failed data**:
   ```bash
   # Re-upload file to trigger reprocessing
   aws s3 cp s3://source/path s3://hoopstat-haus-bronze/raw/box/YYYY-MM-DD/data.json
   ```

2. **Manual Lambda invocation**:
   ```bash
   aws lambda invoke \
     --function-name hoopstat-haus-silver-processing \
     --payload '{"test": true}' \
     response.json
   ```

## Success Criteria

The deployment is successful when:
- [x] Lambda function deploys without errors
- [x] S3 event notification is configured correctly  
- [x] Test data upload triggers Lambda execution
- [x] Silver data is created in expected S3 location
- [x] CloudWatch logs show successful processing
- [x] Error handling routes failures to DLQ
- [x] All monitoring alarms are configured
- [x] End-to-end test passes: Bronze → S3 Event → Lambda → Silver