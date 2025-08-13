# ECR Permissions Fix Documentation

## Issue Description

The deployment workflow was failing with an ECR `AccessDeniedException` when trying to perform `ecr:DescribeImages` operation:

```
An error occurred (AccessDeniedException) when calling the DescribeImages operation: 
User: arn:aws:sts::***:assumed-role/hoopstat-haus-operations/GitHubActions-Deploy-*** 
is not authorized to perform: ecr:DescribeImages on resource: 
arn:aws:ecr:us-east-1:***:repository/hoopstat-haus/prod
```

## Root Cause

The `hoopstat-haus-operations` IAM role had `ecr:DescribeImages` permission but was missing the `ecr:DescribeRepositories` permission. While AWS documentation suggests that `ecr:DescribeImages` should be sufficient, in practice AWS CLI operations often require both permissions to work correctly.

## Solution

Added `ecr:DescribeRepositories` permission to the ECR policy for the `hoopstat-haus-operations` role in `infrastructure/main.tf`:

```hcl
Action = [
  "ecr:BatchCheckLayerAvailability",
  "ecr:GetDownloadUrlForLayer", 
  "ecr:BatchGetImage",
  "ecr:DescribeImages",
  "ecr:DescribeRepositories",  # <- Added this line
  "ecr:PutImage",
  "ecr:InitiateLayerUpload",
  "ecr:UploadLayerPart",
  "ecr:CompleteLayerUpload"
]
```

## Why This Fix Works

The `ecr:DescribeRepositories` permission allows the role to:
1. Verify that the ECR repository exists and is accessible
2. Retrieve repository metadata needed for subsequent operations
3. Enable the AWS CLI to properly execute `describe-images` commands

This is a common pattern in AWS where related permissions are often required together, even if the documentation suggests one permission should be sufficient.

## Testing

Use the provided test script to validate ECR permissions:

```bash
cd infrastructure/tests
./test_ecr_permissions.sh
```

## Related Workflows

This fix enables the following deployment workflow operations:
- **Verify image exists in ECR** (deploy.yml:149): Uses `aws ecr describe-images` to check if container images exist before deployment
- **ECR login and authentication**: Uses `aws ecr get-login-password` for authentication
- **Docker image pull**: Downloads container images from ECR for deployment

## Deployment

After applying this terraform change:
1. Run `terraform plan` to review the changes
2. Run `terraform apply` to update the IAM policy
3. Test the deployment workflow to verify the fix

The change is minimal and only adds the missing permission without modifying any existing permissions or resources.