# feat: Wire top lists and latest index generation into Gold processor

## What do you want to build?

After daily player and team artifacts are written (ticket 01), generate the
top-lists and latest-index JSON artifacts that downstream consumers (frontend,
MCP proxy) depend on.

`JSONArtifactWriter` already implements `write_top_lists()` and
`write_latest_index()`. This ticket calls those methods at the end of
`GoldProcessor.process_date()`.

## Acceptance Criteria

- [ ] `process_date()` calls `write_top_lists(player_analytics, target_date)` after storing player/team analytics
- [ ] `process_date()` calls `write_latest_index(target_date)` as the final step of a successful run
- [ ] Top-list artifacts are written to `served/top_lists/{date}/{metric}.json`
- [ ] Latest index is written to `served/index/latest.json`
- [ ] Dry-run mode skips both calls and logs intent
- [ ] Existing tests continue to pass

## Implementation Notes (Optional)

**Key files:**
- `apps/gold-analytics/app/processors.py` — `GoldProcessor.process_date()`
- `apps/gold-analytics/app/json_artifacts.py` — `write_top_lists()`, `write_latest_index()`

**Approach:**
1. At the end of the successful path in `process_date()`, after `_store_player_analytics` and `_store_team_analytics`, call `self.artifact_writer.write_top_lists(player_analytics, target_date)` and then `self.artifact_writer.write_latest_index(target_date)`
2. Ensure these are inside the `not dry_run` guard
3. The latest index must be written _last_ so consumers only discover a date when all its artifacts are ready

**Depends on:** Ticket 01 (daily artifact writing)

**Relevant ADR:** ADR-028 (Gold Layer Architecture), ADR-038 (CloudFront Cache Tuning — 5-min index TTL)
