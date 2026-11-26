# feat: Backfill 2025-26 public artifacts from existing silver data

## What do you want to build?

Bronze, silver and gold buckets hold 2025-26 data through 2026-03-10, but none of it was published to `served/` (gold's publishing code arrived 2026-03-15). Replay those dates so the public artifacts, the database and the MCP tools include last season through March 10.

Re-running silver for a date writes its `silver-ready` marker, which re-triggers gold with the current code. No re-ingestion from the NBA API is needed.

## Acceptance Criteria

- [ ] Earliest 2025-26 date in the silver bucket identified, and the replay covers it through 2026-03-10
- [ ] Replayed in chunks small enough for the silver Lambda's 5-minute timeout (e.g. by week or month via `silver-processing.yml -f start_date=… -f end_date=…`), with gold failures checked per chunk
- [ ] `served/player_daily/`, `team_daily/`, `top_lists/` exist for every 2025-26 game date
- [ ] `latest.json` still points at the newest 2026-27 date afterwards (requires readiness ticket 02)
- [ ] 2025-26 season summaries generated (`season-players` / `season-teams --season 2025-26`); regular season only
- [ ] Next Build Database run includes 2025-26 rows

## Implementation Notes (Optional)

- **Requires readiness ticket 02** (monotonic `latest.json`), or the replay will repoint the public index at March 2026.
- Pre-#453 bronze data (before 2025-12-31) may hold only one game per date (the overwrite bug). Check silver row counts per date for Oct–Dec 2025; re-ingest those dates from the Pi (`run-daily.sh --date …`) if they're short.
- 2026-03-11 through the end of 2025-26 (including playoffs) was never ingested; that's a separate Pi backfill if wanted.
- Earlier seasons: the public fhoopz CSVs (`www.eric-fischer.codes/fhoopz/data/irl/game_logs/`, 2019-10 → 2025-11) are a possible source, but in a different schema. Out of scope here.
