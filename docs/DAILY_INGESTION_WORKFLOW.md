# Daily Bronze Ingestion Workflow

This document describes the automated daily scheduling workflow for the bronze layer ingestion pipeline.

## Overview

The daily ingestion workflow (`daily-ingestion.yml`) automatically executes the bronze layer data ingestion at 4:30 AM ET daily. It coordinates with the Lambda deployment infrastructure to invoke the deployed bronze-ingestion function.

## Schedule

- **Automatic Execution**: Daily at 4:30 AM ET (9:30 AM UTC)
- **Winter (EST)**: 4:30 AM EST = 9:30 AM UTC ✅
- **Summer (EDT)**: 5:30 AM EDT = 9:30 AM UTC ✅

The fixed UTC schedule ensures consistent execution regardless of daylight saving time changes.

## Architecture

```
GitHub Actions (daily-ingestion.yml)
    ↓ (scheduled trigger)
AWS Lambda (hoopstat-haus-bronze-ingestion)
    ↓ (data processing)
S3 Bronze Layer (data storage)
    ↓ (monitoring)
CloudWatch Logs (execution logs)
```

## Manual Execution

The workflow can be manually triggered via GitHub Actions UI or CLI:

### Via GitHub UI
1. Go to **Actions** → **Daily Bronze Ingestion**
2. Click **Run workflow**
3. Configure parameters:
   - **Season**: NBA season (e.g., "2024-25")
   - **Dry Run**: Test mode without data changes
   - **Force Run**: Run even if no games scheduled

### Via GitHub CLI
```bash
# Basic execution
gh workflow run daily-ingestion.yml

# With custom parameters
gh workflow run daily-ingestion.yml \
  --field season="2024-25" \
  --field dry_run=true \
  --field force_run=false
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `season` | string | `2024-25` | NBA season to ingest |
| `dry_run` | boolean | `false` | Run without making changes |
| `force_run` | boolean | `false` | Force run even if no games scheduled |

## Coordination with Deployment

This workflow coordinates with the deployment infrastructure:

- **Requires**: Lambda function deployed via `deploy.yml` workflow
- **Uses**: Same AWS credentials and OIDC configuration
- **Invokes**: `hoopstat-haus-bronze-ingestion` Lambda function
- **Monitors**: CloudWatch logs at `/hoopstat-haus/data-pipeline`

## Execution Flow

1. **Checkout Code**: Get latest repository code
2. **AWS Authentication**: Configure OIDC credentials
3. **Function Check**: Verify Lambda function exists
4. **Payload Preparation**: Create invocation payload with parameters
5. **Lambda Invocation**: Trigger function asynchronously
6. **Status Monitoring**: Check execution logs
7. **Reporting**: Generate summary and notifications

## Monitoring

### Execution Status
- **GitHub**: Check workflow run status in Actions tab
- **Lambda**: Monitor function metrics in AWS console
- **Logs**: View execution logs in CloudWatch

### Key Metrics
- **Invocation Success**: Lambda function successfully triggered
- **Execution Duration**: Time to complete data processing
- **Error Rate**: Failed executions and error types
- **Data Quality**: Validation results and completeness

### Troubleshooting

#### Common Issues

**1. Lambda Function Not Found**
```
❌ Lambda function not found: hoopstat-haus-bronze-ingestion
```
**Solution**: Ensure the bronze-ingestion app is deployed via the deploy workflow.

**2. Permission Denied**
```
❌ Failed to invoke Lambda function
```
**Solution**: Check AWS credentials and IAM role permissions.

**3. Invocation Timeout**
```
⏳ Waiting for function execution to start...
```
**Solution**: Check Lambda function configuration and CloudWatch logs.

#### Debug Steps

1. **Check Deployment**: Verify Lambda function exists
   ```bash
   aws lambda get-function --function-name hoopstat-haus-bronze-ingestion
   ```

2. **Review Logs**: Check CloudWatch logs for errors
   ```bash
   aws logs tail /hoopstat-haus/data-pipeline --follow
   ```

3. **Test Manually**: Run workflow_dispatch to test configuration

## Security

- **Authentication**: Uses GitHub OIDC (no stored credentials)
- **Permissions**: Minimal IAM role with specific S3 and Lambda access
- **Secrets**: No secrets stored in repository
- **Audit**: All executions logged in CloudWatch

## Maintenance

### Seasonal Updates
- **Cron Schedule**: Fixed UTC time (no DST adjustments needed)
- **NBA Season**: Update default season parameter annually
- **Holiday Handling**: Manual force_run parameter for special cases

### Performance Optimization
- **Execution Time**: Monitor Lambda duration metrics
- **Cost Management**: Review execution frequency and resource usage
- **Error Handling**: Improve retry logic based on failure patterns

## Integration

This workflow integrates with:
- **Bronze Ingestion App**: Primary data processing application
- **Deploy Workflow**: Lambda function deployment
- **Infrastructure**: AWS Lambda, S3, CloudWatch
- **Monitoring**: CloudWatch alarms and metrics

## Future Enhancements

Potential improvements for the workflow:
- **Intelligent Scheduling**: Skip execution when no games scheduled
- **Retry Logic**: Automatic retry on transient failures
- **Notification Integration**: Email/Slack alerts for failures
- **Performance Monitoring**: Advanced metrics and alerting
- **Multi-Environment**: Support for dev/staging environments