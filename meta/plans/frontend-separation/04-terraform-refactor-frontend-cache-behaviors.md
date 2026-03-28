# Ticket 04: Terraform — Refactor Frontend Cache Behaviors

**Title:** `feat: refactor CloudFront cache behaviors for post-separation architecture`

## What do you want to build?

Update the Terraform configuration in `infrastructure/main.tf` to reflect the post-separation architecture. Currently, the CloudFront distribution has cache behaviors for frontend app assets (`*.html`, `assets/*`, `scripts/*`) that use the `frontend_app` response headers policy. After separation, these behaviors need to be re-evaluated:

- **Frontend asset behaviors** (`*.html`, `assets/*`, `scripts/*`) remain but are now deployed by the new frontend repo. No Terraform changes needed for these paths — they still serve from the same S3 origin.
- **Health behavior** (`health/*`) remains and is now backend-owned.
- **The `frontend_app` response headers policy** stays as-is (it provides CORS + 1-hour cache, which is correct for both repos' files).

The main change is **documentation and comments** in the Terraform code to reflect that frontend files are now deployed from an external repository, and to update any variable descriptions or output names that reference "frontend" as if it's part of this repo.

## Acceptance Criteria

- [ ] CloudFront distribution continues to serve all existing paths correctly (no user-facing changes)
- [ ] Terraform comments/descriptions are updated to reflect that `*.html`, `assets/*`, and `scripts/*` cache behaviors serve files deployed by the external `hoopstat-haus-frontend` repo
- [ ] The `health/*` cache behavior is documented as backend-owned (deployed by this repo)
- [ ] The `frontend_app` response headers policy is renamed or re-documented to reflect its broader purpose (e.g., `static_assets` or keep the name but update the description)
- [ ] `terraform plan` shows no unexpected resource changes (comment/description changes may show as updates)
- [ ] If the OIDC IAM role needs scoping changes to allow the new repo to deploy, those changes are included (or deferred to Ticket 06 with a comment)
- [ ] CloudFront outputs (distribution ID, domain name) are documented as shared between repos

## Implementation Notes (Optional)

- **Key Terraform resources to review:**
  - `aws_cloudfront_distribution.gold_artifacts` — cache behaviors for `*.html`, `assets/*`, `scripts/*`, `health/*`
  - `aws_cloudfront_response_headers_policy.frontend_app` — consider renaming to `static_assets_cors` or similar
  - `aws_s3_bucket_policy.gold_cloudfront_read` — already scoped to `served/*`, no change needed
  - IAM role for GitHub Actions — may need to allow the new repo's OIDC identity

- **Do NOT remove any cache behaviors.** The paths are still valid — they're just deployed by a different repo now. The CloudFront distribution is the shared infrastructure that bridges both repos.

- If renaming the response headers policy causes a destroy/recreate (Terraform treats name changes as replacements for some resources), keep the existing name and update only the `description` field to avoid downtime.

- Consider adding a `# Deployed by: hoopstat-haus-frontend repo` comment block above the frontend-related cache behaviors for clarity.

- **Prerequisite:** This ticket depends on Ticket 03 (health dashboard decoupled). It can then progress in parallel with Ticket 02 (new repo creation) since it only changes comments/descriptions, not functional behavior.
