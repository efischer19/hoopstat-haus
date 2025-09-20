# S3 Event-Triggered Data Pipeline Testing Guide

This document provides instructions for testing the complete S3 event-triggered data pipeline: Bronze → Silver → Gold → S3 Tables.

## Overview

The orchestration is now implemented with simple S3 event triggers:

```
Local Cron → Bronze Lambda → S3 Event → Silver Lambda → S3 Event → Gold Lambda → S3 Tables
```

## Prerequisites

1. AWS credentials configured
2. All Lambda functions deployed (`bronze-ingestion`, `silver-processing`, `gold-analytics`) 
3. S3 buckets created (`bronze`, `silver`, `gold`)
4. S3 event notifications configured (via Terraform)

## Testing the Complete Pipeline

### Method 1: Manual Bronze Ingestion (Recommended)

Trigger the pipeline by manually invoking the bronze ingestion Lambda:

```bash
# 1. Trigger bronze ingestion for a specific date
aws lambda invoke \
  --function-name hoopstat-haus-bronze-ingestion \
  --payload '{
    "source": "manual-test", 
    "trigger_type": "manual",
    "parameters": {
      "date": "2024-01-15",
      "dry_run": false,
      "force_run": true
    }
  }' \
  /tmp/bronze-response.json

# 2. Check the response
cat /tmp/bronze-response.json
```

### Method 2: Upload Test File to Bronze Bucket

Simulate a cron job by uploading test data directly:

```bash
# 1. Create test bronze data
echo '{"test": "data", "date": "2024-01-15"}' > /tmp/test-data.json

# 2. Upload to bronze bucket (triggers silver processing)
aws s3 cp /tmp/test-data.json s3://hoopstat-haus-bronze/raw/box_scores/date=2024-01-15/data.json

# 3. This should automatically trigger the cascade
```

## Monitoring the Pipeline

### 1. CloudWatch Logs

Monitor each Lambda function's logs:

```bash
# Bronze ingestion logs
aws logs tail /hoopstat-haus/data-pipeline --filter-pattern="bronze"

# Silver processing logs  
aws logs tail /hoopstat-haus/data-pipeline --filter-pattern="silver"

# Gold analytics logs
aws logs tail /hoopstat-haus/data-pipeline --filter-pattern="gold"
```

### 2. S3 Bucket Contents

Check that data flows through each layer:

```bash
# Check bronze layer
aws s3 ls s3://hoopstat-haus-bronze/raw/box_scores/ --recursive

# Check silver layer
aws s3 ls s3://hoopstat-haus-silver/silver/ --recursive

# Check gold layer (S3 Tables)
aws s3 ls s3://hoopstat-haus-gold/ --recursive
```

### 3. Lambda Function Metrics

Check invocation metrics:

```bash
# Recent Lambda invocations
aws lambda get-function --function-name hoopstat-haus-bronze-ingestion | jq '.Configuration.LastModified'
aws lambda get-function --function-name hoopstat-haus-silver-processing | jq '.Configuration.LastModified'  
aws lambda get-function --function-name hoopstat-haus-gold-analytics | jq '.Configuration.LastModified'
```

## Expected Flow

1. **Bronze Ingestion**
   - Creates: `s3://bronze/raw/box_scores/date=YYYY-MM-DD/data.json`
   - Triggers: Silver processing Lambda via S3 event

2. **Silver Processing** 
   - Reads: Bronze data from above path
   - Creates: `s3://silver/silver/{entity_type}/date=YYYY-MM-DD/{entity}.json`
   - Triggers: Gold analytics Lambda via S3 event

3. **Gold Analytics**
   - Reads: Silver data from above paths
   - Creates: Gold analytics in S3 Tables format
   - Stores: Advanced metrics in Apache Iceberg format

## Troubleshooting

### No Silver Processing After Bronze
- Check S3 event notification on bronze bucket
- Verify Lambda permission for S3 to invoke silver-processing
- Look for errors in silver processing CloudWatch logs

### No Gold Processing After Silver  
- Check S3 event notification on silver bucket
- Verify Lambda permission for S3 to invoke gold-analytics
- Ensure silver data matches expected path patterns

### Common Issues

1. **Path Pattern Mismatches**: Gold analytics now supports both:
   - `silver/{file_type}/season=YYYY-YY/date=YYYY-MM-DD/file`
   - `silver/{file_type}/date=YYYY-MM-DD/file` (current output)

2. **S3 Event Filters**: 
   - Bronze → Silver: Filters for `raw/box_scores/date=` prefix and `/data.json` suffix
   - Silver → Gold: Filters for `silver/` prefix and `.json` suffix

3. **IAM Permissions**: Ensure Lambda execution roles have proper S3 access

## Manual Cleanup

If testing generates unwanted data:

```bash
# Clean bronze test data
aws s3 rm s3://hoopstat-haus-bronze/raw/box_scores/date=2024-01-15/ --recursive

# Clean silver test data  
aws s3 rm s3://hoopstat-haus-silver/silver/ --recursive

# Clean gold test data
aws s3 rm s3://hoopstat-haus-gold/ --recursive
```

## Validation Checklist

- [ ] Bronze ingestion runs successfully
- [ ] Silver processing triggered automatically by bronze S3 event
- [ ] Gold analytics triggered automatically by silver S3 event  
- [ ] All CloudWatch logs show successful execution
- [ ] Data appears in each S3 layer as expected
- [ ] Error handling works (check with invalid data)
- [ ] Daily automation works via local cron (if configured)