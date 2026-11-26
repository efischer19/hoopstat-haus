# feat: MCP tools a model can actually use (search, leaders, season stats)

## What do you want to build?

The MCP proxy exposes two tools: `get_index` and `get_artifact(resource_uri)`. To answer "how is Wembanyama doing this season?", a model would have to already know NBA player IDs, dates and our S3 path layout. Add task-shaped tools on top of the public artifacts and the DuckDB file.

## Acceptance Criteria

- [ ] `search_players(name)` / `search_teams(name)`: fuzzy name → ID lookup (e.g. bundled from `nba_api.stats.static` or a players/teams JSON published by gold)
- [ ] `get_latest_leaders(metric?)`: the most recent `top_lists/{latest_date}/` without the caller knowing the date
- [ ] `get_player_season(player, season?)` / `get_team_season(team, season?)`: season-to-date summary by name or ID (needs readiness ticket 04)
- [ ] `get_player_games(player, last_n?)`: recent per-game lines
- [ ] Optional: `query_sql(sql)`, a read-only query against `https://hoopstat.haus/db/nba_current_season.duckdb` via DuckDB's httpfs, with row/time limits
- [ ] Tool docstrings written for models: what each returns, units, and that season stats are regular-season only
- [ ] Tests use `respx` / fixtures; no live network in CI

## Implementation Notes (Optional)

- Depends on follow-up 07 (package rename / mcp 2.x) and readiness ticket 04 (season summaries).
- Per ADR-033 all compute stays client-side; the server only reads public static files.
- DuckDB is a heavy dependency. Consider making `query_sql` an optional extra (`hoopstat-mcp-proxy[sql]`).
