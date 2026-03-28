# Index Selection Rationale

> Documents the reasoning behind index choices for the HoopStat Haus static
> analytics databases (DuckDB and SQLite).

## Design Principles

1. **Read-optimized**: These are static, pre-built databases — there are no
   writes after compilation. Index overhead only affects build time, not query
   performance, so we can index more aggressively than a transactional database.

2. **Query-pattern driven**: Indexes are selected to support the most common
   analytical query patterns observed in basketball analytics workflows.

3. **Engine-compatible**: All indexes use standard SQL syntax compatible with
   both DuckDB and SQLite. DuckDB may create internal columnar indexes
   automatically, but explicit indexes ensure consistent performance in SQLite.

---

## Index Catalog

### `player_daily_stats` Indexes

| Index | Columns | Query Pattern | Example Query |
|-------|---------|---------------|---------------|
| `idx_pds_player_date` | `(player_id, game_date)` | Player lookup by date range | `SELECT * FROM player_daily_stats WHERE player_id = '203999' AND game_date BETWEEN '2024-01-01' AND '2024-01-31'` |
| `idx_pds_game_date` | `(game_date)` | Date-based filtering | `SELECT * FROM player_daily_stats WHERE game_date = '2024-01-15'` |
| `idx_pds_season_player` | `(season, player_id)` | Season-scoped player queries | `SELECT * FROM player_daily_stats WHERE season = '2023-24' AND player_id = '203999'` |

**Rationale**:

- **`idx_pds_player_date`** is the most critical index. The primary use case for
  player daily stats is "show me this player's games in this date range" — temporal
  analysis is the bread and butter of basketball analytics. The composite
  `(player_id, game_date)` allows index-only lookups for date-range scans within
  a single player.

- **`idx_pds_game_date`** supports "games on date X" queries, which are common
  for daily dashboards and top-list generation. A standalone date index avoids
  scanning the full table when no player filter is applied.

- **`idx_pds_season_player`** supports season-scoped queries where the season is
  the leading filter. This is distinct from the player-first index because season
  filtering (e.g., "all of Player X's games in 2023-24") benefits from season as
  the leading column when querying across multiple players in the same season.

### `team_daily_stats` Indexes

| Index | Columns | Query Pattern | Example Query |
|-------|---------|---------------|---------------|
| `idx_tds_team_date` | `(team_id, game_date)` | Team lookup by date range | `SELECT * FROM team_daily_stats WHERE team_id = '1610612747' AND game_date >= '2024-01-01'` |
| `idx_tds_game_date` | `(game_date)` | Date-based team filtering | `SELECT * FROM team_daily_stats WHERE game_date = '2024-01-15'` |

**Rationale**:

- **`idx_tds_team_date`** mirrors the player pattern — team temporal queries are
  equally common ("Lakers' last 10 games", "team performance this month").

- **`idx_tds_game_date`** supports daily team aggregation queries and the
  `v_team_standings` view which filters by season (derived from date range).

### `player_season_summary` Indexes

| Index | Columns | Query Pattern | Example Query |
|-------|---------|---------------|---------------|
| `idx_pss_season_player` | `(season, player_id)` | Season summary lookups | `SELECT * FROM player_season_summary WHERE season = '2023-24' AND player_id = '203999'` |
| `idx_pss_season_ppg` | `(season, points_per_game DESC)` | Leaderboard queries | `SELECT * FROM player_season_summary WHERE season = '2023-24' ORDER BY points_per_game DESC LIMIT 10` |

**Rationale**:

- **`idx_pss_season_player`** is the direct lookup index. Season summaries are
  almost always queried within a single season context.

- **`idx_pss_season_ppg`** is a sorted index specifically for leaderboard-style
  queries ("top 10 scorers this season"). The `DESC` ordering means the database
  engine can serve `ORDER BY points_per_game DESC LIMIT N` directly from the
  index without a full table sort. This pattern extends to other metrics via
  the query optimizer's ability to use this index for season-filtered scans.

### `team_season_summary` Indexes

