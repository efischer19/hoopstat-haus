#!/bin/bash

# Feature Request Issue Creation Script
# This script creates GitHub issues from extracted feature requests in JSON format
# Usage: ./create-feature-issues.sh [--dry-run] [--category CATEGORY] [--priority PRIORITY]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
JSON_FILE="$REPO_ROOT/meta/plans/extracted-feature-requests.json"
LOG_FILE="$REPO_ROOT/logs/issue-creation-$(date +%Y%m%d_%H%M%S).log"

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
DRY_RUN=false
CATEGORY_FILTER=""
PRIORITY_FILTER=""
VERBOSE=false

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}" | tee -a "$LOG_FILE"
}

# Function to print usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Create GitHub issues from extracted feature requests JSON file.

OPTIONS:
    --dry-run              Preview issues without creating them
    --category CATEGORY    Filter by feature category (frontend, etl-pipeline, mcp-server, etc.)
    --priority PRIORITY    Filter by priority (high, medium, low)
    --verbose              Enable verbose output
    --help                 Show this help message

EXAMPLES:
    $0 --dry-run                                    # Preview all issues
    $0 --category frontend --priority high          # Create only high-priority frontend issues
    $0 --dry-run --category etl-pipeline           # Preview ETL pipeline issues

ENVIRONMENT VARIABLES:
    GITHUB_TOKEN    GitHub personal access token (required if not using gh auth)

REQUIREMENTS:
    - GitHub CLI (gh) must be installed and authenticated
    - jq must be installed for JSON processing
    - Valid GitHub repository access

EOF
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if gh CLI is installed
    if ! command -v gh &> /dev/null; then
        print_status "$RED" "ERROR: GitHub CLI (gh) is not installed. Please install it first."
        print_status "$BLUE" "Installation: https://cli.github.com/"
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        print_status "$RED" "ERROR: jq is not installed. Please install it first."
        print_status "$BLUE" "Installation: https://stedolan.github.io/jq/download/"
        exit 1
    fi
    
    # Check if JSON file exists
    if [[ ! -f "$JSON_FILE" ]]; then
        print_status "$RED" "ERROR: JSON file not found at $JSON_FILE"
        exit 1
    fi
    
    # Check GitHub authentication
    if ! gh auth status &> /dev/null; then
        print_status "$RED" "ERROR: GitHub CLI is not authenticated."
        print_status "$BLUE" "Run: gh auth login"
        exit 1
    fi
    
    # Validate JSON file
    if ! jq empty "$JSON_FILE" &> /dev/null; then
        print_status "$RED" "ERROR: Invalid JSON in $JSON_FILE"
        exit 1
    fi
    
    print_status "$GREEN" "All prerequisites met."
}

# Function to filter features based on criteria
filter_features() {
    local jq_filter=".feature_requests[]"
    
    if [[ -n "$CATEGORY_FILTER" ]]; then
        jq_filter="$jq_filter | select(.category == \"$CATEGORY_FILTER\")"
    fi
    
    if [[ -n "$PRIORITY_FILTER" ]]; then
        jq_filter="$jq_filter | select(.priority == \"$PRIORITY_FILTER\")"
    fi
    
    echo "$jq_filter"
}

# Function to check if issue already exists
issue_exists() {
    local title="$1"
    
    # Search for existing issues with similar title
    if gh issue list --search "in:title \"$title\"" --json title,number --jq '.[] | select(.title == "'"$title"'") | .number' | grep -q .; then
        return 0
    else
        return 1
    fi
}

# Function to format issue body
format_issue_body() {
    local feature="$1"
    
    cat << EOF
## Description
$(echo "$feature" | jq -r '.description')

## Acceptance Criteria
$(echo "$feature" | jq -r '.acceptance_criteria[] | "- [ ] " + .')

$(if echo "$feature" | jq -e '.technical_requirements | length > 0' > /dev/null; then
    echo "## Technical Requirements"
    echo "$feature" | jq -r '.technical_requirements[] | "- " + .'
    echo ""
fi)

$(if echo "$feature" | jq -e '.definition_of_done | length > 0' > /dev/null; then
    echo "## Definition of Done"
    echo "$feature" | jq -r '.definition_of_done[] | "- " + .'
    echo ""
fi)

## Source Information
- **Epic:** $(echo "$feature" | jq -r '.epic')
- **Category:** $(echo "$feature" | jq -r '.category')
- **Priority:** $(echo "$feature" | jq -r '.priority')
- **Complexity:** $(echo "$feature" | jq -r '.complexity')
- **Estimated Effort:** $(echo "$feature" | jq -r '.estimated_effort')
- **Source Document:** $(echo "$feature" | jq -r '.source_document')
- **Source Section:** $(echo "$feature" | jq -r '.source_section')

## Metadata
- **Feature ID:** $(echo "$feature" | jq -r '.id')
- **Generated from planning documents on:** $(date '+%Y-%m-%d %H:%M:%S UTC')
EOF
}

