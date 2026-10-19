# feat: Bronze fetches each box score once per game, not once per team

## What do you want to build?

`LeagueGameFinder` returns one row **per team** per game, so a 15-game night yields 30 schedule rows. `DateScopedIngestion.run()` (`apps/bronze-ingestion/app/ingestion.py`) loops over those rows and fetches the box score for every row, which means two identical `BoxScoreTraditionalV3` calls per game. The writes are idempotent (keyed by game ID), but we double our request volume against stats.nba.com, the endpoint that silently blocked us for seven months. The summary/log counts also report 30 "games" for a 15-game night.

Deduplicate game IDs before fetching box scores, and report real game counts.

## Acceptance Criteria

- [ ] Box scores are fetched once per unique `GAME_ID`, preserving first-seen order
- [ ] The stored schedule JSON is unchanged (still one row per team; silver may rely on it)
- [ ] Logs, `_log_ingestion_summary` and `update_bronze_summary` report the unique game count (e.g. 15, not 30, for 2025-04-13)
- [ ] Unit test: two schedule rows sharing a `GAME_ID` produce exactly one `get_box_score` call
- [ ] Real dry-run for `2025-04-13` reports 15 games and 15 box scores
- [ ] Bronze tests pass and ruff is clean

## Implementation Notes (Optional)

- Check `_validate_ingestion_completeness` and the bronze summary's success-rate math (`successful_box_scores / games_count`) so they use the same unique-game denominator; otherwise the success rate would read 50%.
- Leave `filter_excluded_game_types` (from #963) applied before deduplication.
- Merging rebuilds the armv7 image (~2.5h). Don't merge within ~3h of the Pi's 4:30am ET run.
