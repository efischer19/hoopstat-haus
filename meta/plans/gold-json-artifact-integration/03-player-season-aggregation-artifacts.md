# feat: Design and implement player season aggregation JSON artifacts

## What do you want to build?

Design a JSON schema for player season aggregation artifacts and add a
`write_player_season_artifacts()` method to `JSONArtifactWriter`. Wire this
method into `_store_season_aggregations()` in `processors.py` so that season-level
player statistics are persisted to S3.

Unlike daily artifacts (which already have writer methods), season aggregation
artifacts do not yet have a defined format or writer implementation.

## Acceptance Criteria

- [ ] A JSON schema for player season aggregation artifacts is defined and documented
- [ ] `JSONArtifactWriter` has a `write_player_season_artifacts(aggregations, season)` method
- [ ] Artifacts are written to `served/season_player/{season}/{player_id}.json`
- [ ] Each artifact is ≤100 KB per ADR-028
- [ ] `_store_season_aggregations()` in `processors.py` calls the new writer method instead of logging a warning
- [ ] Dry-run mode is supported
- [ ] Season artifacts use 1-year immutable Cache-Control headers (per ADR-038)

## Implementation Notes (Optional)

**Key files:**
- `apps/gold-analytics/app/json_artifacts.py` — new `write_player_season_artifacts()` method
- `apps/gold-analytics/app/processors.py` — `_store_season_aggregations()`

**Schema design considerations:**
- The `aggregated_seasons` dict maps `player_id` → season stats (points, assists, rebounds, games played, averages, efficiency metrics)
- Consider aligning field names with the existing `GoldPlayerDailyStats` Pydantic model where applicable
- A season-level Pydantic model may be warranted for validation
- Include season identifier, player metadata (name, team), and aggregate statistics

**Depends on:** Ticket 01 (establishes `JSONArtifactWriter` integration pattern in processors)

**Relevant ADR:** ADR-028 (Gold Layer Architecture — ≤100 KB artifact limit, `served/` prefix)
