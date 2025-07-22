#!/bin/bash
# ECR Helper Script for Hoopstat Haus
# Provides common ECR operations for developers and operators

set -euo pipefail

# Configuration
ECR_REPOSITORY="hoopstat-haus/prod"
AWS_REGION="us-east-1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if AWS CLI is installed and configured
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS CLI is not configured or you don't have valid credentials."
        exit 1
    fi
    
    log_success "AWS CLI is configured"
}

# Login to ECR
ecr_login() {
    log_info "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION | \
        docker login --username AWS --password-stdin "$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com"
    log_success "Successfully logged in to ECR"
}

# List all images in the repository
list_images() {
    local app_filter=${1:-""}
    
    log_info "Listing images in ECR repository: $ECR_REPOSITORY"
    
    if [[ -n "$app_filter" ]]; then
        log_info "Filtering for application: $app_filter"
        aws ecr describe-images \
            --repository-name $ECR_REPOSITORY \
            --query "imageDetails[?starts_with(imageTags[0], '$app_filter-')].{Tags:imageTags,Pushed:imagePushedAt,Size:imageSizeInBytes}" \
            --output table
    else
        aws ecr describe-images \
            --repository-name $ECR_REPOSITORY \
            --query "imageDetails[].{Tags:imageTags,Pushed:imagePushedAt,Size:imageSizeInBytes}" \
            --output table
    fi
}

# Get the latest image for an application
get_latest_image() {
    local app_name=$1
    
    log_info "Getting latest image for: $app_name"
    
    local image_tag=$(aws ecr describe-images \
        --repository-name $ECR_REPOSITORY \
        --query "imageDetails[?contains(imageTags, '$app_name-latest')].imageTags[0]" \
        --output text)
    
    if [[ "$image_tag" != "None" && -n "$image_tag" ]]; then
        local registry=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com
        echo "$registry/$ECR_REPOSITORY:$image_tag"
        log_success "Latest image: $image_tag"
    else
        log_error "No latest image found for $app_name"
        return 1
    fi
}

# Pull an image locally
pull_image() {
    local app_name=$1
    local tag=${2:-"latest"}
    
    log_info "Pulling image: $app_name-$tag"
    
    # Login first
    ecr_login
    
    local registry=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com
    local full_image="$registry/$ECR_REPOSITORY:$app_name-$tag"
    
    if docker pull "$full_image"; then
        log_success "Successfully pulled: $full_image"
    else
        log_error "Failed to pull image. Check if the image exists."
        return 1
    fi
}

# Delete an image
delete_image() {
    local app_name=$1
    local tag=${2:-""}
    
    if [[ -z "$tag" ]]; then
        log_error "Please provide an image tag to delete"
        echo "Usage: $0 delete <app-name> <tag>"
        return 1
    fi
    
    log_warning "This will delete the image: $app_name-$tag"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deleting image: $app_name-$tag"
        aws ecr batch-delete-image \
            --repository-name $ECR_REPOSITORY \
            --image-ids imageTag="$app_name-$tag"
        log_success "Image deleted successfully"
    else
        log_info "Deletion cancelled"
    fi
}

# Show repository info
repo_info() {
    log_info "ECR Repository Information"
    echo "=========================="
    
    aws ecr describe-repositories \
        --repository-names $ECR_REPOSITORY \
        --query "repositories[0].{Name:repositoryName,URI:repositoryUri,CreatedAt:createdAt,ImageCount:~}" \
        --output table
    
    echo
    log_info "Repository Size"
    aws ecr describe-repositories \
        --repository-names $ECR_REPOSITORY \
        --query "repositories[0].imageScanningConfiguration" \
        --output table
}

# Show usage information
usage() {
    echo "ECR Helper Script for Hoopstat Haus"
    echo "====================================="
    echo
    echo "Usage: $0 <command> [arguments]"
    echo
    echo "Commands:"
    echo "  login                    - Login to ECR"
    echo "  list [app-name]         - List all images (optionally filter by app)"
    echo "  latest <app-name>       - Get latest image URL for an app"
    echo "  pull <app-name> [tag]   - Pull an image (default tag: latest)"
    echo "  delete <app-name> <tag> - Delete a specific image"
    echo "  info                    - Show repository information"
    echo "  help                    - Show this help message"
    echo
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 list example-calculator-app"
    echo "  $0 pull example-calculator-app"
    echo "  $0 pull example-calculator-app abc123def"
    echo "  $0 delete example-calculator-app old-tag"
}

# Main script logic
main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi
    
    # Check prerequisites
    check_aws_cli
    
    case $1 in
        login)
            ecr_login
            ;;
        list)
            list_images "${2:-}"
            ;;
        latest)
            if [[ $# -lt 2 ]]; then
                log_error "Please provide an application name"
                echo "Usage: $0 latest <app-name>"
                exit 1
            fi
            get_latest_image "$2"
            ;;
        pull)
            if [[ $# -lt 2 ]]; then
                log_error "Please provide an application name"
                echo "Usage: $0 pull <app-name> [tag]"
                exit 1
            fi
            pull_image "$2" "${3:-latest}"
            ;;
        delete)
            if [[ $# -lt 3 ]]; then
                log_error "Please provide application name and tag"
                echo "Usage: $0 delete <app-name> <tag>"
                exit 1
            fi
            delete_image "$2" "$3"
            ;;
        info)
            repo_info
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            log_error "Unknown command: $1"
            usage
            exit 1
            ;;
    esac
}

# Run the main function with all arguments
main "$@"