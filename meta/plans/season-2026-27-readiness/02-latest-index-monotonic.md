# feat: Never move served/index/latest.json backwards

## What do you want to build?

`JSONArtifactWriter.write_latest_index()` (`apps/gold-analytics/app/json_artifacts.py`) unconditionally overwrites `served/index/latest.json` with whatever date gold just processed. Any replay, retry or backfill of an older date, or several dates processed concurrently by S3-triggered Lambdas, repoints the public index (and everything keyed off it: the health aggregator, Build Database, MCP clients) at stale data.

Make the index monotonic: only advance `latest_date` when the processed date is newer than the current one.

## Acceptance Criteria

- [ ] `write_latest_index(d)` reads the existing `served/index/latest.json` (if any) and only writes when `d` is strictly newer than its `latest_date`, or when no index exists
- [ ] A missing or unparseable existing index is treated as "no index" (write), not as an error
- [ ] Unit tests cover: no existing index, newer date (writes), same date (no-op), older date (no-op), corrupt existing index (writes)
- [ ] Gold tests pass with an isolated AWS env, and ruff is clean

## Implementation Notes (Optional)

- A read-then-write race between two concurrent Lambdas is still possible. That's acceptable at our volume (daily runs are sequential); don't add locking. If it ever matters, S3 conditional writes (`If-Match` on the ETag) are the tool.
- Keep the `served/index/latest.json` key and JSON shape unchanged; db-compiler, `build-database.yml` and the MCP proxy read it.
- Prerequisite for the 2025-26 backfill (follow-up 09).
