# feat: Migrate and adapt Terraform infrastructure to hoopstat-data

## What do you want to build?

Migrate the Terraform infrastructure from hoopstat-haus to hoopstat-data, adapting resource names and configurations for the new repository context. The infrastructure should define all AWS resources needed for the data pipeline.

## Acceptance Criteria

- [ ] `infrastructure/main.tf` contains all infrastructure from hoopstat-haus (copy as-is per file-mapping):
  - S3 buckets (bronze, silver, gold layers)
  - Lambda functions for each pipeline stage
  - ECR repositories for each app's Docker image
  - IAM roles and policies (Lambda execution, S3 access, ECR pull)
  - CloudWatch log groups and alarms
  - EventBridge rules for scheduling
  - CloudFront distribution and Origin Access Control (serves gold layer data and frontend)
- [ ] `infrastructure/backend.tf` is updated with new state bucket name/key
- [ ] `infrastructure/variables.tf` is updated with hoopstat-data-specific variables
- [ ] `infrastructure/outputs.tf` is updated with relevant outputs
- [ ] `infrastructure/versions.tf` pins the same provider versions as hoopstat-haus
- [ ] All infrastructure documentation is migrated: GITHUB_ACTIONS_ROLE.md, LAMBDA_DEPLOYMENT.md, PUBLIC_ACCESS_GUIDE.md, observability_README.md, SETUP.md
- [ ] `infrastructure/README.md` is updated for the new repo context
- [ ] `infrastructure/tests/` are migrated
- [ ] `terraform validate` passes (with `-backend=false`)
- [ ] No hardcoded values from the old hoopstat-haus infrastructure remain

## Implementation Notes (Optional)

The infrastructure migration is sensitive. Key considerations:

**What moves to hoopstat-data:**
Per the file-mapping, ALL `infrastructure/` content copies as-is to hoopstat-data:
- S3 bucket definitions (bronze, silver, gold data buckets)
- Lambda function definitions (bronze-ingestion, silver-processing, gold-analytics, health-aggregator, db-compiler)
- ECR repository definitions
- IAM roles for Lambda execution
- CloudWatch monitoring (log groups, alarms, dashboards)
- EventBridge scheduling rules
- CloudFront distribution and Origin Access Control (serves both gold data and frontend)
- State backend configuration (new bucket/key)
- All documentation (GITHUB_ACTIONS_ROLE.md, LAMBDA_DEPLOYMENT.md, PUBLIC_ACCESS_GUIDE.md, SETUP.md, observability_README.md)
- Infrastructure tests

**CloudFront ownership:**
The file-mapping places CloudFront in hoopstat-data because the distribution serves the gold layer data. The hoopstat-app repo only pushes frontend files to S3 — the CloudFront distribution itself is managed as data infrastructure. This means hoopstat-app's deploy workflow needs to reference the CloudFront distribution ID from hoopstat-data's infrastructure outputs.

**The gold layer public access question:**
The gold layer S3 bucket contains data that CloudFront serves to the frontend. Since both the distribution and the bucket live in hoopstat-data's Terraform, hoopstat-app's deploy workflow just needs the distribution ID and S3 bucket name as configuration inputs. This simplifies the cross-repo dependency.

**State migration:**
The existing Terraform state will need to be migrated or the infrastructure re-created. Since we're keeping the old repo alive during migration (Epic 8 is last), we have time to handle this carefully. Consider:
- Fresh `terraform apply` with new state for hoopstat-data
- Import existing resources into new state if we want to avoid recreation
- The safest approach may be to create new resources alongside old ones, validate, then tear down old
