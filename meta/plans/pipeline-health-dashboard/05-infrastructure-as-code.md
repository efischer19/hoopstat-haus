# Ticket 5: Infrastructure as Code — Aggregator Lambda & CloudFront Config

**Title:** `feat: Terraform IaC for health aggregator Lambda and CloudFront cache behavior`

**Labels:** `enhancement`

---

## What do you want to build?

Add Terraform infrastructure for the health aggregator Lambda function and configure CloudFront to serve the `pipeline_health.json` artifact with appropriate caching behavior. This ticket provisions all AWS resources needed to run the aggregator in production.

### Resources to Provision

#### 1. Health Aggregator Lambda Function

A new Lambda function alongside the existing Silver and Gold Lambdas:

- **Name:** `hoopstat-haus-health-aggregator`
- **Runtime:** Container image (ECR), consistent with existing Lambda deployment pattern
- **Trigger:** S3 event notification on Gold bucket — fires when `served/index/latest.json` is created/updated (indicates Gold processing completed)
- **Timeout:** 60 seconds (CloudWatch Logs Insights queries can take 10-20 seconds)
- **Memory:** 256 MB (minimal; primarily I/O bound)
- **Environment Variables:** `LOG_LEVEL`, `APP_NAME`, `GOLD_BUCKET`, `BRONZE_BUCKET`, `LOG_GROUP_NAME`

#### 2. IAM Role & Policy (Least Privilege)

A dedicated IAM role with **strictly read-only** permissions:

- **CloudWatch Logs:** `logs:StartQuery`, `logs:GetQueryResults` on `/hoopstat-haus/data-pipeline` log group only
- **S3 Read (Bronze):** `s3:ListBucket` on `hoopstat-haus-bronze` with prefix condition `quarantine/` only
- **S3 Read (Gold):** `s3:GetObject` on `hoopstat-haus-gold` for `served/index/latest.json` only
- **S3 Write (Gold):** `s3:PutObject` on `hoopstat-haus-gold` for `served/health/*` prefix only
- **CloudWatch Logs Write:** Standard Lambda execution logging permissions

The role must NOT have:
- Write access to Bronze or Silver buckets
- Permissions to any other log groups
- Permissions to modify IAM, Lambda, or any other service

#### 3. CloudFront Cache Behavior for `/health/*`

Add an ordered cache behavior for the `health/*` path pattern:

- **Path Pattern:** `health/*`
- **TTL:** 1 hour (`max-age=3600`), consistent with frontend asset caching (ADR-038)
- **Response Headers Policy:** Use the existing `frontend_app` response headers policy (1-hour cache, CORS)
- **Viewer Protocol Policy:** `redirect-to-https`
- **Allowed Methods:** `GET`, `HEAD` only

#### 4. S3 Event Notification

Configure S3 event notification on the Gold bucket to trigger the health aggregator Lambda when `served/index/latest.json` is written. This chains the health aggregator to the Gold pipeline's completion.

---

## Acceptance Criteria

- [ ] A new Lambda function resource (`aws_lambda_function.health_aggregator`) is added to `infrastructure/main.tf`
- [ ] A dedicated IAM role with least-privilege permissions is created for the health aggregator
- [ ] IAM policy restricts CloudWatch Logs access to the `/hoopstat-haus/data-pipeline` log group only
- [ ] IAM policy restricts S3 read access to `quarantine/` prefix on Bronze and `served/index/latest.json` on Gold
- [ ] IAM policy restricts S3 write access to `served/health/*` prefix on Gold only
- [ ] An S3 event notification triggers the Lambda when `served/index/latest.json` is created/updated in the Gold bucket
- [ ] A CloudFront ordered cache behavior for `health/*` is added with 1-hour TTL
- [ ] `terraform plan` runs cleanly with no errors against the updated configuration
- [ ] All new resources include appropriate tags (`Project`, `Component`, `ManagedBy`)
- [ ] Lambda configuration variables (timeout, memory) use the existing `var.lambda_config` pattern for consistency

---

## Implementation Notes (Optional)

- Follow the existing Lambda infrastructure patterns in `infrastructure/main.tf` (lines ~1393-1622) for the Silver and Gold Lambdas. The health aggregator follows the same ECR image deployment pattern.
- The CloudFront cache behavior for `health/*` should be inserted as a new `ordered_cache_behavior` block, positioned after the `index/*` behavior and before the `*.html` behavior in the distribution config.
- The S3 event notification must use a `filter_prefix` of `served/index/` and `filter_suffix` of `latest.json` to avoid triggering on unrelated writes.
- The IAM role should be a separate resource (not shared with the existing `lambda_execution` role) to enforce the principle of least privilege per ADR-011.
- The Gold S3 bucket policy already grants CloudFront OAC read access to `served/*`, so `served/health/pipeline_health.json` is automatically accessible through CloudFront with no additional bucket policy changes.
- **Dependency on Tickets 2 and 3:** The Lambda code must be built and pushed to ECR before the Lambda function can be created. However, the Terraform can be written and planned before the image exists by using a placeholder `image_uri` (consistent with existing `lifecycle { ignore_changes = [image_uri] }` pattern).
- Reference the `reusable-build-push.yml` workflow for the Docker image build/push pattern that will be used for the new Lambda in Ticket 6.
