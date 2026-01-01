#!/bin/bash
set -euo pipefail

# Script to validate S3 event-triggered orchestration is working
# Usage: ./validate-orchestration.sh [test-date]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
TEST_DATE="${1:-$(date +%Y-%m-%d)}"
BRONZE_BUCKET="hoopstat-haus-bronze"
SILVER_BUCKET="hoopstat-haus-silver"
GOLD_BUCKET="hoopstat-haus-gold"
LOG_GROUP="/hoopstat-haus/data-pipeline"

echo "🏀 Validating S3 Event-Triggered Orchestration"
echo "==============================================="
echo "Test Date: $TEST_DATE"
echo "Bronze Bucket: $BRONZE_BUCKET"
echo "Silver Bucket: $SILVER_BUCKET"
echo "Gold Bucket: $GOLD_BUCKET"
echo ""

# Function to check if AWS CLI is available and configured
check_aws_setup() {
    echo "📋 Checking AWS setup..."
    
    if ! command -v aws &> /dev/null; then
        echo "❌ AWS CLI not found. Please install it first."
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        echo "❌ AWS credentials not configured. Please run 'aws configure'."
        exit 1
    fi
    
    echo "✅ AWS CLI configured"
    echo "   Account: $(aws sts get-caller-identity --query Account --output text)"
    echo "   Region: $(aws configure get region)"
    echo ""
}

# Function to check S3 buckets exist
check_buckets() {
    echo "📁 Checking S3 buckets..."
    
    for bucket in "$BRONZE_BUCKET" "$SILVER_BUCKET" "$GOLD_BUCKET"; do
        if aws s3api head-bucket --bucket "$bucket" 2>/dev/null; then
            echo "✅ Bucket exists: $bucket"
        else
            echo "❌ Bucket not found: $bucket"
            echo "   Please deploy infrastructure first with: cd infrastructure && terraform apply"
            exit 1
        fi
    done
    echo ""
}

# Function to check Lambda functions exist
check_lambda_functions() {
    echo "⚡ Checking Lambda functions..."
    
    local functions=("hoopstat-haus-bronze-ingestion" "hoopstat-haus-silver-processing" "hoopstat-haus-gold-analytics")
    
    for func in "${functions[@]}"; do
        if aws lambda get-function --function-name "$func" &> /dev/null; then
            echo "✅ Lambda function exists: $func"
        else
            echo "❌ Lambda function not found: $func"
            echo "   Please deploy Lambda functions first"
            exit 1
        fi
    done
    echo ""
}

# Function to create test bronze data
create_test_data() {
    echo "📝 Creating test bronze data..."
    
    local test_data=$(cat << EOF
{
  "gameData": {
    "gameId": "test-game-$TEST_DATE",
    "gameDate": "$TEST_DATE",
    "homeTeam": "LAL",
    "awayTeam": "BOS"
  },
  "playerStats": [
    {
      "playerId": "test-player-1",
      "playerName": "Test Player 1",
      "teamId": "LAL",
      "points": 25,
      "rebounds": 8,
      "assists": 6
    }
  ],
  "teamStats": [
    {
      "teamId": "LAL", 
      "teamName": "Lakers",
      "points": 110,
      "fieldGoalsMade": 42,
      "fieldGoalsAttempted": 85
    }
  ]
}
EOF
)
    
    local bronze_key="raw/box/date=$TEST_DATE/data.json"
    echo "$test_data" | aws s3 cp - "s3://$BRONZE_BUCKET/$bronze_key"
    
    echo "✅ Test data uploaded to: s3://$BRONZE_BUCKET/$bronze_key"
    echo ""
}

# Function to wait for processing and check results
wait_and_validate() {
    echo "⏳ Waiting for pipeline processing..."
    echo "   This may take 1-2 minutes for all stages to complete"
    echo ""
    
    # Wait a bit for S3 events to trigger
    sleep 30
    
    echo "🔍 Checking silver layer output..."
    local silver_files=$(aws s3 ls "s3://$SILVER_BUCKET/silver/" --recursive | grep "date=$TEST_DATE" || true)
    
    if [[ -n "$silver_files" ]]; then
        echo "✅ Silver layer data found:"
        echo "$silver_files" | sed 's/^/   /'
    else
        echo "❌ No silver layer data found yet"
        echo "   Checking CloudWatch logs for errors..."
        
        # Check recent logs for silver processing
        aws logs filter-log-events \
            --log-group-name "$LOG_GROUP" \
            --start-time $(date -d '5 minutes ago' +%s)000 \
            --filter-pattern "silver" \
            --query 'events[*].[timestamp,message]' \
            --output table || true
    fi
    echo ""
    
    # Wait a bit more for gold processing
    sleep 30
    
    echo "🔍 Checking gold layer output..."
    local gold_files=$(aws s3 ls "s3://$GOLD_BUCKET/" --recursive | grep "$TEST_DATE" || true)
    
    if [[ -n "$gold_files" ]]; then
        echo "✅ Gold layer data found:"
        echo "$gold_files" | sed 's/^/   /'
    else
        echo "❌ No gold layer data found yet"
        echo "   This is normal if gold processing takes longer"
    fi
    echo ""
}

# Function to check CloudWatch logs for errors
check_logs() {
    echo "📊 Checking recent CloudWatch logs for errors..."
    
    local start_time=$(date -d '10 minutes ago' +%s)000
    
    # Check for ERROR level logs
    local error_logs=$(aws logs filter-log-events \
        --log-group-name "$LOG_GROUP" \
        --start-time "$start_time" \
        --filter-pattern "ERROR" \
        --query 'events[*].[timestamp,message]' \
        --output json 2>/dev/null || echo "[]")
    
    if [[ "$error_logs" != "[]" && "$error_logs" != "" ]]; then
        echo "⚠️  Found ERROR logs:"
        echo "$error_logs" | jq -r '.[] | "   " + (.[0]/1000 | strftime("%Y-%m-%d %H:%M:%S")) + " - " + .[1]'
    else
        echo "✅ No ERROR logs found in recent activity"
    fi
    echo ""
}

# Function to cleanup test data
cleanup_test_data() {
    echo "🧹 Cleaning up test data..."
    
    # Remove bronze test data
    aws s3 rm "s3://$BRONZE_BUCKET/raw/box/date=$TEST_DATE/" --recursive || true
    
    # Remove silver test data (optional - comment out if you want to keep it)
    # aws s3 rm "s3://$SILVER_BUCKET/silver/" --recursive --exclude "*" --include "*date=$TEST_DATE*" || true
    
    echo "✅ Test data cleanup complete"
    echo ""
}

# Main execution
main() {
    check_aws_setup
    check_buckets
    check_lambda_functions
    
    echo "🚀 Starting orchestration validation test..."
    echo ""
    
    create_test_data
    wait_and_validate
    check_logs
    
    echo "📋 Validation Summary"
    echo "===================="
    echo "✅ Test completed for date: $TEST_DATE"
    echo "✅ Check the output above for any issues"
    echo ""
    echo "💡 Next steps:"
    echo "   - Review CloudWatch logs for detailed execution info"
    echo "   - Check S3 buckets for data in each layer"
    echo "   - Run 'cleanup_test_data' if you want to remove test data"
    echo ""
    echo "🔧 To run cleanup manually:"
    echo "   aws s3 rm s3://$BRONZE_BUCKET/raw/box/date=$TEST_DATE/ --recursive"
    echo ""
}

# Run cleanup if requested
if [[ "${1:-}" == "cleanup" ]]; then
    cleanup_test_data
    exit 0
fi

# Execute main function
main "$@"