# Ticket 06: Shared Domain and Cross-Repo Deployment Strategy

**Title:** `feat: establish cross-repo deployment strategy for shared CloudFront`

## What do you want to build?

Define and implement the mechanism by which the new `hoopstat-haus-frontend` repository deploys its files to the shared S3 bucket and CloudFront distribution managed by this repository's Terraform.

This is the critical coordination point between the two repos. The goal is to allow both repos to deploy independently without stepping on each other's files or requiring manual AWS console access.

### Key decisions to formalize

1. **IAM access:** How does the new repo authenticate to AWS?
2. **S3 path scoping:** How do we prevent one repo from overwriting the other's files?
3. **Cache invalidation:** How does the new repo invalidate CloudFront paths after deployment?
4. **Deployment ordering:** Are there any ordering constraints between the two repos' deployments?

## Acceptance Criteria

- [ ] The new `hoopstat-haus-frontend` repo can deploy files to S3 via its own GitHub Actions workflow
- [ ] The new repo's IAM permissions are scoped to only the S3 paths it owns (e.g., `served/index.html`, `served/assets/*`, `served/scripts/app.js`)
- [ ] This repo's IAM permissions are scoped to its own paths (e.g., `served/health/*`, `served/index/*`, `served/player_daily/*`, `served/team_daily/*`, `served/top_lists/*`, `served/db/*`, `served/scripts/health.js`, `served/health.html`)
- [ ] Both repos can independently create CloudFront cache invalidations
- [ ] A deployment from one repo does not overwrite, delete, or corrupt files from the other repo
- [ ] The shared access model is documented (in this repo's `infrastructure/README.md` or a new `CROSS_REPO_DEPLOYMENT.md`)
- [ ] The approach is tested by deploying from both repos and verifying all paths work

## Implementation Notes (Optional)

- **IAM approach (choose one):**

  1. **Shared OIDC role with path conditions:** Extend the existing `hoopstat-haus-github-actions` IAM role to also trust the new repo's GitHub OIDC identity. Use S3 bucket policy conditions or separate IAM policies to restrict each repo to its own paths.
     - *Pros:* Single role to manage; leverages existing OIDC setup (ADR-011).
     - *Cons:* More complex IAM policy; must be careful with `s3:DeleteObject` permissions.

  2. **Separate OIDC role for the new repo:** Create a second IAM role (e.g., `hoopstat-haus-frontend-github-actions`) with its own OIDC trust policy for the new repo. Grant it write access only to frontend paths in the S3 bucket.
     - *Pros:* Clean separation of permissions; easier to audit; independent rotation.
     - *Cons:* Another IAM role to manage in Terraform; the role definition lives in this repo's Terraform.

  - **Recommendation:** Separate OIDC role (Option 2). It's cleaner and follows the principle of least privilege. The Terraform for the new role lives in this repo since this repo owns the infrastructure.

- **S3 path scoping strategy:**
  - Frontend repo writes: `served/index.html`, `served/assets/*`, `served/scripts/app.js`
  - Backend repo writes: `served/health.html`, `served/scripts/health.js`, `served/health/*`, `served/index/*` (data index), `served/player_daily/*`, `served/team_daily/*`, `served/top_lists/*`, `served/db/*`
  - The `served/scripts/` prefix is shared (both `app.js` and `health.js` live there). Consider moving `health.js` to `served/health/health.js` (Ticket 03) to avoid shared prefix conflicts.

- **Cache invalidation:** Both repos need `cloudfront:CreateInvalidation` permission on the shared distribution. Each repo should only invalidate the paths it deploys (frontend: `/*.html`, `/assets/*`, `/scripts/app.js`; backend: `/health.html`, `/health/*`, `/scripts/health.js`).

- **Prerequisites:** This ticket depends on Ticket 02 (new repo exists) and Ticket 04 (Terraform comments updated). The IAM role creation can begin as soon as the new repo name is finalized.

- **No deployment ordering constraints:** The two repos deploy different files. As long as path scoping is correct, deployments can happen in any order, including simultaneously.

- **Testing:** After implementation, verify by:
  1. Deploying from the new repo → check `index.html` loads
  2. Deploying from this repo → check `health.html` loads
  3. Confirm no file from one repo was deleted by the other's `aws s3 sync`
  4. Confirm CloudFront serves all paths correctly
