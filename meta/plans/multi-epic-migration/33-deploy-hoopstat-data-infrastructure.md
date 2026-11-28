# feat: Deploy hoopstat-data infrastructure via Terraform

## What do you want to build?

Run `terraform apply` for the hoopstat-data repository's infrastructure, creating all AWS resources needed for the data pipeline. This is the first real deployment from the new repository.

## Acceptance Criteria

- [ ] `terraform init` succeeds with the new backend configuration
- [ ] `terraform plan` produces a clean plan with expected resources
- [ ] `terraform apply` completes successfully
- [ ] All S3 buckets are created and accessible
- [ ] All ECR repositories are created
- [ ] All Lambda functions are created (with placeholder code initially)
- [ ] All IAM roles and policies are correctly attached
- [ ] CloudWatch log groups are created
- [ ] EventBridge rules are created (but scheduling is disabled initially)
- [ ] `terraform output` shows all expected values
- [ ] The infrastructure workflow in CI can run `terraform plan` successfully

## Implementation Notes (Optional)

**State management decision:**
The old hoopstat-haus Terraform state manages existing AWS resources. Options for the new state:

1. **Fresh state, new resources:** Create entirely new AWS resources from hoopstat-data's Terraform. Old resources stay until teardown (Epic 8). This is the safest approach — no state migration needed, no risk of accidentally modifying live resources.

2. **Import existing resources:** Use `terraform import` to bring existing resources into the new state. Riskier but avoids creating duplicate resources.

**Recommended:** Option 1 (fresh state, new resources). This means during the migration window, there will be two sets of resources (old and new). The cost is minimal and temporary. Once the new pipeline is validated, the old resources are torn down.

**Deployment sequence:**
1. `terraform init` with new backend config
2. `terraform plan` — review carefully
3. `terraform apply` — create resources
4. Verify each resource type manually in the AWS Console
5. Run `terraform plan` again — should show no changes (idempotent)

**S3 bucket naming:**
New buckets need different names than old ones (S3 bucket names are globally unique). Use a naming convention like `hoopstat-data-{layer}-{suffix}` (e.g., `hoopstat-data-bronze-v1`).

**ECR repositories:**
New ECR repos are empty initially. They'll be populated when the Docker build/push workflow runs for the first time.

**Lambda functions:**
Created with a placeholder handler. The real code is deployed when the deploy workflow runs with actual Docker images.
