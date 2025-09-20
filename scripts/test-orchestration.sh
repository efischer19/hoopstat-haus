#!/bin/bash

# Test Daily Orchestration Pipeline
# Tests the complete Bronze → Silver → Gold cascade via S3 events and SQS queues

set -euo pipefail

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-hoopstat-haus}"
TEST_DATE="${1:-$(date -d 'yesterday' '+%Y-%m-%d')}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log with color
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed"
        exit 1
    fi
    
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        error "AWS credentials not configured"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Check infrastructure components
check_infrastructure() {
    log "Checking infrastructure components..."
    
    # Check SQS queues
    SILVER_QUEUE="${PROJECT_NAME}-silver-processing-queue"
    GOLD_QUEUE="${PROJECT_NAME}-gold-analytics-queue"
    
    if aws sqs get-queue-url --queue-name "$SILVER_QUEUE" --region "$AWS_REGION" > /dev/null 2>&1; then
        success "Silver processing SQS queue exists"
    else
        error "Silver processing SQS queue not found: $SILVER_QUEUE"
        return 1
    fi
    
    if aws sqs get-queue-url --queue-name "$GOLD_QUEUE" --region "$AWS_REGION" > /dev/null 2>&1; then
        success "Gold analytics SQS queue exists"
    else
        error "Gold analytics SQS queue not found: $GOLD_QUEUE"
        return 1
    fi
    
    # Check Lambda functions
    SILVER_FUNCTION="${PROJECT_NAME}-silver-processing"
    GOLD_FUNCTION="${PROJECT_NAME}-gold-analytics"
    
    if aws lambda get-function --function-name "$SILVER_FUNCTION" --region "$AWS_REGION" > /dev/null 2>&1; then
        success "Silver processing Lambda function exists"
    else
        error "Silver processing Lambda function not found: $SILVER_FUNCTION"
        return 1
    fi
    
    if aws lambda get-function --function-name "$GOLD_FUNCTION" --region "$AWS_REGION" > /dev/null 2>&1; then
        success "Gold analytics Lambda function exists"
    else
        error "Gold analytics Lambda function not found: $GOLD_FUNCTION"
        return 1
    fi
    
    success "Infrastructure check passed"
}

# Check SQS queue depths
check_queue_depths() {
    log "Checking SQS queue depths..."
    
    SILVER_QUEUE_URL=$(aws sqs get-queue-url --queue-name "${PROJECT_NAME}-silver-processing-queue" --region "$AWS_REGION" --output text --query 'QueueUrl')
    GOLD_QUEUE_URL=$(aws sqs get-queue-url --queue-name "${PROJECT_NAME}-gold-analytics-queue" --region "$AWS_REGION" --output text --query 'QueueUrl')
    
    SILVER_DEPTH=$(aws sqs get-queue-attributes --queue-url "$SILVER_QUEUE_URL" --attribute-names ApproximateNumberOfVisibleMessages --region "$AWS_REGION" --output text --query 'Attributes.ApproximateNumberOfVisibleMessages')
    GOLD_DEPTH=$(aws sqs get-queue-attributes --queue-url "$GOLD_QUEUE_URL" --attribute-names ApproximateNumberOfVisibleMessages --region "$AWS_REGION" --output text --query 'Attributes.ApproximateNumberOfVisibleMessages')
    
    log "Silver processing queue depth: $SILVER_DEPTH messages"
    log "Gold analytics queue depth: $GOLD_DEPTH messages"
    
    if [ "$SILVER_DEPTH" -gt 10 ] || [ "$GOLD_DEPTH" -gt 10 ]; then
        warning "High queue depths detected - processing may be backlogged"
    fi
}

