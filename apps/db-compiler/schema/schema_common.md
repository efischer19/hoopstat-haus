# Database Schema Documentation

> Shared schema reference for the HoopStat Haus static analytics databases.
> Both DuckDB (`duckdb_schema.sql`) and SQLite (`sqlite_schema.sql`) variants
> are generated from this common design.

## Architecture Context

- **ADR-041**: Polyglot Static Database Artifacts (DuckDB & SQLite)
- **Source models**: `libs/hoopstat-data/hoopstat_data/gold_models.py`
- **JSON artifact mappings**: `apps/gold-analytics/app/json_artifacts.py`

The schema maps directly from Gold layer Pydantic models to SQL DDL, optimized
for read-heavy analytical queries typical of basketball analytics. Both database
files are compiled from the same Gold JSON data during a single build pass.

---

## Tables

### `player_daily_stats`

**Source model**: `GoldPlayerDailyStats`

Per-game player box score statistics with Gold-layer computed advanced metrics.
One row per player per game.

| Column | Pydantic Field | Pydantic Type | DuckDB Type | SQLite Type | Nullable | Description |
|--------|---------------|---------------|-------------|-------------|----------|-------------|
| `player_id` | `player_id` | `str` | `VARCHAR` | `TEXT` | NOT NULL | Unique player identifier (NBA API string ID) |
| `player_name` | `player_name` | `str \| None` | `VARCHAR` | `TEXT` | Yes | Player display name |
| `team` | `team` | `str \| None` | `VARCHAR` | `TEXT` | Yes | Team abbreviation (e.g., 'LAL', 'BOS') |
| `position` | `position` | `str \| None` | `VARCHAR` | `TEXT` | Yes | Player position (e.g., 'PG', 'SF') |
| `game_id` | `game_id` | `str \| None` | `VARCHAR` | `TEXT` | Yes | Unique game identifier |
| `game_date` | `game_date` | `str \| None` | `DATE` | `TEXT` | Yes | Game date (DuckDB native DATE; SQLite ISO 8601 TEXT) |
| `season` | `season` | `str \| None` | `VARCHAR` | `TEXT` | Yes | NBA season identifier (e.g., '2023-24') |
| `points` | `points` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Points scored (≥0) |
| `rebounds` | `rebounds` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Total rebounds (≥0) |
| `assists` | `assists` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Assists (≥0) |
| `steals` | `steals` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Steals (≥0) |
| `blocks` | `blocks` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Blocks (≥0) |
| `turnovers` | `turnovers` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Turnovers (≥0) |
| `field_goals_made` | `field_goals_made` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Field goals made |
| `field_goals_attempted` | `field_goals_attempted` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Field goals attempted |
| `three_pointers_made` | `three_pointers_made` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Three-point field goals made |
| `three_pointers_attempted` | `three_pointers_attempted` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Three-point field goals attempted |
| `free_throws_made` | `free_throws_made` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Free throws made |
| `free_throws_attempted` | `free_throws_attempted` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Free throws attempted |
| `minutes_played` | `minutes_played` | `float \| None` | `DOUBLE` | `REAL` | Yes | Minutes played |
| `efficiency_rating` | `efficiency_rating` | `float \| None` | `DOUBLE` | `REAL` | Yes | Player efficiency rating (PER-like) |
| `true_shooting_percentage` | `true_shooting_percentage` | `float \| None` | `DOUBLE` | `REAL` | Yes | True shooting percentage (0–1) |
| `usage_rate` | `usage_rate` | `float \| None` | `DOUBLE` | `REAL` | Yes | Usage rate percentage (0–1) |
| `plus_minus` | `plus_minus` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Plus/minus rating |

**Primary key**: `(player_id, game_id)`

---

### `team_daily_stats`

**Source model**: `GoldTeamDailyStats`

Per-game team statistics with Gold-layer computed ratings. One row per team per game.

