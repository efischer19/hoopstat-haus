-- =============================================================================
-- DuckDB Schema for HoopStat Haus Static Analytics Database
-- =============================================================================
-- Generated from Gold layer Pydantic models defined in:
--   libs/hoopstat-data/hoopstat_data/gold_models.py
--
-- Architecture context:
--   ADR-041: Polyglot Static Database Artifacts (DuckDB & SQLite)
--   This file is the DuckDB-specific DDL. A companion sqlite_schema.sql
--   provides the SQLite variant. Core table structure is identical; differences
--   are limited to type mappings (DATE vs TEXT, BOOLEAN vs INTEGER) and
--   engine-specific views.
--
-- Type mapping notes (Pydantic → DuckDB):
--   str  → VARCHAR   (player IDs, team IDs, names)
--   int  → INTEGER   (counting stats, non-negative)
--   float → DOUBLE   (computed metrics, percentages)
--   str (date) → DATE (native DATE type; ISO 8601 format)
--   str (season) → VARCHAR (format "YYYY-YY")
--   bool → BOOLEAN   (native boolean support)
-- =============================================================================


-- =============================================================================
-- Table: player_daily_stats
-- Source: GoldPlayerDailyStats (gold_models.py)
-- Description: Per-game player box score statistics with Gold-layer computed
--   advanced metrics. One row per player per game.
-- =============================================================================
CREATE TABLE IF NOT EXISTS player_daily_stats (
    -- Identity & context
    player_id       VARCHAR NOT NULL,   -- Unique player identifier (NBA API string ID)
    player_name     VARCHAR,            -- Player display name
    team            VARCHAR,            -- Team abbreviation (e.g., 'LAL', 'BOS')
    position        VARCHAR,            -- Player position (e.g., 'PG', 'SF')
    game_id         VARCHAR,            -- Unique game identifier
    game_date       DATE,               -- Game date (DuckDB native DATE)
    season          VARCHAR,            -- NBA season identifier (e.g., '2023-24')

    -- Core box score stats
    points          INTEGER NOT NULL,   -- Points scored (>=0)
    rebounds        INTEGER NOT NULL,   -- Total rebounds (>=0)
    assists         INTEGER NOT NULL,   -- Assists (>=0)
    steals          INTEGER NOT NULL,   -- Steals (>=0)
    blocks          INTEGER NOT NULL,   -- Blocks (>=0)
    turnovers       INTEGER NOT NULL,   -- Turnovers (>=0)

    -- Shooting stats (nullable — not always available)
    field_goals_made        INTEGER,    -- Field goals made
    field_goals_attempted   INTEGER,    -- Field goals attempted
    three_pointers_made     INTEGER,    -- Three-point field goals made
    three_pointers_attempted INTEGER,   -- Three-point field goals attempted
    free_throws_made        INTEGER,    -- Free throws made
    free_throws_attempted   INTEGER,    -- Free throws attempted

    -- Minutes
    minutes_played  DOUBLE,             -- Minutes played (float for partial minutes)

    -- Gold-layer computed advanced metrics
    efficiency_rating          DOUBLE,  -- Player efficiency rating (PER-like metric)
    true_shooting_percentage   DOUBLE,  -- True shooting percentage (0-1 range)
    usage_rate                 DOUBLE,  -- Usage rate percentage (0-1 range)
    plus_minus                 INTEGER, -- Plus/minus rating (can be negative)

    -- Composite primary key: one row per player per game
    PRIMARY KEY (player_id, game_id)
);


