# Ticket 6: GitHub Actions Workflow for Health Aggregator

**Title:** `feat: GitHub Actions workflow for health aggregator deployment`

**Labels:** `enhancement`

---

## What do you want to build?

Create a GitHub Actions workflow to build, push, and deploy the health aggregator Lambda function. This workflow follows the existing deployment patterns used by the Silver and Gold Lambda functions, leveraging the reusable build-push workflow and OIDC authentication (ADR-011).

### Workflow Components

#### 1. CI Integration

Add the `apps/health-aggregator/` path to the existing CI workflow (`ci.yml`) so that changes to the aggregator trigger linting and testing:

- **Path filter:** `apps/health-aggregator/**`
- **Jobs:** `ruff format --check`, `ruff check`, `pytest`
- Follow the existing CI job patterns for other apps.

#### 2. Deployment Workflow

Create a new workflow (or extend the existing `deploy.yml`) to build and deploy the health aggregator:

- **Trigger:** Push to `main` with changes in `apps/health-aggregator/**`
- **Authentication:** GitHub OIDC with the existing IAM role (per ADR-011)
- **Steps:**
  1. Build Docker image using the reusable `reusable-build-push.yml` workflow
  2. Push image to ECR
  3. Update Lambda function image URI

#### 3. Manual Trigger (Optional)

Add a `workflow_dispatch` trigger to allow manual execution of the health aggregator for testing and debugging:

- Input: `dry_run` (boolean) — if true, generates the JSON but does not write to S3
- Useful for validating the aggregator output before the full infrastructure is live

---

## Acceptance Criteria

- [ ] The CI workflow (`ci.yml`) includes `apps/health-aggregator/**` in its path filters
- [ ] Linting (`ruff format --check`, `ruff check`) and testing (`pytest`) run for the health aggregator on PR and push
- [ ] A deployment workflow builds and pushes the health aggregator Docker image to ECR on merge to `main`
- [ ] The deployment workflow uses the existing `reusable-build-push.yml` pattern
- [ ] The deployment workflow uses GitHub OIDC authentication (per ADR-011)
- [ ] A `workflow_dispatch` trigger allows manual execution with a `dry_run` input parameter
- [ ] All workflow permissions follow the principle of least privilege (`id-token: write`, `contents: read`)
- [ ] The workflow passes on a clean run against `main` branch

---

## Implementation Notes (Optional)

- Follow the patterns in `.github/workflows/deploy.yml` and `.github/workflows/silver-processing.yml` for deployment and OIDC authentication conventions.
- The reusable workflow at `.github/workflows/reusable-build-push.yml` handles the Docker build and ECR push — the new workflow should call this reusable workflow with the `apps/health-aggregator` path.
- The CI workflow (`ci.yml`) uses a matrix strategy for multiple apps — add `health-aggregator` to the matrix if applicable, or add a new job following the existing pattern.
- The manual `workflow_dispatch` trigger should invoke the Lambda function directly using the AWS CLI (`aws lambda invoke`) after the image is deployed, rather than waiting for the S3 event trigger.
- **Dependency on Ticket 5:** The ECR repository and Lambda function must be provisioned via Terraform before the deployment workflow can push images. However, the workflow YAML can be written and validated before the infrastructure exists.
- The workflow does NOT need to handle the daily scheduled trigger — the Lambda is triggered by S3 events (configured in Ticket 5), so no `schedule` cron is needed in GitHub Actions.