| Index | Columns | Query Pattern | Example Query |
|-------|---------|---------------|---------------|
| `idx_tss_season_team` | `(season, team_id)` | Season team lookups | `SELECT * FROM team_season_summary WHERE season = '2023-24' AND team_id = '1610612747'` |

**Rationale**:

- **`idx_tss_season_team`** provides efficient lookups for team season data. With
  only ~30 teams per season, this table is small enough that additional indexes
  provide minimal benefit, but the season-leading composite ensures that
  cross-season queries (e.g., "show me all teams for 2023-24") can use an index
  scan rather than a full table scan.

### `top_lists` Indexes

| Index | Columns | Query Pattern | Example Query |
|-------|---------|---------------|---------------|
| `idx_tl_date_metric` | `(list_date, metric)` | Daily leaderboard lookups | `SELECT * FROM top_lists WHERE list_date = '2024-01-15' AND metric = 'Points Leaders'` |

**Rationale**:

- **`idx_tl_date_metric`** supports the most common access pattern: "show me
  today's leaderboard for metric X". Date-leading ensures efficient lookups
  when querying a specific day's leaderboards.

---

## Query Patterns Supported

The index strategy is designed to efficiently support these five primary
analytical query patterns:

### 1. Player Performance Filtering

> "Players averaging >25ppg and >5apg this season"

```sql
SELECT player_name, points_per_game, assists_per_game
FROM player_season_summary
WHERE season = '2023-24'
  AND points_per_game > 25
  AND assists_per_game > 5
ORDER BY points_per_game DESC;
```

**Index used**: `idx_pss_season_ppg` (season filter + sorted by ppg)

### 2. Team Comparison

> "Top 5 teams by offensive rating this season"

```sql
SELECT team_name, avg_offensive_rating, avg_defensive_rating, wins, losses
FROM v_team_standings
WHERE season = '2023-24'
ORDER BY avg_offensive_rating DESC
LIMIT 5;
```

**Index used**: `idx_tds_game_date` (supports the view's aggregation)

### 3. Temporal Analysis

> "Player scoring trend over the last 10 games"

```sql
-- DuckDB: use the v_player_game_log view
SELECT game_date, points, rolling_10g_ppg
FROM v_player_game_log
WHERE player_id = '203999' AND season = '2023-24'
ORDER BY game_date DESC
LIMIT 10;

-- SQLite: manual query
SELECT game_date, points
FROM player_daily_stats
WHERE player_id = '203999' AND season = '2023-24'
ORDER BY game_date DESC
LIMIT 10;
```

**Index used**: `idx_pds_player_date` or `idx_pds_season_player`

### 4. Cross-Entity Joins

> "Player stats joined with their team's win/loss record"

```sql
SELECT
    pds.player_name,
    pds.points,
    pds.game_date,
    tds.win,
    tds.offensive_rating AS team_offensive_rating
FROM player_daily_stats pds
JOIN team_daily_stats tds
    ON pds.team = tds.team_id
    AND pds.game_date = tds.game_date
WHERE pds.player_id = '203999';
```

**Indexes used**: `idx_pds_player_date` (player filter) + `idx_tds_team_date`
(join condition)

### 5. Leaderboard Queries

> "Top 10 scorers this season"

```sql
SELECT player_name, team, points_per_game, total_games
FROM player_season_summary
WHERE season = '2023-24'
ORDER BY points_per_game DESC
LIMIT 10;
```

**Index used**: `idx_pss_season_ppg` (sorted index eliminates sort step)

---

## Indexes Not Included (and Why)

| Candidate Index | Reason Excluded |
|----------------|-----------------|
| `(team) ON player_daily_stats` | Low cardinality (~30 teams); full scan is fast enough |
| `(position) ON player_daily_stats` | Very low cardinality (5 positions); index would not improve selectivity |
| `(win) ON team_daily_stats` | Boolean column with ~50% selectivity; not useful as standalone index |
| `(metric) ON top_lists` | Covered by `idx_tl_date_metric`; standalone metric filter is rare |
| Per-metric indexes on `player_season_summary` | One sorted index (`ppg DESC`) demonstrates the pattern; adding more (rebounds, assists, etc.) would increase build time with diminishing returns for a static dataset |