| Column | Pydantic Field | Pydantic Type | DuckDB Type | SQLite Type | Nullable | Description |
|--------|---------------|---------------|-------------|-------------|----------|-------------|
| `team_id` | `team_id` | `str` | `VARCHAR` | `TEXT` | NOT NULL | Unique team identifier |
| `team_name` | `team_name` | `str` | `VARCHAR` | `TEXT` | NOT NULL | Team display name |
| `game_id` | `game_id` | `str \| None` | `VARCHAR` | `TEXT` | Yes | Unique game identifier |
| `game_date` | `game_date` | `str \| None` | `DATE` | `TEXT` | Yes | Game date |
| `season` | `season` | `str \| None` | `VARCHAR` | `TEXT` | Yes | NBA season identifier |
| `points` | `points` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Total points scored (≥0) |
| `field_goals_made` | `field_goals_made` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Total field goals made (≥0) |
| `field_goals_attempted` | `field_goals_attempted` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Total field goals attempted (≥0) |
| `three_pointers_made` | `three_pointers_made` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Total three-pointers made |
| `three_pointers_attempted` | `three_pointers_attempted` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Total three-pointers attempted |
| `free_throws_made` | `free_throws_made` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Total free throws made |
| `free_throws_attempted` | `free_throws_attempted` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Total free throws attempted |
| `rebounds` | `rebounds` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Total rebounds (≥0) |
| `assists` | `assists` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Total assists (≥0) |
| `steals` | `steals` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Total steals |
| `blocks` | `blocks` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Total blocks |
| `turnovers` | `turnovers` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Total turnovers |
| `fouls` | `fouls` | `int \| None` | `INTEGER` | `INTEGER` | Yes | Total fouls |
| `offensive_rating` | `offensive_rating` | `float \| None` | `DOUBLE` | `REAL` | Yes | Points per 100 possessions |
| `defensive_rating` | `defensive_rating` | `float \| None` | `DOUBLE` | `REAL` | Yes | Opponent points per 100 possessions |
| `pace` | `pace` | `float \| None` | `DOUBLE` | `REAL` | Yes | Possessions per 48 minutes |
| `true_shooting_percentage` | `true_shooting_percentage` | `float \| None` | `DOUBLE` | `REAL` | Yes | Team TS% (0–1) |
| `opponent_team_id` | `opponent_team_id` | `str \| None` | `VARCHAR` | `TEXT` | Yes | Opponent team identifier |
| `home_game` | `home_game` | `bool \| None` | `BOOLEAN` | `INTEGER` | Yes | Home game flag (SQLite: 0/1) |
| `win` | `win` | `bool \| None` | `BOOLEAN` | `INTEGER` | Yes | Win flag (SQLite: 0/1) |

**Primary key**: `(team_id, game_id)`

---

### `player_season_summary`

**Source model**: `GoldPlayerSeasonSummary`

Season-aggregated player statistics with per-game averages, shooting percentages,
advanced metrics, and performance trends. One row per player per season.

| Column | Pydantic Field | Pydantic Type | DuckDB Type | SQLite Type | Nullable | Description |
|--------|---------------|---------------|-------------|-------------|----------|-------------|
| `player_id` | `player_id` | `str` | `VARCHAR` | `TEXT` | NOT NULL | Unique player identifier |
| `player_name` | `player_name` | `str \| None` | `VARCHAR` | `TEXT` | Yes | Player display name |
| `season` | `season` | `str` | `VARCHAR` | `TEXT` | NOT NULL | NBA season identifier |
| `team` | `team` | `str \| None` | `VARCHAR` | `TEXT` | Yes | Primary team for the season |
| `total_games` | `total_games` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Total games played (≥0) |
| `total_minutes` | `total_minutes` | `float` | `DOUBLE` | `REAL` | NOT NULL | Total minutes played (≥0) |
| `points_per_game` | `points_per_game` | `float` | `DOUBLE` | `REAL` | NOT NULL | Points per game (≥0) |
| `rebounds_per_game` | `rebounds_per_game` | `float` | `DOUBLE` | `REAL` | NOT NULL | Rebounds per game (≥0) |
| `assists_per_game` | `assists_per_game` | `float` | `DOUBLE` | `REAL` | NOT NULL | Assists per game (≥0) |
| `steals_per_game` | `steals_per_game` | `float` | `DOUBLE` | `REAL` | NOT NULL | Steals per game (≥0) |
| `blocks_per_game` | `blocks_per_game` | `float` | `DOUBLE` | `REAL` | NOT NULL | Blocks per game (≥0) |
| `turnovers_per_game` | `turnovers_per_game` | `float` | `DOUBLE` | `REAL` | NOT NULL | Turnovers per game (≥0) |
| `field_goal_percentage` | `field_goal_percentage` | `float \| None` | `DOUBLE` | `REAL` | Yes | Season FG% (0–1) |
| `three_point_percentage` | `three_point_percentage` | `float \| None` | `DOUBLE` | `REAL` | Yes | Season 3P% (0–1) |
| `free_throw_percentage` | `free_throw_percentage` | `float \| None` | `DOUBLE` | `REAL` | Yes | Season FT% (0–1) |
| `efficiency_rating` | `efficiency_rating` | `float \| None` | `DOUBLE` | `REAL` | Yes | Season efficiency rating |
| `true_shooting_percentage` | `true_shooting_percentage` | `float \| None` | `DOUBLE` | `REAL` | Yes | Season TS% (0–1) |
| `usage_rate` | `usage_rate` | `float \| None` | `DOUBLE` | `REAL` | Yes | Season usage rate (0–1) |
| `scoring_trend` | `scoring_trend` | `float \| None` | `DOUBLE` | `REAL` | Yes | PPG trend (% change) |
| `efficiency_trend` | `efficiency_trend` | `float \| None` | `DOUBLE` | `REAL` | Yes | Efficiency trend (% change) |

