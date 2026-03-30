# feat: Provision new AWS OIDC tokens for hoopstat-data and hoopstat-app

## What do you want to build?

Create new GitHub OIDC IAM roles in AWS for the `hoopstat-data` and `hoopstat-app` repositories. Each role should have the minimum permissions needed for its repository's CI/CD workflows.

## Acceptance Criteria

- [ ] IAM OIDC identity provider is configured for GitHub Actions (or reuses the existing one)
- [ ] IAM role for `hoopstat-data` is created with trust policy scoped to `repo:efischer19/hoopstat-data:*`
- [ ] IAM role for `hoopstat-app` is created with trust policy scoped to `repo:efischer19/hoopstat-app:*`
- [ ] `hoopstat-data` role permissions include: S3 (read/write data buckets), ECR (push images), Lambda (update functions), CloudWatch (write logs/metrics), Terraform state S3 (read/write), DynamoDB lock table (if used)
- [ ] `hoopstat-app` role permissions include: S3 (write to frontend bucket), CloudFront (create invalidation)
- [ ] Both roles follow least-privilege principle — no `*` resource wildcards where avoidable
- [ ] Role ARNs are added as GitHub repository variables (`AWS_ROLE_ARN`) in their respective repos
- [ ] Both repos can successfully authenticate to AWS via OIDC in a test workflow
- [ ] Role configurations are documented (either in Terraform or markdown)

## Implementation Notes (Optional)

Reference hoopstat-haus's OIDC setup:
- `infrastructure/GITHUB_ACTIONS_ROLE.md` documents the current pattern
- ADR-011 (GitHub OIDC for AWS Authentication) describes the decision

Two approaches for creating the roles:
1. **Terraform in hoopstat-data:** Define both roles in hoopstat-data's Terraform config. This keeps infrastructure centralized but means hoopstat-app depends on hoopstat-data for IAM.
2. **Manual/CLI creation:** Create roles via AWS CLI or Console. Simpler for initial setup but less reproducible.

Recommended approach: Define both roles in hoopstat-data's Terraform (it already owns the infrastructure). Document the role ARNs and add them to both repos as variables.

**Permission boundaries:**

hoopstat-data role needs:
- `s3:GetObject`, `s3:PutObject`, `s3:ListBucket`, `s3:DeleteObject` on data buckets
- `ecr:GetAuthorizationToken`, `ecr:BatchCheckLayerAvailability`, `ecr:PutImage`, etc.
- `lambda:UpdateFunctionCode`, `lambda:UpdateFunctionConfiguration`
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
- Terraform state: `s3:GetObject`, `s3:PutObject` on state bucket; `dynamodb:GetItem`, `dynamodb:PutItem` on lock table

hoopstat-app role needs:
- `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket` on frontend bucket
- `cloudfront:CreateInvalidation` on the distribution

Test authentication by adding a simple workflow step:
```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ vars.AWS_ROLE_ARN }}
    aws-region: us-east-1
- run: aws sts get-caller-identity
```
