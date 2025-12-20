#!/bin/bash

# Bronze Ingestion Local Setup Script
# Sets up Docker-based local execution for bronze-ingestion
# 
# Usage: ./setup-local.sh [target_directory]
# Example: ./setup-local.sh /home/user/bronze-cron

set -euo pipefail

# Configuration
TARGET_DIR="${1:-$HOME/bronze-ingestion-local}"
LOG_DIR="$TARGET_DIR/logs"

echo "🏀 Setting up local bronze-ingestion Docker execution..."
echo "📁 Target directory: $TARGET_DIR"

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install AWS CLI first."
    exit 1
fi

# Verify AWS credentials
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

# Create target directory and log directory
mkdir -p "$TARGET_DIR"
mkdir -p "$LOG_DIR"
echo "📁 Created directories: $TARGET_DIR, $LOG_DIR"

# Get ECR URI and image reference (defaults align with Terraform)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com"
# Allow overrides; defaults to hoopstat-haus/prod:bronze-ingestion-latest
ECR_REPO="${ECR_REPOSITORY:-${PROJECT_NAME:-hoopstat-haus}/${ENVIRONMENT:-prod}}"
IMAGE_TAG="${IMAGE_TAG:-bronze-ingestion-latest}"
IMAGE_URI="$ECR_URI/$ECR_REPO:$IMAGE_TAG"

# Configure ECR access
echo "🔐 Configuring ECR access..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "$ECR_URI"

# Create the daily runner script in target directory
echo "📝 Creating daily runner script..."
cat > "$TARGET_DIR/run-daily.sh" << 'EOF'
#!/bin/bash

set -euo pipefail

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/bronze-ingestion-$(date +%Y%m%d).log"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Runtime configuration with sensible defaults
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
AWS_REGION="${AWS_REGION:-$AWS_DEFAULT_REGION}"
BRONZE_BUCKET="${BRONZE_BUCKET:-hoopstat-haus-bronze}"
ECR_REPO="${ECR_REPOSITORY:-${PROJECT_NAME:-hoopstat-haus}/${ENVIRONMENT:-prod}}"
IMAGE_TAG="${IMAGE_TAG:-bronze-ingestion-latest}"
IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🏀 Starting bronze-ingestion daily execution..."

# Validate prerequisites
if ! docker info > /dev/null 2>&1; then
    log "❌ Docker is not running. Please start Docker first."
    exit 1
fi

if ! aws sts get-caller-identity > /dev/null 2>&1; then
    log "❌ AWS credentials not properly configured."
    exit 1
fi

# Parse optional arguments: --date YYYY-MM-DD and --dry-run
RUN_DATE=""
EXTRA_ARGS=()
while [[ ${#} -gt 0 ]]; do
    case "$1" in
        --date)
            if [[ ${#} -lt 2 ]]; then
                log "❌ Missing value for --date"
                exit 2
            fi
            RUN_DATE="$2"; shift 2 ;;
        --dry-run)
            EXTRA_ARGS+=(--dry-run); shift ;;
        *)
            log "❌ Unknown argument: $1"
            exit 2 ;;
    esac
done

# Ensure ECR login (handles token expiry)
if ! aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com" >/dev/null 2>&1; then
    log "⚠️  Unable to login to ECR; attempting pull with existing credentials"
fi

# Pull latest image (in case there's a newer version)
log "📥 Pulling latest bronze-ingestion image..."
if ! docker pull "$IMAGE_URI" 2>&1 | tee -a "$LOG_FILE"; then
    log "⚠️  Failed to pull latest image, using cached version"
fi

# Compute yesterday's date in a cross-platform way
if YESTERDAY=$(date -d 'yesterday' '+%Y-%m-%d' 2>/dev/null); then
    :
elif YESTERDAY=$(date -v -1d '+%Y-%m-%d' 2>/dev/null); then
    :
else
    YESTERDAY=$(python3 - <<'PY'
from datetime import date, timedelta
print((date.today() - timedelta(days=1)).isoformat())
PY
    )
fi

# Decide which date to ingest
if [[ -z "${RUN_DATE}" ]]; then
    RUN_DATE="${YESTERDAY}"
fi

# Execute bronze ingestion for the selected date
log "🚀 Executing bronze-ingestion container for ${RUN_DATE}'s games..."
EXIT_CODE=0
docker run --rm \
    --name bronze-ingestion-daily \
    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
    -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
    -e AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION}" \
    -e AWS_REGION="${AWS_REGION}" \
    -e AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN:-}" \
    -e BRONZE_BUCKET="${BRONZE_BUCKET}" \
    --entrypoint python \
    "$IMAGE_URI" \
    -m app.main ingest --date "${RUN_DATE}" ${EXTRA_ARGS[@]:-} 2>&1 | tee -a "$LOG_FILE" || EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log "✅ Bronze ingestion completed successfully"
else
    log "❌ Bronze ingestion failed with exit code $EXIT_CODE"
    exit $EXIT_CODE
fi

log "📊 Daily bronze ingestion process complete"
EOF

# Make runner script executable
chmod +x "$TARGET_DIR/run-daily.sh"

# Test pull the image
echo "📥 Pulling latest bronze-ingestion image..."
docker pull "$IMAGE_URI"

# Test execution (dry run style check)
echo "🧪 Testing container execution (quick validation)..."
if docker run --rm \
    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
    -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
    -e AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}" \
    -e AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}" \
    -e BRONZE_BUCKET="${BRONZE_BUCKET:-hoopstat-haus-bronze}" \
    -e AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN:-}" \
    --entrypoint python \
    "$IMAGE_URI" \
    -m app.main --help > /dev/null 2>&1; then
    echo "✅ Container execution test passed"
else
    echo "❌ Container execution test failed"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Test manual execution:"
echo "   cd $TARGET_DIR && ./run-daily.sh"
echo "   # with a specific date:"
echo "   cd $TARGET_DIR && ./run-daily.sh --date \\$(date +%F) --dry-run"
echo ""
echo "2. Add to crontab (runs daily at 4:30 AM ET):"
echo "   ( crontab -l 2>/dev/null; echo 'CRON_TZ=America/New_York'; echo '30 4 * * * BRONZE_BUCKET=${BRONZE_BUCKET:-hoopstat-haus-bronze} AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1} $TARGET_DIR/run-daily.sh >> $TARGET_DIR/cron.log 2>&1' ) | crontab -"
echo ""
echo "3. View logs:"
echo "   tail -f $TARGET_DIR/logs/bronze-ingestion-\$(date +%Y%m%d).log"
echo "   # Cron output goes to system default location"
echo ""
echo "🏀 Bronze ingestion is ready for daily execution!"
