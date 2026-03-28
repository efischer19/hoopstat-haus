# Static Database Guide

**Status:** Production
**Last Updated:** 2026-03-28
**Related ADRs:** [ADR-041](../meta/adr/ADR-041-static-database-artifacts.md), [ADR-028](../meta/adr/ADR-028-gold_layer_final.md)

## Overview

Hoopstat Haus publishes the entire Gold layer analytics dataset as static database files that you can query directly with SQL. Two formats are available:

| Format | URL |
|--------|-----|
| **DuckDB** | `https://data.hoopstat.haus/db/nba_current_season.duckdb` |
| **SQLite** | `https://data.hoopstat.haus/db/nba_current_season.sqlite` |

Both files are updated daily (2–4 hours after games complete) and contain identical data. Choose the format that best fits your use case — see [Format Selection Guide](#format-selection-guide) below.

---

## Quick Start

### DuckDB — Query Remotely (No Download)

DuckDB supports HTTP Range Requests, so you can query the database directly over the network:

```python
import duckdb

# Query the remote database directly (uses HTTP Range Requests)
result = duckdb.sql("""
    SELECT player_name, points_per_game, assists_per_game
    FROM 'https://data.hoopstat.haus/db/nba_current_season.duckdb'.player_season_summary
    ORDER BY points_per_game DESC
    LIMIT 10
""")
print(result)
```

### DuckDB CLI

```bash
# Install DuckDB CLI (macOS)
brew install duckdb

# Query the remote database
duckdb -c "
    ATTACH 'https://data.hoopstat.haus/db/nba_current_season.duckdb' AS nba (READ_ONLY);
    SELECT player_name, points_per_game
    FROM nba.player_season_summary
    ORDER BY points_per_game DESC
    LIMIT 10;
"
```

### SQLite — Download Then Query (Zero Dependencies)

```python
import urllib.request
import sqlite3

# Download the database (only ~2-5MB)
urllib.request.urlretrieve(
    "https://data.hoopstat.haus/db/nba_current_season.sqlite",
    "nba_current_season.sqlite"
)

# Query locally with zero dependencies
conn = sqlite3.connect("nba_current_season.sqlite")
for row in conn.execute("""
    SELECT player_name, points_per_game, assists_per_game
    FROM player_season_summary
    ORDER BY points_per_game DESC
    LIMIT 10
"""):
    print(row)
```

### SQLite CLI

```bash
# Download and query (sqlite3 is pre-installed on macOS/Linux)
curl -o nba.sqlite https://data.hoopstat.haus/db/nba_current_season.sqlite
sqlite3 nba.sqlite "SELECT player_name, points_per_game FROM player_season_summary ORDER BY points_per_game DESC LIMIT 10;"
```

### Node.js (using better-sqlite3)

```javascript
const Database = require('better-sqlite3');
const https = require('https');
const fs = require('fs');

// Download the SQLite database
const file = fs.createWriteStream('nba.sqlite');
https.get('https://data.hoopstat.haus/db/nba_current_season.sqlite', (res) => {
  res.pipe(file);
  file.on('finish', () => {
    const db = new Database('nba.sqlite', { readonly: true });
    const rows = db.prepare(`
      SELECT player_name, points_per_game
      FROM player_season_summary
      ORDER BY points_per_game DESC
      LIMIT 10
    `).all();
    console.table(rows);
  });
});
```

---

## Format Selection Guide

| Use Case | Recommended Format | Why |
|----------|-------------------|-----|
| AI agent / MCP proxy queries | DuckDB | Rich analytical SQL, HTTP Range Requests for remote querying |
| Data science / Jupyter notebooks | DuckDB | Window functions, CTEs, columnar execution for analytics |
| iOS / Android mobile app | SQLite | Built-in OS support, no third-party drivers needed |
| Flask / Django web app | SQLite | Standard library `sqlite3`, zero dependencies |
| PHP backend | SQLite | PDO SQLite driver is universal |
| Browser-based SQL (WASM) | Either | DuckDB WASM or sql.js (SQLite WASM) both work |
| Quick CLI exploration | DuckDB | `duckdb` CLI with remote `ATTACH`; or `sqlite3` for local file |

### Key Differences

| Feature | DuckDB | SQLite |
|---------|--------|--------|
| Remote query (no download) | ✅ HTTP Range Requests | ❌ Must download first |
| Window functions | ✅ Full support | ⚠️ Partial (no `ROWS BETWEEN` in older versions) |
| Date type | ✅ Native `DATE` | ⚠️ `TEXT` (ISO 8601 strings) |
| Boolean type | ✅ Native `BOOLEAN` | ⚠️ `INTEGER` (0/1) |
| Platform support | Requires DuckDB library | Built into every OS and language |
| File size | Slightly larger (columnar) | Smaller |

---

## Schema Documentation

The database contains five tables and up to three views, all derived from the Gold layer Pydantic models (`gold_models.py`). Data is compiled from Gold JSON artifacts in a single build pass.

### Tables at a Glance

| Table | Grain | Primary Key | Description |
|-------|-------|-------------|-------------|
| `player_daily_stats` | Player + Game | `(player_id, game_id)` | Per-game player box scores with advanced metrics |
| `team_daily_stats` | Team + Game | `(team_id, game_id)` | Per-game team stats with offensive/defensive ratings |
| `player_season_summary` | Player + Season | `(player_id, season)` | Season averages, shooting %, and performance trends |
| `team_season_summary` | Team + Season | `(team_id, season)` | Season efficiency metrics and Four Factors |
| `top_lists` | Metric + Date + Rank | `(metric, list_date, rank)` | Daily leaderboards by metric |

### Views

| View | Compatibility | Description |
|------|---------------|-------------|
| `v_team_standings` | Both | Season standings with W/L records and average ratings |
| `v_player_current_averages` | Both | Season summary joined with latest daily game stats |
| `v_player_game_log` | DuckDB only | Daily stats enriched with rolling 10-game averages |

### Table: `player_daily_stats`

Per-game player box score statistics with Gold-layer computed advanced metrics. One row per player per game.

| Column | DuckDB Type | SQLite Type | Nullable | Description |
|--------|-------------|-------------|----------|-------------|
| `player_id` | VARCHAR | TEXT | NOT NULL | Unique player identifier (NBA API string ID) |
| `player_name` | VARCHAR | TEXT | Yes | Player display name |
| `team` | VARCHAR | TEXT | Yes | Team abbreviation (e.g., 'LAL', 'BOS') |
| `position` | VARCHAR | TEXT | Yes | Player position (e.g., 'PG', 'SF') |
| `game_id` | VARCHAR | TEXT | Yes | Unique game identifier |
| `game_date` | DATE | TEXT | Yes | Game date (ISO 8601 YYYY-MM-DD) |
| `season` | VARCHAR | TEXT | Yes | NBA season identifier (e.g., '2025-26') |
| `points` | INTEGER | INTEGER | NOT NULL | Points scored (≥0) |
| `rebounds` | INTEGER | INTEGER | NOT NULL | Total rebounds (≥0) |
| `assists` | INTEGER | INTEGER | NOT NULL | Assists (≥0) |
| `steals` | INTEGER | INTEGER | NOT NULL | Steals (≥0) |
| `blocks` | INTEGER | INTEGER | NOT NULL | Blocks (≥0) |
| `turnovers` | INTEGER | INTEGER | NOT NULL | Turnovers (≥0) |
| `field_goals_made` | INTEGER | INTEGER | Yes | Field goals made |
| `field_goals_attempted` | INTEGER | INTEGER | Yes | Field goals attempted |
| `three_pointers_made` | INTEGER | INTEGER | Yes | Three-point field goals made |
| `three_pointers_attempted` | INTEGER | INTEGER | Yes | Three-point field goals attempted |
| `free_throws_made` | INTEGER | INTEGER | Yes | Free throws made |
| `free_throws_attempted` | INTEGER | INTEGER | Yes | Free throws attempted |
| `minutes_played` | DOUBLE | REAL | Yes | Minutes played (float for partial minutes) |
| `efficiency_rating` | DOUBLE | REAL | Yes | Player efficiency rating (PER-like metric) |
| `true_shooting_percentage` | DOUBLE | REAL | Yes | True shooting percentage (0–1 range) |
| `usage_rate` | DOUBLE | REAL | Yes | Usage rate percentage (0–1 range) |
| `plus_minus` | INTEGER | INTEGER | Yes | Plus/minus rating (can be negative) |

### Table: `team_daily_stats`

Per-game team statistics with Gold-layer computed ratings. One row per team per game.

| Column | DuckDB Type | SQLite Type | Nullable | Description |
|--------|-------------|-------------|----------|-------------|
| `team_id` | VARCHAR | TEXT | NOT NULL | Unique team identifier (NBA API string ID) |
| `team_name` | VARCHAR | TEXT | NOT NULL | Team display name (e.g., 'Los Angeles Lakers') |
| `game_id` | VARCHAR | TEXT | Yes | Unique game identifier |
| `game_date` | DATE | TEXT | Yes | Game date (ISO 8601 YYYY-MM-DD) |
| `season` | VARCHAR | TEXT | Yes | NBA season identifier (e.g., '2025-26') |
| `points` | INTEGER | INTEGER | NOT NULL | Total points scored (≥0) |
| `field_goals_made` | INTEGER | INTEGER | NOT NULL | Total field goals made (≥0) |
| `field_goals_attempted` | INTEGER | INTEGER | NOT NULL | Total field goals attempted (≥0) |
| `three_pointers_made` | INTEGER | INTEGER | Yes | Total three-pointers made |
| `three_pointers_attempted` | INTEGER | INTEGER | Yes | Total three-pointers attempted |
| `free_throws_made` | INTEGER | INTEGER | Yes | Total free throws made |
| `free_throws_attempted` | INTEGER | INTEGER | Yes | Total free throws attempted |
| `rebounds` | INTEGER | INTEGER | NOT NULL | Total rebounds (≥0) |
| `assists` | INTEGER | INTEGER | NOT NULL | Total assists (≥0) |
| `steals` | INTEGER | INTEGER | Yes | Total steals |
| `blocks` | INTEGER | INTEGER | Yes | Total blocks |
| `turnovers` | INTEGER | INTEGER | Yes | Total turnovers |
| `fouls` | INTEGER | INTEGER | Yes | Total fouls |
| `offensive_rating` | DOUBLE | REAL | Yes | Offensive rating (pts per 100 possessions) |
| `defensive_rating` | DOUBLE | REAL | Yes | Defensive rating (opponent pts per 100 possessions) |
| `pace` | DOUBLE | REAL | Yes | Pace (possessions per 48 minutes) |
| `true_shooting_percentage` | DOUBLE | REAL | Yes | Team true shooting percentage (0–1 range) |
| `opponent_team_id` | VARCHAR | TEXT | Yes | Opponent team identifier |
| `home_game` | BOOLEAN | INTEGER | Yes | Whether this was a home game (SQLite: 0/1) |
| `win` | BOOLEAN | INTEGER | Yes | Whether the team won (SQLite: 0/1) |

### Table: `player_season_summary`

Season-aggregated player statistics with per-game averages, shooting percentages, advanced metrics, and performance trends. One row per player per season.

| Column | DuckDB Type | SQLite Type | Nullable | Description |
|--------|-------------|-------------|----------|-------------|
| `player_id` | VARCHAR | TEXT | NOT NULL | Unique player identifier |
| `player_name` | VARCHAR | TEXT | Yes | Player display name |
| `season` | VARCHAR | TEXT | NOT NULL | NBA season identifier (e.g., '2025-26') |
| `team` | VARCHAR | TEXT | Yes | Primary team for the season |
| `total_games` | INTEGER | INTEGER | NOT NULL | Total games played (≥0) |
| `total_minutes` | DOUBLE | REAL | NOT NULL | Total minutes played (≥0) |
| `points_per_game` | DOUBLE | REAL | NOT NULL | Points per game (≥0) |
| `rebounds_per_game` | DOUBLE | REAL | NOT NULL | Rebounds per game (≥0) |
| `assists_per_game` | DOUBLE | REAL | NOT NULL | Assists per game (≥0) |
| `steals_per_game` | DOUBLE | REAL | NOT NULL | Steals per game (≥0) |
| `blocks_per_game` | DOUBLE | REAL | NOT NULL | Blocks per game (≥0) |
| `turnovers_per_game` | DOUBLE | REAL | NOT NULL | Turnovers per game (≥0) |
| `field_goal_percentage` | DOUBLE | REAL | Yes | Season FG% (0–1 range) |
| `three_point_percentage` | DOUBLE | REAL | Yes | Season 3P% (0–1 range) |
| `free_throw_percentage` | DOUBLE | REAL | Yes | Season FT% (0–1 range) |
| `efficiency_rating` | DOUBLE | REAL | Yes | Season efficiency rating |
| `true_shooting_percentage` | DOUBLE | REAL | Yes | Season true shooting % (0–1 range) |
| `usage_rate` | DOUBLE | REAL | Yes | Season usage rate (0–1 range) |
| `scoring_trend` | DOUBLE | REAL | Yes | Points per game trend (% change) |
| `efficiency_trend` | DOUBLE | REAL | Yes | Efficiency rating trend (% change) |

### Table: `team_season_summary`

Season-aggregated team statistics with per-game averages, efficiency metrics, Four Factors, and shooting percentages. One row per team per season.

| Column | DuckDB Type | SQLite Type | Nullable | Description |
|--------|-------------|-------------|----------|-------------|
| `team_id` | VARCHAR | TEXT | NOT NULL | Unique team identifier |
| `team_name` | VARCHAR | TEXT | Yes | Team display name |
| `season` | VARCHAR | TEXT | NOT NULL | NBA season identifier (e.g., '2025-26') |
| `season_type` | VARCHAR | TEXT | Yes | Season type (e.g., 'regular', 'playoff') |
| `total_games` | INTEGER | INTEGER | NOT NULL | Total games played (≥0) |
| `total_points` | INTEGER | INTEGER | NOT NULL | Total points scored (≥0) |
| `total_points_allowed` | INTEGER | INTEGER | NOT NULL | Total points allowed (≥0) |
| `points_per_game` | DOUBLE | REAL | NOT NULL | Points per game (≥0) |
| `points_allowed_per_game` | DOUBLE | REAL | NOT NULL | Points allowed per game (≥0) |
| `assists_per_game` | DOUBLE | REAL | NOT NULL | Assists per game (≥0) |
| `total_rebounds_per_game` | DOUBLE | REAL | NOT NULL | Total rebounds per game (≥0) |
| `turnovers_per_game` | DOUBLE | REAL | NOT NULL | Turnovers per game (≥0) |
| `field_goal_percentage` | DOUBLE | REAL | Yes | Season FG% (0–1 range) |
| `three_point_percentage` | DOUBLE | REAL | Yes | Season 3P% (0–1 range) |
| `free_throw_percentage` | DOUBLE | REAL | Yes | Season FT% (0–1 range) |
| `true_shooting_percentage` | DOUBLE | REAL | Yes | Season TS% (0–1 range) |
| `effective_field_goal_percentage` | DOUBLE | REAL | Yes | Effective FG% (0–1 range) |
| `offensive_rating` | DOUBLE | REAL | Yes | Offensive rating (pts per 100 possessions) |
| `defensive_rating` | DOUBLE | REAL | Yes | Defensive rating (opponent pts per 100 possessions) |
| `net_rating` | DOUBLE | REAL | Yes | Net rating (offensive − defensive) |
| `pace` | DOUBLE | REAL | Yes | Pace (possessions per 48 minutes) |
| `turnover_percentage` | DOUBLE | REAL | Yes | Turnover percentage (0–1 range) |
| `offensive_rebound_percentage` | DOUBLE | REAL | Yes | Offensive rebound percentage (0–1 range) |
| `free_throw_rate` | DOUBLE | REAL | Yes | Free throw rate (FTA / FGA) |
| `data_quality_score` | DOUBLE | REAL | Yes | Data quality score (0–1 range) |

### Table: `top_lists`

Daily leaderboards by metric. Each row represents one player's ranking in a specific metric on a specific date.

| Column | DuckDB Type | SQLite Type | Nullable | Description |
|--------|-------------|-------------|----------|-------------|
| `metric` | VARCHAR | TEXT | NOT NULL | Metric name (e.g., 'Points Leaders') |
| `list_date` | DATE | TEXT | NOT NULL | Date of the leaderboard (ISO 8601) |
| `rank` | INTEGER | INTEGER | NOT NULL | Player rank within the leaderboard (1-based) |
| `player_id` | VARCHAR | TEXT | NOT NULL | Player identifier |
| `player_name` | VARCHAR | TEXT | Yes | Player display name |
| `team` | VARCHAR | TEXT | Yes | Team abbreviation |
| `value` | DOUBLE | REAL | NOT NULL | Metric value for this player on this date |

### Indexes

All indexes are designed for read-heavy analytical queries. See `apps/db-compiler/schema/index_rationale.md` for design rationale.

| Index | Table | Columns | Purpose |
|-------|-------|---------|---------|
| `idx_pds_player_date` | player_daily_stats | `(player_id, game_date)` | Player temporal lookups |
| `idx_pds_game_date` | player_daily_stats | `(game_date)` | Date-based filtering |
| `idx_pds_season_player` | player_daily_stats | `(season, player_id)` | Season-scoped player queries |
| `idx_tds_team_date` | team_daily_stats | `(team_id, game_date)` | Team temporal lookups |
| `idx_tds_game_date` | team_daily_stats | `(game_date)` | Date-based filtering |
| `idx_pss_season_player` | player_season_summary | `(season, player_id)` | Season-scoped player queries |
| `idx_pss_season_ppg` | player_season_summary | `(season, points_per_game DESC)` | Leaderboard queries |
| `idx_tss_season_team` | team_season_summary | `(season, team_id)` | Season-scoped team queries |
| `idx_tl_date_metric` | top_lists | `(list_date, metric)` | Date-based leaderboard lookups |

### Type Mapping Reference

| Pydantic | DuckDB | SQLite | Notes |
|----------|--------|--------|-------|
| `str` | VARCHAR | TEXT | IDs, names, abbreviations |
| `int` | INTEGER | INTEGER | Counting stats (≥0) |
| `float` | DOUBLE | REAL | Metrics, percentages |
| `str` (date) | DATE | TEXT | ISO 8601 format (YYYY-MM-DD) |
| `str` (season) | VARCHAR | TEXT | Format "YYYY-YY" (e.g., '2025-26') |
| `bool` | BOOLEAN | INTEGER | DuckDB uses native booleans; SQLite uses 0/1 |

---

## Example SQL Queries

The following queries are compatible with **both DuckDB and SQLite** unless noted otherwise. Dates used in examples are illustrative — replace with actual dates from your dataset.

### 1. Top 10 Scorers This Season

```sql
SELECT player_name, team, points_per_game
FROM player_season_summary
ORDER BY points_per_game DESC
LIMIT 10;
```

### 2. Players Averaging a Double-Double

```sql
SELECT player_name, team, points_per_game, rebounds_per_game, assists_per_game
FROM player_season_summary
WHERE (points_per_game >= 10 AND rebounds_per_game >= 10)
   OR (points_per_game >= 10 AND assists_per_game >= 10)
ORDER BY points_per_game DESC;
```

### 3. Team Offensive Ratings From a Specific Date

```sql
SELECT team_name, offensive_rating, defensive_rating,
       offensive_rating - defensive_rating AS net_rating
FROM team_daily_stats
WHERE game_date = '2026-03-25'
ORDER BY net_rating DESC;
```

### 4. Player Shooting Efficiency Trend (Last 10 Games)

```sql
SELECT game_date, points, true_shooting_percentage, efficiency_rating
FROM player_daily_stats
WHERE player_name = 'Luka Doncic'
ORDER BY game_date DESC
LIMIT 10;
```

### 5. Best 3-Point Shooters (Minimum 20 Games Played)

```sql
SELECT player_name, team, three_point_percentage,
       CAST(total_games AS INTEGER) AS games
FROM player_season_summary
WHERE three_point_percentage IS NOT NULL
  AND total_games >= 20
ORDER BY three_point_percentage DESC
LIMIT 15;
```

### 6. Teams With Best Home Records

```sql
SELECT team_name,
       SUM(CASE WHEN win = 1 AND home_game = 1 THEN 1 ELSE 0 END) AS home_wins,
       SUM(CASE WHEN home_game = 1 THEN 1 ELSE 0 END) AS home_games
FROM team_daily_stats
GROUP BY team_name
ORDER BY home_wins DESC;
```

### 7. Players With Improving Efficiency (Positive Trend)

```sql
SELECT player_name, team, efficiency_rating, efficiency_trend
FROM player_season_summary
WHERE efficiency_trend > 0
ORDER BY efficiency_trend DESC
LIMIT 10;
```

### 8. High-Scoring Games on a Date

```sql
SELECT p.player_name, p.team, p.points, p.assists, p.rebounds,
       p.true_shooting_percentage
FROM player_daily_stats p
WHERE p.game_date = '2026-03-25'
  AND p.points >= 30
ORDER BY p.points DESC;
```

### 9. Team Comparison Query

```sql
SELECT team_name,
       AVG(offensive_rating) AS avg_off_rating,
       AVG(defensive_rating) AS avg_def_rating,
       AVG(offensive_rating) - AVG(defensive_rating) AS avg_net_rating
FROM team_daily_stats
WHERE season = '2025-26'
GROUP BY team_name
ORDER BY avg_net_rating DESC;
```

### 10. Cross-Table Join: Player Stats With Team Context

```sql
SELECT p.player_name, p.points, p.assists,
       t.team_name, t.win, t.offensive_rating
FROM player_daily_stats p
JOIN team_daily_stats t
  ON p.game_date = t.game_date AND p.team = t.team_name
WHERE p.game_date = '2026-03-25'
ORDER BY p.points DESC
LIMIT 20;
```

> **Note:** The `player_daily_stats.team` column stores team abbreviations
> (e.g., 'LAL'), while `team_daily_stats.team_name` stores full names
> (e.g., 'Los Angeles Lakers'). If the join above returns no rows, use
> `team_id` instead:
>
> ```sql
> JOIN team_daily_stats t
>   ON p.game_date = t.game_date
>   AND p.team = (SELECT team_name FROM team_season_summary WHERE team_id = t.team_id LIMIT 1)
> ```
>
> Or join via a subquery on `player_daily_stats.player_id` and
> `team_daily_stats.team_id` if both reference the same team ID format.

### 11. Season Standings via View

```sql
SELECT team_name, wins, losses, avg_offensive_rating, avg_defensive_rating
FROM v_team_standings
WHERE season = '2025-26'
ORDER BY wins DESC;
```

### 12. Player Current Form via View

```sql
SELECT player_name, team, points_per_game,
       latest_points, latest_game_date,
       scoring_trend
FROM v_player_current_averages
WHERE season = '2025-26'
ORDER BY points_per_game DESC
LIMIT 10;
```

---

## MCP Integration

The Hoopstat MCP server provides an `execute_nba_sql_query` tool that lets AI agents run SQL queries against the DuckDB database. See [MCP_SETUP.md](../MCP_SETUP.md) for full setup instructions.

**Example natural language prompts an AI agent can answer via SQL:**

- "Who are the top 10 scorers in the NBA this season?"
- "Show me players averaging a triple-double"
- "Compare the Celtics and Lakers offensive efficiency"
- "Which players have the best true shooting percentage with at least 20 games played?"
- "What was the highest-scoring game last week?"

---

## Troubleshooting

### CORS Errors in the Browser

**Symptom:** Browser console shows CORS errors when fetching `.duckdb` or `.sqlite` files.

**Solutions:**

1. Verify you are using the CloudFront URL (`https://data.hoopstat.haus/db/...`), not a direct S3 URL.
2. Ensure the request uses HTTPS (not HTTP).
3. Check that the CloudFront distribution status is "Deployed".
4. For DuckDB WASM, ensure your page origin is allowed by CORS policy.

### HTTP Range Request Failures (DuckDB Remote)

**Symptom:** DuckDB remote ATTACH or query fails with a network error.

**Solutions:**

1. Verify the URL is correct and the file exists: `curl -I https://data.hoopstat.haus/db/nba_current_season.duckdb`
2. Confirm Range Requests are supported: look for `Accept-Ranges: bytes` in the response headers.
3. Update DuckDB to the latest version — older versions may have HTTP client issues.
4. If behind a corporate proxy, the proxy may strip Range headers. Try downloading the file instead.

### Version Mismatch (DuckDB)

**Symptom:** "Serialization Error: Failed to deserialize" or similar when opening the DuckDB file.

**Solutions:**

1. The `.duckdb` file format is tied to the DuckDB version that created it. Update your DuckDB CLI or library to match.
2. Check the database build metadata: `duckdb -c "SELECT * FROM duckdb_extensions();"` to see the version.
3. As a fallback, use the SQLite file instead — the SQLite format is stable across versions.

### SQLite "Database is Locked" or Read-Only Errors

**Symptom:** Cannot open the downloaded SQLite file.

**Solutions:**

1. Ensure the file downloaded completely (check file size matches `Content-Length` header).
2. Open in read-only mode: `sqlite3 -readonly nba.sqlite` or `sqlite3.connect("nba.sqlite", uri=True)` with `?mode=ro`.
3. On Windows, ensure no other process has the file open.

### Empty Query Results

**Symptom:** Queries return no rows.

**Solutions:**

1. Check available seasons: `SELECT DISTINCT season FROM player_season_summary;`
2. Check available dates: `SELECT DISTINCT game_date FROM player_daily_stats ORDER BY game_date DESC LIMIT 10;`
3. Verify player/team names match exactly: `SELECT DISTINCT player_name FROM player_season_summary ORDER BY player_name;`
4. For date-filtered queries, ensure the date format matches ISO 8601 (`YYYY-MM-DD`).

---

## References

- [ADR-041: Polyglot Static Database Artifacts](../meta/adr/ADR-041-static-database-artifacts.md)
- [ADR-028: Gold Layer Architecture](../meta/adr/ADR-028-gold_layer_final.md)
- [Data Dictionary](DATA_DICTIONARY.md) — Full Pydantic model documentation
- [JSON Artifact Schemas](JSON_ARTIFACT_SCHEMAS.md) — JSON artifact format reference
- [Public Access Guide](../infrastructure/PUBLIC_ACCESS_GUIDE.md) — CloudFront infrastructure details
- [MCP Setup Guide](../MCP_SETUP.md) — AI agent integration via MCP
