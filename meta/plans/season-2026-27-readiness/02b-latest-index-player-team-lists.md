# feat: Include player and team lists in served/index/latest.json

## What do you want to build?

The frontend (`frontend-app/scripts/app.js`, identical in `hoopstat-app`) fills its player and team dropdowns from `players` and `teams` arrays in `index/latest.json`. Gold's `write_latest_index()` only writes `latest_date`, `available_data` and `updated_at`. Any client of the index would show "Latest data: <date>" with empty selectors and could never load a `player_daily` / `team_daily` artifact without already knowing IDs.

This is a backend contract gap, not a frontend one. The same lists give MCP clients (follow-up 08's search tools) a name → ID lookup.

Add `players` and `teams` lists for the latest date to the index.

## Acceptance Criteria

- [ ] `latest.json` includes `players: [{"id": "<player_id>", "name": "<player_name>", "team_id": "<team_id>"}]` and `teams: [{"id": "<team_id>", "name": "<team_name>"}]` for every player and team with a daily artifact on `latest_date`, sorted by name
- [ ] Existing fields (`latest_date`, `available_data`, `updated_at`) unchanged; db-compiler, `build-database.yml`, the health aggregator and the MCP proxy still parse it
- [ ] IDs in the lists match the artifact filenames, so `player_daily/{latest_date}/{id}.json` resolves for every listed player
- [ ] Compatible with ticket 02's monotonic write (lists are written only when the index advances, or when the same date is reprocessed)
- [ ] Index size stays small (one night: ~250–350 players, ≤30 teams; well under the ~100 KB artifact cap from ADR-027)
- [ ] Unit tests cover the new fields and an empty-day case; gold tests pass and ruff is clean

## Implementation Notes (Optional)

- `GoldProcessor.process_date()` (`apps/gold-analytics/app/processors.py`) already has `player_analytics` and `team_analytics` DataFrames in hand when it calls `write_latest_index(target_date)`; pass them in rather than re-listing S3.
- Name fields already exist in the artifact payloads (`player_name`, `team_name` in `json_artifacts.py`); use the same source so names match.
- The frontend reads `item.id || item.player_id || item.team_id` and `item.name || item.full_name || item.team_name`, so `id` / `name` keys work with no frontend change.
- Do together with ticket 02 (same writer, same tests), as one PR or back to back.