-- =============================================================================
-- Table: team_daily_stats
-- Source: GoldTeamDailyStats (gold_models.py)
-- Description: Per-game team statistics with Gold-layer computed ratings.
--   One row per team per game.
-- =============================================================================
CREATE TABLE IF NOT EXISTS team_daily_stats (
    -- Identity & context
    team_id         VARCHAR NOT NULL,   -- Unique team identifier (NBA API string ID)
    team_name       VARCHAR NOT NULL,   -- Team display name (e.g., 'Los Angeles Lakers')
    game_id         VARCHAR,            -- Unique game identifier
    game_date       DATE,               -- Game date (DuckDB native DATE)
    season          VARCHAR,            -- NBA season identifier (e.g., '2023-24')

    -- Core team stats
    points                  INTEGER NOT NULL,   -- Total points scored (>=0)
    field_goals_made        INTEGER NOT NULL,   -- Total field goals made (>=0)
    field_goals_attempted   INTEGER NOT NULL,   -- Total field goals attempted (>=0)
    three_pointers_made     INTEGER,            -- Total three-pointers made
    three_pointers_attempted INTEGER,           -- Total three-pointers attempted
    free_throws_made        INTEGER,            -- Total free throws made
    free_throws_attempted   INTEGER,            -- Total free throws attempted
    rebounds                INTEGER NOT NULL,   -- Total rebounds (>=0)
    assists                 INTEGER NOT NULL,   -- Total assists (>=0)
    steals                  INTEGER,            -- Total steals
    blocks                  INTEGER,            -- Total blocks
    turnovers               INTEGER,            -- Total turnovers
    fouls                   INTEGER,            -- Total fouls

    -- Gold-layer computed metrics
    offensive_rating           DOUBLE,  -- Offensive rating (points per 100 possessions)
    defensive_rating           DOUBLE,  -- Defensive rating (opponent points per 100 possessions)
    pace                       DOUBLE,  -- Pace (possessions per 48 minutes)
    true_shooting_percentage   DOUBLE,  -- Team true shooting percentage (0-1 range)

    -- Game context
    opponent_team_id   VARCHAR,         -- Opponent team identifier
    home_game          BOOLEAN,         -- Whether this was a home game
    win                BOOLEAN,         -- Whether the team won

    -- Composite primary key: one row per team per game
    PRIMARY KEY (team_id, game_id)
);


-- =============================================================================
-- Table: player_season_summary
-- Source: GoldPlayerSeasonSummary (gold_models.py)
-- Description: Season-aggregated player statistics with per-game averages,
--   shooting percentages, advanced metrics, and performance trends.
--   One row per player per season.
-- =============================================================================
CREATE TABLE IF NOT EXISTS player_season_summary (
    -- Identity & context
    player_id       VARCHAR NOT NULL,   -- Unique player identifier
    player_name     VARCHAR,            -- Player display name
    season          VARCHAR NOT NULL,   -- NBA season identifier (e.g., '2023-24')
    team            VARCHAR,            -- Primary team for the season

    -- Season totals
    total_games     INTEGER NOT NULL,   -- Total games played (>=0)
    total_minutes   DOUBLE  NOT NULL,   -- Total minutes played (>=0)

    -- Per-game averages
    points_per_game     DOUBLE NOT NULL,    -- Points per game (>=0)
    rebounds_per_game   DOUBLE NOT NULL,    -- Rebounds per game (>=0)
    assists_per_game    DOUBLE NOT NULL,    -- Assists per game (>=0)
    steals_per_game     DOUBLE NOT NULL,    -- Steals per game (>=0)
    blocks_per_game     DOUBLE NOT NULL,    -- Blocks per game (>=0)
    turnovers_per_game  DOUBLE NOT NULL,    -- Turnovers per game (>=0)

    -- Season shooting percentages (nullable — may not be available)
    field_goal_percentage      DOUBLE,  -- Season FG% (0-1 range)
    three_point_percentage     DOUBLE,  -- Season 3P% (0-1 range)
    free_throw_percentage      DOUBLE,  -- Season FT% (0-1 range)

    -- Advanced metrics
    efficiency_rating          DOUBLE,  -- Season efficiency rating
    true_shooting_percentage   DOUBLE,  -- Season true shooting % (0-1 range)
    usage_rate                 DOUBLE,  -- Season usage rate (0-1 range)

    -- Performance trends (month-over-month changes)
    scoring_trend      DOUBLE,          -- Points per game trend (% change)
    efficiency_trend   DOUBLE,          -- Efficiency rating trend (% change)

    -- Composite primary key: one row per player per season
    PRIMARY KEY (player_id, season)
);