**Primary key**: `(player_id, season)`

---

### `team_season_summary`

**Source model**: `GoldTeamSeasonSummary`

Season-aggregated team statistics with per-game averages, efficiency metrics,
Four Factors, and shooting percentages. One row per team per season.

| Column | Pydantic Field | Pydantic Type | DuckDB Type | SQLite Type | Nullable | Description |
|--------|---------------|---------------|-------------|-------------|----------|-------------|
| `team_id` | `team_id` | `str` | `VARCHAR` | `TEXT` | NOT NULL | Unique team identifier |
| `team_name` | `team_name` | `str \| None` | `VARCHAR` | `TEXT` | Yes | Team display name |
| `season` | `season` | `str` | `VARCHAR` | `TEXT` | NOT NULL | NBA season identifier |
| `season_type` | `season_type` | `str \| None` | `VARCHAR` | `TEXT` | Yes | Season type (regular/playoff) |
| `total_games` | `total_games` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Total games played (≥0) |
| `total_points` | `total_points` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Total points scored (≥0) |
| `total_points_allowed` | `total_points_allowed` | `int` | `INTEGER` | `INTEGER` | NOT NULL | Total points allowed (≥0) |
| `points_per_game` | `points_per_game` | `float` | `DOUBLE` | `REAL` | NOT NULL | Points per game (≥0) |
| `points_allowed_per_game` | `points_allowed_per_game` | `float` | `DOUBLE` | `REAL` | NOT NULL | Points allowed per game (≥0) |
| `assists_per_game` | `assists_per_game` | `float` | `DOUBLE` | `REAL` | NOT NULL | Assists per game (≥0) |
| `total_rebounds_per_game` | `total_rebounds_per_game` | `float` | `DOUBLE` | `REAL` | NOT NULL | Total rebounds per game (≥0) |
| `turnovers_per_game` | `turnovers_per_game` | `float` | `DOUBLE` | `REAL` | NOT NULL | Turnovers per game (≥0) |
| `field_goal_percentage` | `field_goal_percentage` | `float \| None` | `DOUBLE` | `REAL` | Yes | Season FG% (0–1) |
| `three_point_percentage` | `three_point_percentage` | `float \| None` | `DOUBLE` | `REAL` | Yes | Season 3P% (0–1) |
| `free_throw_percentage` | `free_throw_percentage` | `float \| None` | `DOUBLE` | `REAL` | Yes | Season FT% (0–1) |
| `true_shooting_percentage` | `true_shooting_percentage` | `float \| None` | `DOUBLE` | `REAL` | Yes | Season TS% (0–1) |
| `effective_field_goal_percentage` | `effective_field_goal_percentage` | `float \| None` | `DOUBLE` | `REAL` | Yes | Effective FG% (0–1) |
| `offensive_rating` | `offensive_rating` | `float \| None` | `DOUBLE` | `REAL` | Yes | Points per 100 possessions |
| `defensive_rating` | `defensive_rating` | `float \| None` | `DOUBLE` | `REAL` | Yes | Opponent points per 100 possessions |
| `net_rating` | `net_rating` | `float \| None` | `DOUBLE` | `REAL` | Yes | Net rating (off - def) |
| `pace` | `pace` | `float \| None` | `DOUBLE` | `REAL` | Yes | Possessions per 48 minutes |
| `turnover_percentage` | `turnover_percentage` | `float \| None` | `DOUBLE` | `REAL` | Yes | Turnover percentage (0–1) |
| `offensive_rebound_percentage` | `offensive_rebound_percentage` | `float \| None` | `DOUBLE` | `REAL` | Yes | Offensive rebound % (0–1) |
| `free_throw_rate` | `free_throw_rate` | `float \| None` | `DOUBLE` | `REAL` | Yes | Free throw rate (FTA/FGA) |
| `data_quality_score` | `data_quality_score` | `float \| None` | `DOUBLE` | `REAL` | Yes | Data quality score (0–1) |

