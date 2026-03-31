# feat: Configure AWS S3/CloudFront deployment for hoopstat-app

## What do you want to build?

Configure the AWS deployment workflow in `hoopstat-app` to deploy the frontend to S3 and invalidate the CloudFront distribution. Set up the necessary GitHub repository secrets/variables and verify the workflow is ready for deployment.

## Acceptance Criteria

- [ ] `.github/workflows/deploy-aws.yml` is configured with hoopstat-app-specific values
- [ ] GitHub repository variables are documented: `AWS_ROLE_ARN`, `S3_BUCKET_NAME`, `CLOUDFRONT_DISTRIBUTION_ID`
- [ ] The workflow uses GitHub OIDC for AWS authentication (ADR-011 pattern)
- [ ] The S3 sync command targets the correct bucket path
- [ ] The CloudFront invalidation covers all necessary paths (`/*` or specific patterns)
- [ ] The workflow triggers on push to `main` and via manual `workflow_dispatch`
- [ ] A concurrency group prevents parallel deployments
- [ ] The workflow is syntactically valid (passes `actionlint` or similar)
- [ ] README documents the deployment process and required AWS setup

## Implementation Notes (Optional)

Adapt from hoopstat-haus's `.github/workflows/deploy-frontend.yml`:
- Keep the OIDC authentication pattern
- Update source path from `frontend-app/` to `src/`
- Use repository variables instead of hardcoded values
- Preserve the CloudFront invalidation step

The OIDC role for hoopstat-app needs different permissions than hoopstat-data:
- S3: PutObject, DeleteObject on the frontend bucket
- CloudFront: CreateInvalidation on the distribution
- No Lambda, ECR, or data bucket access needed

The actual AWS resources (S3 bucket, CloudFront distribution, OIDC provider) must exist before this workflow can run. Per the file-mapping, the CloudFront distribution and S3 buckets are managed by hoopstat-data's Terraform (ticket 22). The hoopstat-app deploy workflow references these resources via GitHub repository variables (`S3_BUCKET_NAME`, `CLOUDFRONT_DISTRIBUTION_ID`) whose values come from hoopstat-data's Terraform outputs.