# Test manual Lambda invocation
test_lambda_invocation() {
    log "Testing Lambda function invocations..."
    
    # Create test S3 event for silver processing
    SILVER_TEST_EVENT=$(cat <<EOF
{
  "Records": [
    {
      "eventSource": "aws:s3",
      "eventName": "ObjectCreated:Put",
      "s3": {
        "bucket": {
          "name": "${PROJECT_NAME}-bronze"
        },
        "object": {
          "key": "raw/box_scores/date=${TEST_DATE}/data.json"
        }
      }
    }
  ]
}
EOF
)
    
    # Create test S3 event for gold analytics
    GOLD_TEST_EVENT=$(cat <<EOF
{
  "Records": [
    {
      "eventSource": "aws:s3",
      "eventName": "ObjectCreated:Put",
      "s3": {
        "bucket": {
          "name": "${PROJECT_NAME}-silver"
        },
        "object": {
          "key": "silver/player_stats/season=2024-25/date=${TEST_DATE}/data.parquet"
        }
      }
    }
  ]
}
EOF
)
    
    log "Testing silver processing Lambda with test event..."
    SILVER_RESULT=$(aws lambda invoke \
        --function-name "${PROJECT_NAME}-silver-processing" \
        --payload "$SILVER_TEST_EVENT" \
        --region "$AWS_REGION" \
        --output text \
        /tmp/silver-response.json)
    
    if echo "$SILVER_RESULT" | grep -q "200"; then
        success "Silver processing Lambda test successful"
    else
        error "Silver processing Lambda test failed: $SILVER_RESULT"
        cat /tmp/silver-response.json
    fi
    
    log "Testing gold analytics Lambda with test event..."
    GOLD_RESULT=$(aws lambda invoke \
        --function-name "${PROJECT_NAME}-gold-analytics" \
        --payload "$GOLD_TEST_EVENT" \
        --region "$AWS_REGION" \
        --output text \
        /tmp/gold-response.json)
    
    if echo "$GOLD_RESULT" | grep -q "200"; then
        success "Gold analytics Lambda test successful"
    else
        error "Gold analytics Lambda test failed: $GOLD_RESULT"
        cat /tmp/gold-response.json
    fi
}

# Check recent CloudWatch logs
check_recent_logs() {
    log "Checking recent CloudWatch logs..."
    
    # Check for recent silver processing logs
    SILVER_LOG_GROUP="/aws/lambda/${PROJECT_NAME}-silver-processing"
    GOLD_LOG_GROUP="/aws/lambda/${PROJECT_NAME}-gold-analytics"
    
    START_TIME=$(($(date +%s) - 3600))000  # 1 hour ago in milliseconds
    
    log "Recent silver processing logs:"
    aws logs filter-log-events \
        --log-group-name "$SILVER_LOG_GROUP" \
        --start-time "$START_TIME" \
        --region "$AWS_REGION" \
        --query 'events[0:5].message' \
        --output table 2>/dev/null || warning "No recent silver processing logs found"
    
    log "Recent gold analytics logs:"
    aws logs filter-log-events \
        --log-group-name "$GOLD_LOG_GROUP" \
        --start-time "$START_TIME" \
        --region "$AWS_REGION" \
        --query 'events[0:5].message' \
        --output table 2>/dev/null || warning "No recent gold analytics logs found"
}

# Main execution
main() {
    log "🏀 Testing Daily Orchestration Pipeline"
    log "Target date: $TEST_DATE"
    log "AWS Region: $AWS_REGION"
    log "Project: $PROJECT_NAME"
    echo ""
    
    check_prerequisites
    echo ""
    
    check_infrastructure
    echo ""
    
    check_queue_depths
    echo ""
    
    test_lambda_invocation
    echo ""
    
    check_recent_logs
    echo ""
    
    success "🎉 Daily orchestration pipeline test completed!"
    echo ""
    log "📋 Next steps:"
    log "1. Check CloudWatch alarms for any issues"
    log "2. Monitor SQS queue depths during processing"
    log "3. Verify data appears in S3 silver and gold layers"
    log "4. Run the bronze ingestion script: apps/bronze-ingestion/setup-local.sh"
}

# Handle script arguments
case "${1:-test}" in
    "check")
        check_prerequisites
        check_infrastructure
        ;;
    "queues")
        check_queue_depths
        ;;
    "logs")
        check_recent_logs
        ;;
    "lambdas")
        test_lambda_invocation
        ;;
    *)
        main
        ;;
esac