**Primary key**: `(team_id, season)`

---

### `top_lists`

**Source**: Top lists JSON artifacts (`json_artifacts.py`)

Daily leaderboards by metric. Each row represents one player's ranking in a specific
metric on a specific date. The structure is denormalized from the nested JSON format
for efficient SQL querying.

| Column | JSON Field | DuckDB Type | SQLite Type | Nullable | Description |
|--------|-----------|-------------|-------------|----------|-------------|
| `metric` | `metric` | `VARCHAR` | `TEXT` | NOT NULL | Metric name (e.g., 'Points Leaders') |
| `list_date` | `date` | `DATE` | `TEXT` | NOT NULL | Date of the leaderboard |
| `rank` | `players[].rank` | `INTEGER` | `INTEGER` | NOT NULL | Player rank (1-based) |
| `player_id` | `players[].player_id` | `VARCHAR` | `TEXT` | NOT NULL | Player identifier |
| `player_name` | `players[].player_name` | `VARCHAR` | `TEXT` | Yes | Player display name |
| `team` | `players[].team` | `VARCHAR` | `TEXT` | Yes | Team abbreviation |
| `value` | `players[].value` | `DOUBLE` | `REAL` | NOT NULL | Metric value |

**Primary key**: `(metric, list_date, rank)`

---

## Type Mapping Reference

| Pydantic Type | DuckDB Type | SQLite Type | Notes |
|---------------|-------------|-------------|-------|
| `str` | `VARCHAR` | `TEXT` | IDs, names, abbreviations |
| `int` | `INTEGER` | `INTEGER` | Counting stats (non-negative) |
| `float` | `DOUBLE` | `REAL` | Computed metrics, percentages |
| `str` (date) | `DATE` | `TEXT` | DuckDB has native DATE; SQLite uses ISO 8601 TEXT |
| `str` (season) | `VARCHAR` | `TEXT` | Format "YYYY-YY" (e.g., '2023-24') |
| `bool` | `BOOLEAN` | `INTEGER` | SQLite uses 0/1 for boolean values |

---

## Excluded Fields

The following Pydantic model fields are intentionally excluded from the database
schema because they are infrastructure metadata not relevant to analytics queries:

| Field | Reason |
|-------|--------|
| `partition_key` | S3 partition metadata; not relevant for SQL queries |
| `lineage` | Pydantic `DataLineage` object for ETL tracking; not analytical data |
| `validation_mode` | Internal Pydantic validation configuration |

---

## Views

### `v_team_standings`

**Compatibility**: Both DuckDB and SQLite

Aggregates team daily stats into season standings with win/loss records and
average ratings. Useful for team comparison and ranking queries.

**Columns**: `team_id`, `team_name`, `season`, `games_played`, `wins`, `losses`,
`avg_points`, `avg_offensive_rating`, `avg_defensive_rating`, `avg_pace`

### `v_player_current_averages`

**Compatibility**: Both engines (DuckDB uses `ROW_NUMBER()` window function;
SQLite uses correlated subquery)

Joins player season summary with their most recent daily performance for
"current form" lookups combining season averages and latest game stats.

**Columns**: Season averages from `player_season_summary` plus latest game
`points`, `rebounds`, `assists`, `efficiency_rating`, and `game_date`

### `v_player_game_log` (DuckDB only)

**Compatibility**: DuckDB only (uses `ROWS BETWEEN` window frames)

Enriched player game log with rolling 10-game averages for temporal trend analysis.

**Columns**: Daily stats plus `rolling_10g_ppg`, `rolling_10g_rpg`, `rolling_10g_apg`
