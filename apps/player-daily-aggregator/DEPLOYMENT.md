# Deployment Guide

This document provides instructions for deploying the Player Daily Aggregator Lambda function to AWS.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform (if using infrastructure as code)
- Python 3.12 runtime support in target AWS region

## Environment Variables

The Lambda function requires the following environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SILVER_BUCKET` | Yes | - | S3 bucket containing Silver layer data |
| `GOLD_BUCKET` | Yes | - | S3 bucket for Gold layer output |
| `AWS_REGION` | No | us-east-1 | AWS region for S3 operations |
| `MAX_WORKERS` | No | 4 | Maximum worker threads for processing |
| `CHUNK_SIZE` | No | 10000 | Processing chunk size |
| `MIN_EXPECTED_PLAYERS` | No | 1 | Minimum players expected for validation |
| `MAX_NULL_PERCENTAGE` | No | 0.1 | Maximum null percentage allowed (0.1 = 10%) |

## IAM Permissions

The Lambda execution role requires the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::your-silver-bucket/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::your-gold-bucket/*"
        }
    ]
}
```

## S3 Event Trigger Configuration

Configure S3 event notifications on the Silver bucket:

- **Event Types**: `s3:ObjectCreated:*`
- **Prefix**: `silver/player_games/`
- **Suffix**: `.parquet`

## Lambda Configuration

- **Runtime**: Python 3.12
- **Handler**: `app.handler.lambda_handler`
- **Memory**: 512 MB (adjust based on data volume)
- **Timeout**: 5 minutes (adjust based on processing needs)
- **Architecture**: x86_64

## Package Deployment

1. **Install dependencies**:
   ```bash
   poetry export -f requirements.txt --output requirements.txt
   pip install -r requirements.txt -t package/
   ```

2. **Copy application code**:
   ```bash
   cp -r app/ package/
   ```

3. **Create deployment package**:
   ```bash
   cd package/
   zip -r ../player-daily-aggregator.zip .
   ```

4. **Deploy with AWS CLI**:
   ```bash
   aws lambda update-function-code \
     --function-name player-daily-aggregator \
     --zip-file fileb://player-daily-aggregator.zip
   ```

## Testing

After deployment, test with a sample S3 event:

```bash
aws lambda invoke \
  --function-name player-daily-aggregator \
  --payload file://test-event.json \
  response.json
```

Where `test-event.json` contains:
```json
{
  "Records": [{
    "eventSource": "aws:s3",
    "s3": {
      "bucket": {"name": "your-silver-bucket"},
      "object": {"key": "silver/player_games/season=2023-24/date=2024-01-15/player_stats.parquet"}
    }
  }]
}
```

## Monitoring

Monitor the function using:
- CloudWatch Logs: `/aws/lambda/player-daily-aggregator`
- CloudWatch Metrics: Duration, Errors, Invocations
- Custom metrics can be added using the `hoopstat-observability` library

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   - Error: `ValueError: SILVER_BUCKET environment variable is required`
   - Solution: Set required environment variables

2. **S3 Permission Errors**
   - Error: `ClientError: Access Denied`
   - Solution: Verify IAM permissions and bucket policies

3. **Invalid Data Format**
   - Error: `ValidationError: Missing required columns`
   - Solution: Check Silver layer data schema matches expected format

4. **Memory Issues**
   - Error: Task timed out or memory exceeded
   - Solution: Increase Lambda memory allocation or optimize data processing

### Log Analysis

Key log patterns to monitor:
- `Successfully processed N players` - Normal operation
- `ValidationError` - Data quality issues
- `ClientError` - AWS service issues
- `KeyError: Column(s)` - Data schema issues

## Performance Tuning

- Adjust `CHUNK_SIZE` for memory vs. speed tradeoff
- Increase Lambda memory for faster processing
- Consider using Lambda reserved concurrency for high throughput
- Monitor execution duration and optimize aggregation logic if needed