# Function to create a single issue
create_issue() {
    local feature="$1"
    local title
    local body
    local labels
    local issue_number
    
    title=$(echo "$feature" | jq -r '.title')
    body=$(format_issue_body "$feature")
    labels=$(echo "$feature" | jq -r '.github_labels | join(",")')
    
    if [[ "$DRY_RUN" == true ]]; then
        print_status "$YELLOW" "DRY RUN: Would create issue: $title"
        if [[ "$VERBOSE" == true ]]; then
            echo "Labels: $labels"
            echo "Body preview:"
            echo "$body" | head -20
            echo "..."
            echo ""
        fi
        return 0
    fi
    
    # Check if issue already exists
    if issue_exists "$title"; then
        print_status "$YELLOW" "SKIPPED: Issue already exists: $title"
        return 0
    fi
    
    # Create the issue
    print_status "$BLUE" "Creating issue: $title"
    
    if issue_number=$(gh issue create \
        --title "$title" \
        --body "$body" \
        --label "$labels" \
        2>&1); then
        
        print_status "$GREEN" "SUCCESS: Created issue #$issue_number - $title"
        return 0
    else
        print_status "$RED" "ERROR: Failed to create issue: $title"
        log "Error details: $issue_number"
        return 1
    fi
}

# Function to process all features
process_features() {
    local filter
    local features_json
    local total_count
    local success_count=0
    local skip_count=0
    local error_count=0
    
    filter=$(filter_features)
    features_json=$(jq -c "$filter" "$JSON_FILE")
    total_count=$(echo "$features_json" | wc -l)
    
    if [[ $total_count -eq 0 ]]; then
        print_status "$YELLOW" "No features match the specified criteria."
        return 0
    fi
    
    print_status "$BLUE" "Processing $total_count feature requests..."
    echo ""
    
    while IFS= read -r feature; do
        local title
        title=$(echo "$feature" | jq -r '.title')
        
        if create_issue "$feature"; then
            ((success_count++))
        else
            if issue_exists "$title"; then
                ((skip_count++))
            else
                ((error_count++))
            fi
        fi
        
        # Rate limiting - GitHub API allows 5000 requests per hour
        # Add a small delay to be respectful
        sleep 1
        
    done <<< "$features_json"
    
    echo ""
    print_status "$GREEN" "Processing complete!"
    print_status "$BLUE" "Summary:"
    echo "  Total features processed: $total_count"
    echo "  Successfully created: $success_count"
    echo "  Skipped (already exist): $skip_count"
    echo "  Errors: $error_count"
    
    if [[ $error_count -gt 0 ]]; then
        print_status "$RED" "Some issues failed to create. Check the log file: $LOG_FILE"
        return 1
    fi
    
    return 0
}

# Function to show preview summary
show_preview() {
    local filter
    local features_json
    local categories
    local priorities
    
    filter=$(filter_features)
    features_json=$(jq -c "$filter" "$JSON_FILE")
    
    echo ""
    print_status "$BLUE" "Preview Summary"
    echo "==============="
    
    echo "Total features to process: $(echo "$features_json" | wc -l)"
    echo ""
    
    echo "By Category:"
    categories=$(echo "$features_json" | jq -r '.category' | sort | uniq -c | sort -nr)
    echo "$categories"
    echo ""
    
    echo "By Priority:"
    priorities=$(echo "$features_json" | jq -r '.priority' | sort | uniq -c | sort -nr)
    echo "$priorities"
    echo ""
    
    if [[ "$VERBOSE" == true ]]; then
        echo "Feature List:"
        echo "$features_json" | jq -r '"\(.id): \(.title)"' | nl
        echo ""
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --category)
            CATEGORY_FILTER="$2"
            shift 2
            ;;
        --priority)
            PRIORITY_FILTER="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            print_status "$RED" "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    log "Starting feature request issue creation script"
    log "Options: DRY_RUN=$DRY_RUN, CATEGORY_FILTER=$CATEGORY_FILTER, PRIORITY_FILTER=$PRIORITY_FILTER"
    
    check_prerequisites
    
    if [[ "$DRY_RUN" == true ]]; then
        show_preview
    fi
    
    # Confirm before proceeding (unless dry run)
    if [[ "$DRY_RUN" == false ]]; then
        echo ""
        read -p "Do you want to proceed with creating these issues? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "$YELLOW" "Operation cancelled by user."
            exit 0
        fi
    fi
    
    process_features
    
    log "Script completed"
}

# Run main function
main "$@"