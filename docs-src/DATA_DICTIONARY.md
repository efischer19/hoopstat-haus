# Data Dictionary

> **Auto-generated** from Pydantic model definitions. Do not edit manually.
>
> Last updated: 2026-03-14 12:42 UTC

## Overview

This document describes all data models used in the Hoopstat Haus medallion data architecture. Models are organized by layer:

- **Common Models** -- Shared types used across layers (e.g., data lineage tracking)
- **Silver Layer** -- Cleaned and validated data models from the Bronze-to-Silver ETL
- **Gold Layer** -- Analytics-ready models with pre-computed metrics from the Silver-to-Gold ETL

---

## Common Models

### DataLineage

_Data lineage tracking information._

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `source_system` | `str` | Yes | -- | Source system that provided the data |
| `ingestion_timestamp` | `datetime` | No | -- | When data was ingested |
| `schema_version` | `str` | Yes | -- | Schema version used for validation |
| `transformation_stage` | `str` | Yes | -- | ETL stage (bronze/silver/gold) |
| `validation_mode` | `ValidationMode` | No | -- | Validation strictness level |

---

## Silver Layer Models

Cleaned and standardized models produced by the Bronze-to-Silver ETL pipeline.

### PlayerStats

_Player statistics data model._

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `lineage` | `DataLineage | None` | No | -- | Data lineage and metadata tracking |
| `player_id` | `str` | Yes | -- | Unique identifier for the player |
| `player_name` | `str | None` | No | -- | Player's name |
| `team` | `str | None` | No | -- | Player's team |
| `position` | `str | None` | No | -- | Player's position |
| `points` | `int` | Yes | ge=0 | Points scored |
| `rebounds` | `int` | Yes | ge=0 | Total rebounds |
| `assists` | `int` | Yes | ge=0 | Assists |
| `steals` | `int` | Yes | ge=0 | Steals |
| `blocks` | `int` | Yes | ge=0 | Blocks |
| `turnovers` | `int` | Yes | ge=0 | Turnovers |
| `field_goals_made` | `int | None` | No | ge=0 | Field goals made |
| `field_goals_attempted` | `int | None` | No | ge=0 | Field goals attempted |
| `three_pointers_made` | `int | None` | No | ge=0 | Three pointers made |
| `three_pointers_attempted` | `int | None` | No | ge=0 | Three pointers attempted |
| `free_throws_made` | `int | None` | No | ge=0 | Free throws made |
| `free_throws_attempted` | `int | None` | No | ge=0 | Free throws attempted |
| `minutes_played` | `float | None` | No | ge=0 | Minutes played |
| `game_id` | `str | None` | No | -- | Game identifier |

### TeamStats

_Team statistics data model._

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `lineage` | `DataLineage | None` | No | -- | Data lineage and metadata tracking |
| `team_id` | `str` | Yes | -- | Unique identifier for the team |
| `team_name` | `str` | Yes | -- | Team name |
| `points` | `int` | Yes | ge=0 | Total points scored |
| `field_goals_made` | `int` | Yes | ge=0 | Total field goals made |
| `field_goals_attempted` | `int` | Yes | ge=0 | Total field goals attempted |
| `three_pointers_made` | `int | None` | No | ge=0 | Total three pointers made |
| `three_pointers_attempted` | `int | None` | No | ge=0 | Total three pointers attempted |
| `free_throws_made` | `int | None` | No | ge=0 | Total free throws made |
| `free_throws_attempted` | `int | None` | No | ge=0 | Total free throws attempted |
| `rebounds` | `int` | Yes | ge=0 | Total rebounds |
| `assists` | `int` | Yes | ge=0 | Total assists |
| `steals` | `int | None` | No | ge=0 | Total steals |
| `blocks` | `int | None` | No | ge=0 | Total blocks |
| `turnovers` | `int | None` | No | ge=0 | Total turnovers |
| `fouls` | `int | None` | No | ge=0 | Total fouls |
| `game_id` | `str | None` | No | -- | Game identifier |

### GameStats

_Game statistics data model._

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `lineage` | `DataLineage | None` | No | -- | Data lineage and metadata tracking |
| `game_id` | `str` | Yes | -- | Unique identifier for the game |
| `home_team_id` | `str` | Yes | -- | Home team identifier |
| `away_team_id` | `str` | Yes | -- | Away team identifier |
| `home_score` | `int` | Yes | ge=0 | Home team final score |
| `away_score` | `int` | Yes | ge=0 | Away team final score |
| `season` | `str | None` | No | -- | Season identifier |
| `game_date` | `str | None` | No | -- | Game date (ISO format) |
| `venue` | `str | None` | No | -- | Game venue |
| `quarters` | `int | None` | No | ge=4, le=8 | Number of quarters/periods |
| `overtime` | `bool | None` | No | -- | Whether game went to overtime |

---

## Gold Layer Models

Analytics-ready models with pre-computed metrics produced by the Silver-to-Gold ETL pipeline.

### GoldPlayerDailyStats

