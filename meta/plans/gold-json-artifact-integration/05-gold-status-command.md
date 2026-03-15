# feat: Implement gold layer status command with JSON artifact validation

## What do you want to build?

Replace the stub `status` command in `apps/gold-analytics/app/main.py` with a
real health check that validates the `served/` prefix structure and confirms
JSON artifacts exist and are well-formed.

The bronze layer already has a working `status_handler()` (in
`apps/bronze-ingestion/app/lambda_handler.py`) that can serve as a template
for this pattern.

## Acceptance Criteria

- [ ] `status` command connects to S3 and lists artifact types under the `served/` prefix
- [ ] Command reports the latest date for which artifacts exist
- [ ] Command validates that `served/index/latest.json` is present and parseable
- [ ] Command reports artifact counts per type (player_daily, team_daily, top_lists)
- [ ] Command exits with code 0 on success, code 1 on any validation failure
- [ ] The warning log about "Health check not yet implemented" is removed
- [ ] The "Planned: Check for served/ prefix structure" log message is removed

## Implementation Notes (Optional)

**Key files:**
- `apps/gold-analytics/app/main.py` — `status()` command

**Approach:**
1. Use `boto3` S3 client (or reuse `JSONArtifactWriter`'s client) to list objects under `served/`
2. Parse `served/index/latest.json` to determine the most recent processing date
3. Count artifacts per prefix (`served/player_daily/`, `served/team_daily/`, `served/top_lists/`)
4. Report findings via structured logging
5. Pattern after the bronze `status_handler()` for consistency

**Depends on:** Ticket 01 (artifacts must exist to validate)

**Relevant ADR:** ADR-028 (Gold Layer Architecture — `served/` prefix structure)
