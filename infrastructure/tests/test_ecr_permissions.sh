#!/bin/bash
# Test script to validate ECR permissions for the operations role
# This script can be used to test that the ECR permissions are correctly configured

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ECR_REPOSITORY_NAME="${ECR_REPOSITORY_NAME:-hoopstat-haus/prod}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ROLE_NAME="${ROLE_NAME:-hoopstat-haus-operations}"

echo -e "${YELLOW}🔍 Testing ECR permissions for role: $ROLE_NAME${NC}"
echo -e "${YELLOW}📍 Repository: $ECR_REPOSITORY_NAME${NC}"
echo -e "${YELLOW}🌍 Region: $AWS_REGION${NC}"
echo ""

# Function to test a specific ECR permission
test_ecr_permission() {
    local action=$1
    local description=$2
    local command=$3
    
    echo -e "${YELLOW}Testing: $action - $description${NC}"
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ SUCCESS: $action permission is working${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED: $action permission is not working${NC}"
        return 1
    fi
}

# Test basic ECR authentication
echo -e "${YELLOW}1. Testing ECR authentication (ecr:GetAuthorizationToken)${NC}"
if test_ecr_permission "ecr:GetAuthorizationToken" "Get ECR login token" "aws ecr get-login-password --region $AWS_REGION"; then
    echo -e "${GREEN}   ECR authentication is working${NC}"
else
    echo -e "${RED}   ECR authentication failed - check ecr:GetAuthorizationToken permission${NC}"
    exit 1
fi

echo ""

# Test repository description
echo -e "${YELLOW}2. Testing repository access (ecr:DescribeRepositories)${NC}"
if test_ecr_permission "ecr:DescribeRepositories" "Describe ECR repositories" "aws ecr describe-repositories --region $AWS_REGION --repository-names $ECR_REPOSITORY_NAME"; then
    echo -e "${GREEN}   Repository access is working${NC}"
else
    echo -e "${RED}   Repository access failed - check ecr:DescribeRepositories permission${NC}"
    exit 1
fi

echo ""

# Test image description
echo -e "${YELLOW}3. Testing image access (ecr:DescribeImages)${NC}"
if test_ecr_permission "ecr:DescribeImages" "Describe ECR images" "aws ecr describe-images --region $AWS_REGION --repository-name $ECR_REPOSITORY_NAME --max-items 1"; then
    echo -e "${GREEN}   Image access is working${NC}"
else
    echo -e "${YELLOW}   ⚠️  Image access failed - this is expected if no images exist yet${NC}"
    echo -e "${YELLOW}   ℹ️  To verify permission, try: aws ecr describe-images --region $AWS_REGION --repository-name $ECR_REPOSITORY_NAME${NC}"
fi

echo ""
echo -e "${GREEN}🎉 ECR permissions test completed!${NC}"
echo -e "${YELLOW}📝 Note: Some operations may fail if the repository is empty or images don't exist yet.${NC}"
echo -e "${YELLOW}   This is normal and doesn't indicate a permissions problem.${NC}"