# feat: Migrate and adapt Terraform infrastructure to hoopstat-data

## What do you want to build?

Migrate the Terraform infrastructure from hoopstat-haus to hoopstat-data, adapting resource names and configurations for the new repository context. The infrastructure should define all AWS resources needed for the data pipeline.

## Acceptance Criteria

- [ ] `infrastructure/main.tf` contains all data pipeline infrastructure (adapted from hoopstat-haus):
  - S3 buckets (bronze, silver, gold layers)
  - Lambda functions for each pipeline stage
  - ECR repositories for each app's Docker image
  - IAM roles and policies (Lambda execution, S3 access, ECR pull)
  - CloudWatch log groups and alarms
  - EventBridge rules for scheduling
- [ ] `infrastructure/backend.tf` is updated with new state bucket name/key
- [ ] `infrastructure/variables.tf` is updated with hoopstat-data-specific variables
- [ ] `infrastructure/outputs.tf` is updated with relevant outputs
- [ ] `infrastructure/versions.tf` pins the same provider versions as hoopstat-haus
- [ ] `infrastructure/GITHUB_ACTIONS_ROLE.md` documents the new OIDC role requirements
- [ ] `infrastructure/README.md` is updated for the new repo context
- [ ] `terraform validate` passes (with `-backend=false`)
- [ ] CloudFront-related resources are NOT included (those belong in hoopstat-app or are shared infrastructure)
- [ ] No hardcoded values from the old hoopstat-haus infrastructure remain

## Implementation Notes (Optional)

The infrastructure migration is sensitive. Key considerations:

**What moves to hoopstat-data:**
- S3 bucket definitions (bronze, silver, gold data buckets)
- Lambda function definitions (bronze-ingestion, silver-processing, gold-analytics, health-aggregator, db-compiler)
- ECR repository definitions
- IAM roles for Lambda execution
- CloudWatch monitoring (log groups, alarms, dashboards)
- EventBridge scheduling rules
- State backend configuration (new bucket/key)

**What does NOT move to hoopstat-data:**
- CloudFront distribution (serves the frontend — goes to hoopstat-app or shared infra)
- Route53 records (shared infrastructure, managed separately)
- The gold/served S3 path's public access policy (this bridges data and app — needs careful handling)

**The gold layer public access question:**
The gold layer S3 bucket contains data that CloudFront serves to the frontend. This creates a dependency between hoopstat-data (writes the data) and hoopstat-app (serves it via CloudFront). Options:
1. hoopstat-data owns the S3 bucket, hoopstat-app references it via data source
2. Shared infrastructure module owns the bucket
3. hoopstat-data writes to a path that hoopstat-app's CloudFront is configured to read from

This should be documented as a decision in the file-mapping investigation (ticket 01) and may warrant its own ADR.

**State migration:**
The existing Terraform state will need to be migrated or the infrastructure re-created. Since we're keeping the old repo alive during migration (Epic 8 is last), we have time to handle this carefully. Consider:
- Fresh `terraform apply` with new state for hoopstat-data
- Import existing resources into new state if we want to avoid recreation
- The safest approach may be to create new resources alongside old ones, validate, then tear down old