_Gold layer player daily statistics with pre-computed metrics._

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `lineage` | `DataLineage | None` | No | -- | Data lineage and metadata tracking |
| `player_id` | `str` | Yes | -- | Unique identifier for the player |
| `player_name` | `str | None` | No | -- | Player's name |
| `team` | `str | None` | No | -- | Player's team |
| `position` | `str | None` | No | -- | Player's position |
| `points` | `int` | Yes | ge=0 | Points scored |
| `rebounds` | `int` | Yes | ge=0 | Total rebounds |
| `assists` | `int` | Yes | ge=0 | Assists |
| `steals` | `int` | Yes | ge=0 | Steals |
| `blocks` | `int` | Yes | ge=0 | Blocks |
| `turnovers` | `int` | Yes | ge=0 | Turnovers |
| `field_goals_made` | `int | None` | No | ge=0 | Field goals made |
| `field_goals_attempted` | `int | None` | No | ge=0 | Field goals attempted |
| `three_pointers_made` | `int | None` | No | ge=0 | Three pointers made |
| `three_pointers_attempted` | `int | None` | No | ge=0 | Three pointers attempted |
| `free_throws_made` | `int | None` | No | ge=0 | Free throws made |
| `free_throws_attempted` | `int | None` | No | ge=0 | Free throws attempted |
| `minutes_played` | `float | None` | No | ge=0 | Minutes played |
| `game_id` | `str | None` | No | -- | Game identifier |
| `game_date` | `str | None` | No | -- | Game date (YYYY-MM-DD) |
| `efficiency_rating` | `float | None` | No | -- | Player efficiency rating (PER-like metric) |
| `true_shooting_percentage` | `float | None` | No | ge=0, le=1 | True shooting percentage |
| `usage_rate` | `float | None` | No | ge=0, le=1 | Usage rate percentage |
| `plus_minus` | `int | None` | No | -- | Plus/minus rating |
| `partition_key` | `str | None` | No | -- | S3 partition key |
| `season` | `str | None` | No | -- | NBA season (e.g., '2023-24') |

### GoldPlayerSeasonSummary

_Gold layer player season summary with aggregated statistics._

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `lineage` | `DataLineage | None` | No | -- | Data lineage and metadata tracking |
| `player_id` | `str` | Yes | -- | Unique identifier for the player |
| `player_name` | `str | None` | No | -- | Player's name |
| `season` | `str` | Yes | -- | NBA season (e.g., '2023-24') |
| `team` | `str | None` | No | -- | Primary team for the season |
| `total_games` | `int` | Yes | ge=0 | Total games played |
| `total_minutes` | `float` | Yes | ge=0 | Total minutes played |
| `points_per_game` | `float` | Yes | ge=0 | Points per game |
| `rebounds_per_game` | `float` | Yes | ge=0 | Rebounds per game |
| `assists_per_game` | `float` | Yes | ge=0 | Assists per game |
| `steals_per_game` | `float` | Yes | ge=0 | Steals per game |
| `blocks_per_game` | `float` | Yes | ge=0 | Blocks per game |
| `turnovers_per_game` | `float` | Yes | ge=0 | Turnovers per game |
| `field_goal_percentage` | `float | None` | No | ge=0, le=1 | Season field goal percentage |
| `three_point_percentage` | `float | None` | No | ge=0, le=1 | Season three-point percentage |
| `free_throw_percentage` | `float | None` | No | ge=0, le=1 | Season free throw percentage |
| `efficiency_rating` | `float | None` | No | -- | Season efficiency rating |
| `true_shooting_percentage` | `float | None` | No | ge=0, le=1 | Season true shooting percentage |
| `usage_rate` | `float | None` | No | ge=0, le=1 | Season usage rate |
| `scoring_trend` | `float | None` | No | -- | Points per game trend (% change) |
| `efficiency_trend` | `float | None` | No | -- | Efficiency rating trend (% change) |
| `partition_key` | `str | None` | No | -- | S3 partition key |

### GoldTeamDailyStats

_Gold layer team daily statistics with computed metrics._

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `lineage` | `DataLineage | None` | No | -- | Data lineage and metadata tracking |
| `team_id` | `str` | Yes | -- | Unique identifier for the team |
| `team_name` | `str` | Yes | -- | Team name |
| `game_id` | `str | None` | No | -- | Game identifier |
| `game_date` | `str | None` | No | -- | Game date (YYYY-MM-DD) |
| `season` | `str | None` | No | -- | NBA season (e.g., '2023-24') |
| `points` | `int` | Yes | ge=0 | Total points scored |
| `field_goals_made` | `int` | Yes | ge=0 | Total field goals made |
| `field_goals_attempted` | `int` | Yes | ge=0 | Total field goals attempted |
| `three_pointers_made` | `int | None` | No | ge=0 | Total three pointers made |
| `three_pointers_attempted` | `int | None` | No | ge=0 | Total three pointers attempted |
| `free_throws_made` | `int | None` | No | ge=0 | Total free throws made |
| `free_throws_attempted` | `int | None` | No | ge=0 | Total free throws attempted |
| `rebounds` | `int` | Yes | ge=0 | Total rebounds |
| `assists` | `int` | Yes | ge=0 | Total assists |
| `steals` | `int | None` | No | ge=0 | Total steals |
| `blocks` | `int | None` | No | ge=0 | Total blocks |
| `turnovers` | `int | None` | No | ge=0 | Total turnovers |
| `fouls` | `int | None` | No | ge=0 | Total fouls |
| `offensive_rating` | `float | None` | No | -- | Offensive rating (points per 100 possessions) |
| `defensive_rating` | `float | None` | No | -- | Defensive rating (opponent points per 100 possessions) |
| `pace` | `float | None` | No | -- | Pace (possessions per 48 minutes) |
| `true_shooting_percentage` | `float | None` | No | ge=0, le=1 | Team true shooting percentage |
| `opponent_team_id` | `str | None` | No | -- | Opponent team identifier |
| `home_game` | `bool | None` | No | -- | Whether this was a home game |
| `win` | `bool | None` | No | -- | Whether the team won |
| `partition_key` | `str | None` | No | -- | S3 partition key |
