# feat: Design and implement team season aggregation JSON artifacts

## What do you want to build?

Design a JSON schema for team season aggregation artifacts and add a
`write_team_season_artifacts()` method to `JSONArtifactWriter`. Wire this
method into `_store_team_season_aggregations()` in `processors.py` so that
season-level team statistics are persisted to S3.

This mirrors the player season aggregation work (ticket 03) but for team-level
data.

## Acceptance Criteria

- [ ] A JSON schema for team season aggregation artifacts is defined and documented
- [ ] `JSONArtifactWriter` has a `write_team_season_artifacts(aggregations, season)` method
- [ ] Artifacts are written to `served/season_team/{season}/{team_id}.json`
- [ ] Each artifact is ≤100 KB per ADR-028
- [ ] `_store_team_season_aggregations()` in `processors.py` calls the new writer method instead of logging a warning
- [ ] Dry-run mode is supported
- [ ] Season artifacts use 1-year immutable Cache-Control headers (per ADR-038)

## Implementation Notes (Optional)

**Key files:**
- `apps/gold-analytics/app/json_artifacts.py` — new `write_team_season_artifacts()` method
- `apps/gold-analytics/app/processors.py` — `_store_team_season_aggregations()`

**Schema design considerations:**
- The `aggregated_seasons` dict maps `team_id` → season stats (wins, losses, points for/against, team ratings, etc.)
- Consider aligning field names with the existing `GoldTeamDailyStats` Pydantic model where applicable
- A season-level Pydantic model may be warranted for validation
- Include season identifier, team metadata, and aggregate statistics

**Depends on:** Ticket 01 (establishes integration pattern), Ticket 03 (establishes season artifact conventions)

**Relevant ADR:** ADR-028 (Gold Layer Architecture — ≤100 KB artifact limit, `served/` prefix)