-- =============================================================================
-- Table: team_season_summary
-- Source: GoldTeamSeasonSummary (gold_models.py)
-- Description: Season-aggregated team statistics with per-game averages,
--   efficiency metrics, Four Factors, and shooting percentages.
--   One row per team per season.
-- =============================================================================
CREATE TABLE IF NOT EXISTS team_season_summary (
    -- Identity & context
    team_id         VARCHAR NOT NULL,   -- Unique team identifier
    team_name       VARCHAR,            -- Team display name
    season          VARCHAR NOT NULL,   -- NBA season identifier (e.g., '2023-24')
    season_type     VARCHAR,            -- Season type (e.g., 'regular', 'playoff')

    -- Season totals
    total_games          INTEGER NOT NULL,   -- Total games played (>=0)
    total_points         INTEGER NOT NULL,   -- Total points scored (>=0)
    total_points_allowed INTEGER NOT NULL,   -- Total points allowed (>=0)

    -- Per-game averages
    points_per_game          DOUBLE NOT NULL,    -- Points per game (>=0)
    points_allowed_per_game  DOUBLE NOT NULL,    -- Points allowed per game (>=0)
    assists_per_game         DOUBLE NOT NULL,    -- Assists per game (>=0)
    total_rebounds_per_game  DOUBLE NOT NULL,    -- Total rebounds per game (>=0)
    turnovers_per_game       DOUBLE NOT NULL,    -- Turnovers per game (>=0)

    -- Shooting percentages
    field_goal_percentage           DOUBLE, -- Season FG% (0-1 range)
    three_point_percentage          DOUBLE, -- Season 3P% (0-1 range)
    free_throw_percentage           DOUBLE, -- Season FT% (0-1 range)
    true_shooting_percentage        DOUBLE, -- Season TS% (0-1 range)
    effective_field_goal_percentage DOUBLE, -- Effective FG% (0-1 range)

    -- Efficiency metrics
    offensive_rating   DOUBLE,          -- Offensive rating (pts per 100 possessions)
    defensive_rating   DOUBLE,          -- Defensive rating (opponent points per 100 possessions)
    net_rating         DOUBLE,          -- Net rating (offensive - defensive)
    pace               DOUBLE,          -- Pace (possessions per 48 minutes)

    -- Four Factors
    turnover_percentage          DOUBLE, -- Turnover percentage (0-1 range)
    offensive_rebound_percentage DOUBLE, -- Offensive rebound percentage (0-1 range)
    free_throw_rate              DOUBLE, -- Free throw rate (FTA / FGA)

    -- Data quality
    data_quality_score   DOUBLE,        -- Data quality score (0-1 range)

    -- Composite primary key: one row per team per season
    PRIMARY KEY (team_id, season)
);


-- =============================================================================
-- Table: top_lists
-- Source: Top lists JSON artifacts (json_artifacts.py)
-- Description: Daily leaderboards by metric. Each row represents one player's
--   ranking in a specific metric on a specific date.
-- =============================================================================
CREATE TABLE IF NOT EXISTS top_lists (
    -- Leaderboard context
    metric          VARCHAR NOT NULL,   -- Metric name (e.g., 'Points Leaders')
    list_date       DATE    NOT NULL,   -- Date of the leaderboard (DuckDB native DATE)
    rank            INTEGER NOT NULL,   -- Player rank within the leaderboard (1-based)

    -- Player info
    player_id       VARCHAR NOT NULL,   -- Player identifier
    player_name     VARCHAR,            -- Player display name
    team            VARCHAR,            -- Team abbreviation

    -- Metric value
    value           DOUBLE  NOT NULL,   -- Metric value for this player on this date

    -- Composite primary key: one entry per metric per date per rank
    PRIMARY KEY (metric, list_date, rank)
);


-- =============================================================================
-- Indexes
-- =============================================================================
-- Optimized for the most common analytical query patterns:
--   1. Player lookup by date range (temporal analysis)
--   2. Date-based filtering ("all games on date X")
--   3. Season-scoped player queries
--   4. Team lookup by date range
--   5. Leaderboard-style queries (sorted by performance metrics)

-- player_daily_stats indexes
CREATE INDEX IF NOT EXISTS idx_pds_player_date
    ON player_daily_stats (player_id, game_date);

CREATE INDEX IF NOT EXISTS idx_pds_game_date
    ON player_daily_stats (game_date);

CREATE INDEX IF NOT EXISTS idx_pds_season_player
    ON player_daily_stats (season, player_id);

-- team_daily_stats indexes
CREATE INDEX IF NOT EXISTS idx_tds_team_date
    ON team_daily_stats (team_id, game_date);

CREATE INDEX IF NOT EXISTS idx_tds_game_date
    ON team_daily_stats (game_date);

