# feat: Wire daily JSON artifact writing into Gold processor pipeline

## What do you want to build?

Connect the existing `JSONArtifactWriter` to the `GoldProcessor` pipeline so
that player and team daily analytics are persisted as JSON artifacts under the
`served/` prefix in S3 instead of logging warnings.

The writer module (`apps/gold-analytics/app/json_artifacts.py`) already
implements `write_player_daily_artifacts()` and `write_team_daily_artifacts()`.
This ticket wires those methods into `_store_player_analytics` and
`_store_team_analytics` in `processors.py`.

## Acceptance Criteria

- [ ] `GoldProcessor.__init__` instantiates a `JSONArtifactWriter` using the `gold_bucket` parameter
- [ ] `_store_player_analytics` calls `write_player_daily_artifacts(analytics, target_date)` instead of logging a warning
- [ ] `_store_team_analytics` calls `write_team_daily_artifacts(analytics, target_date)` instead of logging a warning
- [ ] Dry-run mode skips artifact writing and logs what would have been written
- [ ] Existing unit tests continue to pass
- [ ] All linting and formatting checks pass (`ruff format`, `ruff check`)

## Implementation Notes (Optional)

**Key files:**
- `apps/gold-analytics/app/processors.py` — `GoldProcessor.__init__`, `_store_player_analytics`, `_store_team_analytics`
- `apps/gold-analytics/app/json_artifacts.py` — `JSONArtifactWriter`

**Approach:**
1. Import `JSONArtifactWriter` in `processors.py`
2. In `GoldProcessor.__init__`, add `self.artifact_writer = JSONArtifactWriter(gold_bucket=self.gold_bucket)`
3. Replace the warning logs in `_store_player_analytics` with `self.artifact_writer.write_player_daily_artifacts(analytics, target_date)`
4. Replace the warning logs in `_store_team_analytics` with `self.artifact_writer.write_team_daily_artifacts(analytics, target_date)`
5. Guard writes behind `dry_run` flag — the flag is available in `process_date()` but not currently passed to the storage methods, so threading it through may be needed

**Relevant ADR:** ADR-028 (Gold Layer Architecture)
