# feat: Daily build generates season summaries and runs after the pipeline

## What do you want to build?

Two gaps in the daily "Build Database" job (`.github/workflows/build-database.yml`):

1. **Season summaries are never generated automatically.** Player and team season aggregates (`served/season_player/{season}/`, `served/season_team/{season}/`) are only written by gold's CLI (`season-players` / `season-teams` in `apps/gold-analytics/app/main.py`); the daily Lambda path never calls them. db-compiler's `player_season_summary` / `team_season_summary` tables will be empty or stale all season.
2. **It runs before the data exists.** The job's cron is `0 6 * * *` (06:00 UTC), but the Pi's bronze run is 4:30am ET (08:30 UTC) and silver/gold finish shortly after. Each night's games reach the database only ~22h later.

Add a step that runs gold season aggregation for the current season before compiling, and move the schedule to after the pipeline finishes.

## Acceptance Criteria

- [ ] Before compiling, the workflow runs gold `season-players` and `season-teams` for the current season (derived from today's date: Oct–Jun → `YYYY-YY`; override via a dispatch input)
- [ ] Season aggregation runs in GitHub Actions (OIDC credentials), **not** in the gold Lambda, so its whole-season read isn't bound by the 5-minute Lambda timeout
- [ ] Cron moves to after the pipeline (e.g. `0 11 * * *`, 7am ET), with a comment explaining the dependency on the Pi's 4:30am ET run
- [ ] With no games yet in the current season (e.g. a run before Oct 21), the job still succeeds and skips cleanly
- [ ] After ticket 01's replay data exists, a dispatched run produces non-empty season summary tables in the DuckDB file (2025-26)
- [ ] Season totals contain only regular-season (`002`) games (relies on #963)

## Implementation Notes (Optional)

- The CLI commands already exist (`season-players --season`, `season-teams --season`); check their exact flags and whether they need `GOLD_BUCKET` / `SILVER_BUCKET` env.
- `_load_season_*_games` reads every silver date in the season window, so runtime grows through the season. Log the duration so growth is visible.
- Job permissions: the OIDC role used by `build-database.yml` needs silver read and gold write for `served/season_*`; check the IAM policy in `infrastructure/main.tf` and extend it if needed (infrastructure change → `infrastructure.yml`).
- Depends on ticket 01 proving the gold → served path works.
- Observed: GitHub has been starting this `0 6 * * *` job ~6h late (Oct 8–10 runs began 12:06–13:02 UTC). That delay currently hides the ordering bug, but don't rely on it; set the cron explicitly after the pipeline, and consider triggering on gold's `latest.json` write instead of a fixed time.
