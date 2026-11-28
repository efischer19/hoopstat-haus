# feat: Tear down AWS infrastructure and disable scheduled workflows

## What do you want to build?

Tear down the AWS infrastructure managed by the hoopstat-haus repository and disable all scheduled GitHub Actions workflows. This removes the operational footprint of the old repository.

## Acceptance Criteria

- [ ] All scheduled workflows are disabled (daily-ingestion cron, silver-processing, health-aggregator, etc.)
- [ ] The `workflow_dispatch` trigger is removed from deployment workflows to prevent accidental runs
- [ ] `terraform destroy` is run successfully against the hoopstat-haus infrastructure state
- [ ] All Lambda functions created by hoopstat-haus are deleted
- [ ] All ECR repositories created by hoopstat-haus are deleted (after confirming images are not referenced by new repos)
- [ ] CloudWatch log groups, alarms, and dashboards are removed
- [ ] EventBridge rules are removed
- [ ] S3 data buckets are evaluated: keep if hoopstat-data references them, delete if new buckets are provisioned
- [ ] The Terraform state bucket itself is cleaned up or retained as needed
- [ ] A summary of what was destroyed is documented in a PR description

## Implementation Notes (Optional)

**CRITICAL DEPENDENCY:** This ticket must NOT be started until Epic 9 (Integration & Deployment) is fully validated and the new hoopstat.haus v1 is confirmed working. The old infrastructure serves as a fallback during migration.

**S3 data bucket handling:**
The most sensitive part of teardown is the S3 data. Options:
1. **If hoopstat-data creates NEW buckets:** The old buckets can be deleted after verifying the new pipeline has populated the new buckets with equivalent data.
2. **If hoopstat-data references the SAME buckets:** The buckets should NOT be destroyed — only the Terraform state ownership transfers. Use `terraform state rm` to remove them from the old state without deleting the resources.

**Teardown sequence:**
1. Disable all scheduled workflows (immediate — prevents new pipeline runs)
2. Wait for any in-progress pipeline runs to complete
3. Run `terraform destroy` for non-data resources (Lambdas, ECR, CloudWatch, EventBridge)
4. Handle S3 buckets per the decision above
5. Handle CloudFront distribution (may be shared with hoopstat-app)
6. Clean up Terraform state backend

**CloudFront distribution:**
The existing CloudFront distribution serves both the frontend and the gold data. Depending on how Epic 9 handles this:
- If a new distribution is created: destroy the old one
- If the existing distribution is transferred: remove from old Terraform state, import to new