-- player_season_summary indexes
CREATE INDEX IF NOT EXISTS idx_pss_season_player
    ON player_season_summary (season, player_id);

CREATE INDEX IF NOT EXISTS idx_pss_season_ppg
    ON player_season_summary (season, points_per_game DESC);

-- team_season_summary indexes
CREATE INDEX IF NOT EXISTS idx_tss_season_team
    ON team_season_summary (season, team_id);

-- top_lists indexes
CREATE INDEX IF NOT EXISTS idx_tl_date_metric
    ON top_lists (list_date, metric);


-- =============================================================================
-- Views
-- =============================================================================

-- -----------------------------------------------------------------------------
-- View: v_team_standings
-- Purpose: Team win/loss records with offensive/defensive ratings per season.
-- Compatibility: Works in both DuckDB and SQLite (uses standard SQL aggregates).
-- Usage: "Top 5 teams by offensive rating", "Team comparison queries"
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_team_standings AS
SELECT
    tds.team_id,
    tds.team_name,
    tds.season,
    COUNT(*)                                        AS games_played,
    SUM(CASE WHEN tds.win = TRUE THEN 1 ELSE 0 END)  AS wins,
    SUM(CASE WHEN tds.win = FALSE THEN 1 ELSE 0 END) AS losses,
    ROUND(AVG(tds.points), 1)                       AS avg_points,
    ROUND(AVG(tds.offensive_rating), 1)             AS avg_offensive_rating,
    ROUND(AVG(tds.defensive_rating), 1)             AS avg_defensive_rating,
    ROUND(AVG(tds.pace), 1)                         AS avg_pace
FROM team_daily_stats tds
WHERE tds.season IS NOT NULL
GROUP BY tds.team_id, tds.team_name, tds.season;


-- -----------------------------------------------------------------------------
-- View: v_player_current_averages
-- Purpose: Convenience view joining player season summary with their most recent
--   daily performance for quick "current form" lookups.
-- Compatibility: DuckDB only — uses window function ROW_NUMBER() with PARTITION BY.
-- Usage: "Player current averages with latest game stats"
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_player_current_averages AS
SELECT
    pss.player_id,
    pss.player_name,
    pss.season,
    pss.team,
    -- Season averages
    pss.total_games,
    pss.points_per_game,
    pss.rebounds_per_game,
    pss.assists_per_game,
    pss.steals_per_game,
    pss.blocks_per_game,
    pss.field_goal_percentage,
    pss.three_point_percentage,
    pss.free_throw_percentage,
    pss.efficiency_rating       AS season_efficiency_rating,
    pss.true_shooting_percentage AS season_true_shooting_pct,
    -- Latest game stats
    latest.game_date            AS latest_game_date,
    latest.points               AS latest_points,
    latest.rebounds              AS latest_rebounds,
    latest.assists               AS latest_assists,
    latest.efficiency_rating    AS latest_efficiency_rating,
    -- Trends
    pss.scoring_trend,
    pss.efficiency_trend
FROM player_season_summary pss
LEFT JOIN (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY player_id, season
            ORDER BY game_date DESC
        ) AS rn
    FROM player_daily_stats
) latest
    ON pss.player_id = latest.player_id
    AND pss.season = latest.season
    AND latest.rn = 1;


-- -----------------------------------------------------------------------------
-- View: v_player_game_log
-- Purpose: Enriched player game log with running averages over the last 10 games.
-- Compatibility: DuckDB only — uses window functions with ROWS BETWEEN.
-- Usage: "Player scoring trend over the last 10 games"
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_player_game_log AS
SELECT
    player_id,
    player_name,
    team,
    game_date,
    game_id,
    season,
    points,
    rebounds,
    assists,
    efficiency_rating,
    true_shooting_percentage,
    -- Rolling 10-game averages
    ROUND(AVG(points) OVER (
        PARTITION BY player_id, season
        ORDER BY game_date
        ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
    ), 1) AS rolling_10g_ppg,
    ROUND(AVG(rebounds) OVER (
        PARTITION BY player_id, season
        ORDER BY game_date
        ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
    ), 1) AS rolling_10g_rpg,
    ROUND(AVG(assists) OVER (
        PARTITION BY player_id, season
        ORDER BY game_date
        ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
    ), 1) AS rolling_10g_apg
FROM player_daily_stats;
