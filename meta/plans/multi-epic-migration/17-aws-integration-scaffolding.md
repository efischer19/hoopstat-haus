# feat: AWS integration scaffolding for python-aws-data-blueprint

## What do you want to build?

Add AWS integration scaffolding to the `python-aws-data-blueprint` template: Terraform infrastructure files, Lambda-ready Docker configuration, ECR workflows, and S3 data access patterns.

## Acceptance Criteria

- [ ] `infrastructure/main.tf` exists with placeholder resources: S3 bucket, Lambda function, ECR repository, IAM roles
- [ ] `infrastructure/backend.tf` exists with S3 backend configuration (placeholder values)
- [ ] `infrastructure/variables.tf` exists with clearly documented variable definitions
- [ ] `infrastructure/outputs.tf` exists with useful output values
- [ ] `infrastructure/versions.tf` exists pinning AWS provider version
- [ ] `infrastructure/README.md` explains the infrastructure structure and how to customize
- [ ] `infrastructure/GITHUB_ACTIONS_ROLE.md` exists with generalized OIDC role setup guide (adapted from hoopstat-haus)
- [ ] `infrastructure/SETUP.md` exists with generalized Terraform setup guide (adapted from hoopstat-haus)
- [ ] `.github/workflows/infrastructure.yml` exists with Terraform plan (on PR) and apply (on merge) jobs
- [ ] `.github/workflows/deploy.yml` exists with ECR push and Lambda update jobs (using placeholder values)
- [ ] `.github/workflows/reusable-build-push.yml` exists as a reusable Docker build/push workflow (adapted from hoopstat-haus)
- [ ] Example app `Dockerfile` is updated to use Lambda-compatible base image (e.g., `public.ecr.aws/lambda/python:3.12`)
- [ ] `scripts/ecr-helper.sh` exists for local ECR operations (adapted from hoopstat-haus)
- [ ] All AWS resource identifiers use placeholder values (e.g., `123456789012` for account ID, `us-east-1` for region)
- [ ] OIDC role configuration is documented but uses placeholder ARNs

## Implementation Notes (Optional)

Adapt heavily from hoopstat-haus `infrastructure/` and `.github/workflows/`:

Terraform (`infrastructure/`):
- `main.tf` — Simplified version of hoopstat-haus, showing S3 + Lambda + ECR + IAM pattern. Remove hoopstat-specific resources (CloudFront, DynamoDB, CloudWatch dashboards). Keep the core pattern.
- Include comments explaining each resource block's purpose
- Use `var.project_name` extensively for naming

Workflows (`.github/workflows/`):
- `infrastructure.yml` — Adapt from hoopstat-haus, use OIDC auth
- `deploy.yml` — Adapt from hoopstat-haus, ECR build/push + Lambda update
- `reusable-build-push.yml` — Adapt from hoopstat-haus

Docker:
- Update example app Dockerfile to use Lambda base image
- Show the `ENTRYPOINT` and `CMD` for Lambda handler pattern

The key constraint from the issue: "The example definitely doesn't have to actually work here, it won't have credentials. But it should exist, just with placeholder values."
