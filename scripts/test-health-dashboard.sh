#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# test-health-dashboard.sh
#
# Convenience script that:
#   1. Runs the health-aggregator integration tests
#   2. Generates a mock pipeline_health.json
#   3. Serves the frontend locally
#
# Usage:
#   ./scripts/test-health-dashboard.sh          # run tests + serve dashboard (open in browser manually)
#   ./scripts/test-health-dashboard.sh --test   # run tests only
#   ./scripts/test-health-dashboard.sh --serve  # serve dashboard only (open in browser manually)
# ---------------------------------------------------------------------------

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGGREGATOR_DIR="$REPO_ROOT/apps/health-aggregator"
FRONTEND_DIR="$REPO_ROOT/frontend-app"
MOCK_HEALTH_DIR="$FRONTEND_DIR/health"
PORT=8080

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

# ---------------------------------------------------------------------------
# Run integration tests
# ---------------------------------------------------------------------------
run_tests() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " Running health-aggregator integration tests"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ ! -f "$AGGREGATOR_DIR/pyproject.toml" ]; then
        error "Cannot find $AGGREGATOR_DIR/pyproject.toml"
        exit 1
    fi

    cd "$AGGREGATOR_DIR"

    if ! command -v poetry &> /dev/null; then
        error "Poetry is not installed. Install it: pip install poetry"
        exit 1
    fi

    poetry install --quiet
    info "Dependencies installed"

    if poetry run pytest tests/integration/ -v; then
        info "All integration tests passed"
    else
        error "Integration tests failed"
        exit 1
    fi

    cd "$REPO_ROOT"
}

# ---------------------------------------------------------------------------
# Generate mock pipeline_health.json
# ---------------------------------------------------------------------------
generate_mock_data() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " Generating mock pipeline_health.json"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    mkdir -p "$MOCK_HEALTH_DIR"

    # Generate 7 days of mock data with today as most recent
    python3 -c "
import json
import datetime as dt

today = dt.date.today()
summaries = []
for i in range(7):
    d = today - dt.timedelta(days=i)
    summaries.append({
        'date': str(d),
        'bronze': {'status': 'success', 'records_ingested': 100 + i * 5},
        'silver': {
            'status': 'success',
            'records_processed': 95 + i * 3,
            'records_quarantined': 2 + i,
            'quality_score': round(0.95 - i * 0.01, 4),
        },
        'gold': {'status': 'success', 'artifacts_written': 10 + i},
    })

report = {
    'schema_version': '1.0.0',
    'generated_at': dt.datetime.now(dt.UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'overall_status': 'operational',
    'stages': {
        'bronze': {
            'status': 'operational',
            'last_success_at': dt.datetime.now(dt.UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
        },
        'silver': {
            'status': 'operational',
            'last_success_at': dt.datetime.now(dt.UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
        },
        'gold': {
            'status': 'operational',
            'last_success_at': dt.datetime.now(dt.UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
        },
    },
    'daily_summaries': summaries,
}

with open('$MOCK_HEALTH_DIR/pipeline_health.json', 'w') as f:
    json.dump(report, f, indent=2)
print('Mock data written to $MOCK_HEALTH_DIR/pipeline_health.json')
"
    info "Mock pipeline_health.json generated"
}

# ---------------------------------------------------------------------------
# Serve frontend
# ---------------------------------------------------------------------------
serve_dashboard() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " Serving health dashboard"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    info "Dashboard: http://localhost:$PORT/health.html"
    info "Press Ctrl+C to stop"
    echo ""

    cd "$FRONTEND_DIR"
    python3 -m http.server "$PORT"
}

# ---------------------------------------------------------------------------
# Cleanup mock data on exit
# ---------------------------------------------------------------------------
cleanup() {
    if [ -f "$MOCK_HEALTH_DIR/pipeline_health.json" ]; then
        rm -f "$MOCK_HEALTH_DIR/pipeline_health.json"
        # Attempt to remove the directory if it's empty; ignore failure if not empty
        rmdir "$MOCK_HEALTH_DIR" 2>/dev/null || true
        info "Cleaned up mock data"
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    echo "🏀 Hoopstat Haus — Health Dashboard Test Runner"

    case "${1:-all}" in
        --test)
            run_tests
            ;;
        --serve)
            generate_mock_data
            trap cleanup EXIT
            serve_dashboard
            ;;
        *)
            run_tests
            generate_mock_data
            trap cleanup EXIT
            serve_dashboard
            ;;
    esac
}

main "$@"
