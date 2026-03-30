# feat: Optional AWS S3/CloudFront deployment path for static-js-app-blueprint

## What do you want to build?

Add an optional AWS deployment path to the `static-js-app-blueprint` template. This should be clearly documented and easy to enable, but disabled by default. When enabled, it deploys the static frontend to an S3 bucket and invalidates a CloudFront distribution.

## Acceptance Criteria

- [ ] `.github/workflows/deploy-aws.yml` exists but is disabled by default (uses `workflow_dispatch` only, or has an enable flag)
- [ ] The workflow performs: `aws s3 sync` to an S3 bucket, then `aws cloudfront create-invalidation`
- [ ] AWS credentials use GitHub OIDC (consistent with ADR-011 from hoopstat-haus), not static keys
- [ ] All AWS-specific values (bucket name, distribution ID, IAM role ARN) are configurable via GitHub repository variables or secrets
- [ ] README includes a clear "Opting into AWS Deployment" section with step-by-step instructions
- [ ] The README section documents required AWS resources (S3 bucket, CloudFront distribution, OIDC provider, IAM role) but explicitly states infrastructure provisioning is out of scope
- [ ] The GitHub Pages workflow (ticket 09) remains the default and is not affected
- [ ] Example GitHub repository variable names are documented (e.g., `AWS_ROLE_ARN`, `S3_BUCKET_NAME`, `CLOUDFRONT_DISTRIBUTION_ID`)

## Implementation Notes (Optional)

The issue explicitly states: "infrastructure is beyond the scope of this template repo." The workflow should assume the AWS resources already exist and just deploy to them. Document what resources are needed but don't create Terraform for them.

Adapt from hoopstat-haus's `deploy-frontend.yml` workflow:
- Keep the OIDC authentication pattern
- Keep the S3 sync and CloudFront invalidation steps
- Remove hoopstat-specific paths and bucket names
- Replace with configurable variables

Consider providing a toggle mechanism: either a repository variable `DEPLOY_TARGET` (values: `pages` or `aws`) that switches between the two deployment paths, or simply keep both workflows and let the user enable/disable as needed. The simpler approach (separate workflows) is probably better for a template.
