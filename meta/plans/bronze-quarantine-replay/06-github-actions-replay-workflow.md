# Ticket 06: GitHub Actions Workflow for Manual Replay

## What do you want to build?

Create a GitHub Actions workflow that wraps the quarantine replay CLI, allowing operators to trigger replays via `workflow_dispatch` without needing to run scripts locally. This is the CI/CD integration piece of the epic.

The workflow should support the same options as the CLI (single file, batch by classification, batch by date, dry-run) and surface the replay results in the GitHub Actions run summary.

## Acceptance Criteria

- [ ] A new workflow file `.github/workflows/quarantine-replay.yml` is created with `workflow_dispatch` trigger.
- [ ] The workflow accepts the following inputs:
  - `mode` (required, choice): `single`, `by-classification`, `by-date`
  - `s3_key` (optional, string): S3 key of a specific quarantine record (required when `mode=single`)
  - `classification` (optional, choice): `transient`, `rounding_mismatch`, `schema_change`, `data_quality`, `unknown` (required when `mode=by-classification`)
  - `date` (optional, string): Target date in `YYYY-MM-DD` format (required when `mode=by-date`)
  - `dry_run` (optional, boolean, default: true): Perform a dry run without writing to S3
  - `force` (optional, boolean, default: false): Force replay of already-resolved records
- [ ] The workflow uses GitHub OIDC to authenticate with AWS (per ADR-011), assuming the same IAM role used by the Silver processing workflow.
- [ ] The workflow runs the replay CLI command with the provided inputs and captures the output.
- [ ] The workflow writes a summary to `$GITHUB_STEP_SUMMARY` showing: number of files processed, success/failure counts, and any error details.
- [ ] The workflow defaults to `dry_run: true` as a safety measure -- operators must explicitly opt in to write operations.
- [ ] The workflow includes input validation (e.g., `s3_key` is required for `single` mode) and fails fast with a clear error message for invalid input combinations.
- [ ] The workflow is documented in the bronze-ingestion README with usage examples.

## Implementation Notes (Optional)

**Workflow structure (following existing patterns):**

Reference `silver-processing.yml` for the established workflow patterns in this repo (OIDC auth, Docker/Poetry setup, input validation).

```yaml
name: Quarantine Replay
on:
  workflow_dispatch:
    inputs:
      mode:
        description: "Replay mode"
        required: true
        type: choice
        options:
          - single
          - by-classification
          - by-date
      # ... additional inputs
```

**Authentication:**
- Use the same OIDC role as `silver-processing.yml` (requires read/write access to both bronze and silver S3 buckets)
- If the existing role doesn't have bronze read access, update the IAM policy in Terraform (keep the change minimal)

**Execution approach:**
- The workflow should install the bronze-ingestion app via Poetry, then invoke the CLI directly
- Alternatively, if the app is Dockerized, use the Docker image for consistency
- Follow whichever pattern `silver-processing.yml` uses

**Safety measures:**
- Default `dry_run: true` prevents accidental data writes
- Require explicit `force: true` for re-replaying resolved records
- Log all inputs at the start of the workflow for audit trail

**Limitations:**
- The workflow runs in GitHub's hosted runners, which have network access to AWS but not to the NBA API (which blocks cloud IPs per the deprecated `daily-ingestion.yml`). This is fine because replay does not call the NBA API -- it reads from S3.

**Future enhancements (out of scope for this ticket):**
- Slack/Teams notification on replay completion
- Scheduled workflow to auto-replay transient errors after a configurable delay
- Integration with a quarantine dashboard
