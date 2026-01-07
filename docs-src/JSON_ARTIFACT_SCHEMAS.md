# JSON Artifact Schemas for Static Data

**Status:** v1 (Current)  
**Last Updated:** 2025-12-27  
**Related ADRs:** [ADR-027](../meta/adr/ADR-027-hybrid_gold_architecture.md), [ADR-028](../meta/adr/ADR-028-gold_layer_final.md)

## Overview

This document defines the data contracts, schemas, and constraints for static JSON artifacts that are consumed directly by browsers and mobile apps. These artifacts are pre-computed from Gold layer analytics and served via S3 with public read access.

## Design Principles

1. **Simplicity First:** Flat structures with minimal nesting for easy consumption
2. **Self-Contained:** Include human-readable fields to minimize client-side lookups
3. **Size Constrained:** All artifacts must be ≤100KB to ensure fast delivery
4. **Versioned:** All schemas include explicit version fields for evolution
5. **Browser-Friendly:** Direct consumption via HTTPS GET with CORS support

## Schema Versioning Strategy

### Version Format
All JSON artifacts include a `schema_version` field using semantic versioning:
- Format: `v{major}` (e.g., `v1`, `v2`)
- Current version: `v1`

### Version Evolution Rules
1. **Breaking changes** require a new major version (v1 → v2)
   - Removing required fields
   - Changing field types
   - Restructuring nested objects
2. **Non-breaking changes** can be added to existing versions
   - Adding optional fields
   - Expanding enum values
   - Adding metadata fields
3. **Backward compatibility:** Clients should gracefully handle unknown optional fields

### Version Migration Strategy
- **Version identification:** Clients rely on the `schema_version` field within each JSON artifact
- **Path-based versioning (future):** If needed, new major versions may use separate S3 paths (e.g., `served/v2/...`)
- **For v1:** All artifacts use paths without version prefix (e.g., `served/player_daily/...`) as specified in ADR-028
- **Backward compatibility:** Old schema versions remain available during migration periods

## Size Limit: ≤100KB Per Artifact

### Rationale
1. **Performance:** Ensures fast download over mobile networks (<1 second on 3G)
2. **CDN Efficiency:** Fits within typical CDN cache size sweet spots
3. **Memory Constraints:** Fits comfortably in browser/mobile app memory
4. **Cost Control:** Minimizes S3 data transfer and storage costs

### Size Enforcement
- Gold analytics processor validates artifact size before upload
- Artifacts exceeding 100KB are rejected with error logging
- For data that naturally exceeds 100KB, use pagination or date-based splitting

### Size Estimation Guide
| Artifact Type | Typical Size | Max Records |
|--------------|--------------|-------------|
| `player_daily` | 2-5KB | 1 player, 1 date |
| `team_daily` | 3-6KB | 1 team, 1 date |
| `top_lists` | 15-30KB | ~100 players |

## Artifact Type: `player_daily`

### Purpose
Daily player performance statistics with advanced analytics for a single player on a specific date.

### S3 Path Pattern
```
served/player_daily/{date}/{player_id}.json
```
Example: `served/player_daily/2024-11-15/2544.json`

**Note:** Path follows ADR-028 specification. Version identification is via `schema_version` field in JSON.

### Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "schema_version",
    "player_id",
    "player_name",
    "team_id",
    "team_abbr",
    "game_date",
    "opponent_team_id",
    "opponent_abbr",
    "is_home",
    "minutes_played",
    "points",
    "rebounds",
    "assists",
    "field_goals_made",
    "field_goals_attempted",
    "three_pointers_made",
    "three_pointers_attempted",
    "free_throws_made",
    "free_throws_attempted"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "enum": ["v1"],
      "description": "Schema version for this artifact"
    },
    "player_id": {
      "type": "string",
      "description": "NBA player ID"
    },
    "player_name": {
      "type": "string",
      "description": "Human-readable player name (e.g., 'LeBron James')"
    },
    "team_id": {
      "type": "string",
      "description": "NBA team ID for player's team"
    },
    "team_abbr": {
      "type": "string",
      "minLength": 2,
      "maxLength": 3,
      "description": "Team abbreviation (e.g., 'LAL', 'BOS')"
    },
    "game_date": {
      "type": "string",
      "format": "date",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
      "description": "Game date in ISO 8601 format (YYYY-MM-DD)"
    },
    "opponent_team_id": {
      "type": "string",
      "description": "NBA team ID for opponent"
    },
    "opponent_abbr": {
      "type": "string",
      "minLength": 2,
      "maxLength": 3,
      "description": "Opponent team abbreviation"
    },
    "is_home": {
      "type": "boolean",
      "description": "True if player's team was home team"
    },
    "minutes_played": {
      "type": "number",
      "minimum": 0,
      "maximum": 60,
      "description": "Minutes played in game"
    },
    "points": {
      "type": "integer",
      "minimum": 0,
      "description": "Total points scored"
    },
    "rebounds": {
      "type": "integer",
      "minimum": 0,
      "description": "Total rebounds (offensive + defensive)"
    },
    "assists": {
      "type": "integer",
      "minimum": 0,
      "description": "Total assists"
    },
    "steals": {
      "type": "integer",
      "minimum": 0,
      "description": "Total steals"
    },
    "blocks": {
      "type": "integer",
      "minimum": 0,
      "description": "Total blocks"
    },
    "turnovers": {
      "type": "integer",
      "minimum": 0,
      "description": "Total turnovers"
    },
    "field_goals_made": {
      "type": "integer",
      "minimum": 0,
      "description": "Field goals made"
    },
    "field_goals_attempted": {
      "type": "integer",
      "minimum": 0,
      "description": "Field goals attempted"
    },
    "three_pointers_made": {
      "type": "integer",
      "minimum": 0,
      "description": "Three-pointers made"
    },
    "three_pointers_attempted": {
      "type": "integer",
      "minimum": 0,
      "description": "Three-pointers attempted"
    },
    "free_throws_made": {
      "type": "integer",
      "minimum": 0,
      "description": "Free throws made"
    },
    "free_throws_attempted": {
      "type": "integer",
      "minimum": 0,
      "description": "Free throws attempted"
    },
    "field_goal_pct": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Field goal percentage (0.0 to 1.0)"
    },
    "three_point_pct": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Three-point percentage (0.0 to 1.0)"
    },
    "free_throw_pct": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Free throw percentage (0.0 to 1.0)"
    },
    "true_shooting_pct": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "True shooting percentage: Points / (2 * (FGA + 0.44 * FTA))"
    },
    "effective_field_goal_pct": {
      "type": "number",
      "minimum": 0,
      "maximum": 1.5,
      "description": "Effective FG%: (FGM + 0.5 * 3PM) / FGA"
    },
    "player_efficiency_rating": {
      "type": "number",
      "description": "Simplified PER: (PTS + REB + AST + STL + BLK - TOV) / MIN"
    },
    "plus_minus": {
      "type": "integer",
      "description": "Plus/minus for the game (optional, may be null)"
    },
    "game_id": {
      "type": "string",
      "description": "NBA game ID"
    },
    "season": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}$",
      "description": "NBA season (e.g., '2024-25')"
    }
  },
  "additionalProperties": false
}
```

### Required vs Optional Fields

**Required (Must be present in all artifacts):**
- `schema_version`, `player_id`, `player_name`, `team_id`, `team_abbr`
- `game_date`, `opponent_team_id`, `opponent_abbr`, `is_home`
- `minutes_played`, `points`, `rebounds`, `assists`
- Core shooting stats: `field_goals_made`, `field_goals_attempted`, `three_pointers_made`, `three_pointers_attempted`, `free_throws_made`, `free_throws_attempted`

**Optional (May be computed if sufficient data):**
- `steals`, `blocks`, `turnovers`: Present if player had >0 minutes
- Percentages (`field_goal_pct`, `three_point_pct`, `free_throw_pct`): Computed if attempts > 0
- Advanced metrics (`true_shooting_pct`, `effective_field_goal_pct`, `player_efficiency_rating`): Computed if attempts > 0
- `plus_minus`: May be null if not available from source data
- `game_id`, `season`: Metadata fields for client-side filtering

### Example Payload

```json
{
  "schema_version": "v1",
  "player_id": "2544",
  "player_name": "LeBron James",
  "team_id": "1610612747",
  "team_abbr": "LAL",
  "game_date": "2024-11-15",
  "opponent_team_id": "1610612738",
  "opponent_abbr": "BOS",
  "is_home": true,
  "game_id": "0022400234",
  "season": "2024-25",
  "minutes_played": 35.5,
  "points": 28,
  "rebounds": 8,
  "assists": 7,
  "steals": 2,
  "blocks": 1,
  "turnovers": 3,
  "field_goals_made": 10,
  "field_goals_attempted": 18,
  "three_pointers_made": 3,
  "three_pointers_attempted": 8,
  "free_throws_made": 5,
  "free_throws_attempted": 6,
  "field_goal_pct": 0.556,
  "three_point_pct": 0.375,
  "free_throw_pct": 0.833,
  "true_shooting_pct": 0.608,
  "effective_field_goal_pct": 0.639,
  "player_efficiency_rating": 0.986,
  "plus_minus": 12
}
```

**Size:** ~650 bytes (well within 100KB limit)

## Artifact Type: `team_daily`

### Purpose
Daily team performance statistics with advanced analytics for a single team on a specific date.

### S3 Path Pattern
```
served/team_daily/{date}/{team_id}.json
```
Example: `served/team_daily/2024-11-15/1610612747.json`

**Note:** Path follows ADR-028 specification. Version identification is via `schema_version` field in JSON.

### Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "schema_version",
    "team_id",
    "team_abbr",
    "team_name",
    "game_date",
    "opponent_team_id",
    "opponent_abbr",
    "is_home",
    "win",
    "points",
    "points_allowed",
    "field_goals_made",
    "field_goals_attempted",
    "three_pointers_made",
    "three_pointers_attempted",
    "free_throws_made",
    "free_throws_attempted"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "enum": ["v1"],
      "description": "Schema version for this artifact"
    },
    "team_id": {
      "type": "string",
      "description": "NBA team ID"
    },
    "team_abbr": {
      "type": "string",
      "minLength": 2,
      "maxLength": 3,
      "description": "Team abbreviation (e.g., 'LAL', 'BOS')"
    },
    "team_name": {
      "type": "string",
      "description": "Human-readable team name (e.g., 'Los Angeles Lakers')"
    },
    "game_date": {
      "type": "string",
      "format": "date",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
      "description": "Game date in ISO 8601 format (YYYY-MM-DD)"
    },
    "opponent_team_id": {
      "type": "string",
      "description": "NBA team ID for opponent"
    },
    "opponent_abbr": {
      "type": "string",
      "minLength": 2,
      "maxLength": 3,
      "description": "Opponent team abbreviation"
    },
    "is_home": {
      "type": "boolean",
      "description": "True if team was home team"
    },
    "win": {
      "type": "boolean",
      "description": "True if team won the game"
    },
    "points": {
      "type": "integer",
      "minimum": 0,
      "description": "Total points scored by team"
    },
    "points_allowed": {
      "type": "integer",
      "minimum": 0,
      "description": "Total points allowed by team"
    },
    "field_goals_made": {
      "type": "integer",
      "minimum": 0,
      "description": "Field goals made"
    },
    "field_goals_attempted": {
      "type": "integer",
      "minimum": 0,
      "description": "Field goals attempted"
    },
    "three_pointers_made": {
      "type": "integer",
      "minimum": 0,
      "description": "Three-pointers made"
    },
    "three_pointers_attempted": {
      "type": "integer",
      "minimum": 0,
      "description": "Three-pointers attempted"
    },
    "free_throws_made": {
      "type": "integer",
      "minimum": 0,
      "description": "Free throws made"
    },
    "free_throws_attempted": {
      "type": "integer",
      "minimum": 0,
      "description": "Free throws attempted"
    },
    "offensive_rebounds": {
      "type": "integer",
      "minimum": 0,
      "description": "Offensive rebounds"
    },
    "defensive_rebounds": {
      "type": "integer",
      "minimum": 0,
      "description": "Defensive rebounds"
    },
    "total_rebounds": {
      "type": "integer",
      "minimum": 0,
      "description": "Total rebounds"
    },
    "assists": {
      "type": "integer",
      "minimum": 0,
      "description": "Total assists"
    },
    "steals": {
      "type": "integer",
      "minimum": 0,
      "description": "Total steals"
    },
    "blocks": {
      "type": "integer",
      "minimum": 0,
      "description": "Total blocks"
    },
    "turnovers": {
      "type": "integer",
      "minimum": 0,
      "description": "Total turnovers"
    },
    "field_goal_pct": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Field goal percentage (0.0 to 1.0)"
    },
    "three_point_pct": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Three-point percentage (0.0 to 1.0)"
    },
    "free_throw_pct": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Free throw percentage (0.0 to 1.0)"
    },
    "true_shooting_pct": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "True shooting percentage"
    },
    "effective_field_goal_pct": {
      "type": "number",
      "minimum": 0,
      "maximum": 1.5,
      "description": "Effective FG%: (FGM + 0.5 * 3PM) / FGA"
    },
    "possessions": {
      "type": "number",
      "minimum": 0,
      "description": "Estimated possessions: FGA - OREB + TOV + 0.44 * FTA"
    },
    "offensive_rating": {
      "type": "number",
      "minimum": 0,
      "description": "Points per 100 possessions"
    },
    "defensive_rating": {
      "type": "number",
      "minimum": 0,
      "description": "Points allowed per 100 possessions"
    },
    "net_rating": {
      "type": "number",
      "description": "Offensive rating - defensive rating"
    },
    "pace": {
      "type": "number",
      "minimum": 0,
      "description": "Estimated possessions per 48 minutes"
    },
    "turnover_rate": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "Turnover percentage of possessions"
    },
    "rebound_rate": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "Offensive rebound percentage"
    },
    "free_throw_rate": {
      "type": "number",
      "minimum": 0,
      "description": "Free throw attempts per field goal attempt"
    },
    "game_id": {
      "type": "string",
      "description": "NBA game ID"
    },
    "season": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}$",
      "description": "NBA season (e.g., '2024-25')"
    }
  },
  "additionalProperties": false
}
```

### Required vs Optional Fields

**Required (Must be present in all artifacts):**
- `schema_version`, `team_id`, `team_abbr`, `team_name`
- `game_date`, `opponent_team_id`, `opponent_abbr`, `is_home`, `win`
- `points`, `points_allowed`
- Core shooting stats: `field_goals_made`, `field_goals_attempted`, `three_pointers_made`, `three_pointers_attempted`, `free_throws_made`, `free_throws_attempted`

**Optional (May be computed if sufficient data):**
- Box score totals: `offensive_rebounds`, `defensive_rebounds`, `total_rebounds`, `assists`, `steals`, `blocks`, `turnovers`
- Percentages: `field_goal_pct`, `three_point_pct`, `free_throw_pct`
- Advanced metrics: `true_shooting_pct`, `effective_field_goal_pct`, `possessions`, `offensive_rating`, `defensive_rating`, `net_rating`, `pace`, `turnover_rate`, `rebound_rate`, `free_throw_rate`
- Metadata: `game_id`, `season`

### Example Payload

```json
{
  "schema_version": "v1",
  "team_id": "1610612747",
  "team_abbr": "LAL",
  "team_name": "Los Angeles Lakers",
  "game_date": "2024-11-15",
  "opponent_team_id": "1610612738",
  "opponent_abbr": "BOS",
  "is_home": true,
  "win": false,
  "game_id": "0022400234",
  "season": "2024-25",
  "points": 108,
  "points_allowed": 115,
  "field_goals_made": 40,
  "field_goals_attempted": 88,
  "three_pointers_made": 12,
  "three_pointers_attempted": 35,
  "free_throws_made": 16,
  "free_throws_attempted": 20,
  "offensive_rebounds": 10,
  "defensive_rebounds": 34,
  "total_rebounds": 44,
  "assists": 24,
  "steals": 8,
  "blocks": 5,
  "turnovers": 14,
  "field_goal_pct": 0.455,
  "three_point_pct": 0.343,
  "free_throw_pct": 0.800,
  "true_shooting_pct": 0.548,
  "effective_field_goal_pct": 0.523,
  "possessions": 98.8,
  "offensive_rating": 109.3,
  "defensive_rating": 116.4,
  "net_rating": -7.1,
  "pace": 99.5,
  "turnover_rate": 14.2,
  "rebound_rate": 12.8,
  "free_throw_rate": 0.227
}
```

**Size:** ~900 bytes (well within 100KB limit)

## Artifact Type: `top_lists`

### Purpose
Ranked lists of top performers by specific metrics for a given date or time period.

### S3 Path Pattern
```
served/top_lists/{date}/{metric}.json
```
Examples:
- `served/top_lists/2024-11-15/top_scorers.json`
- `served/top_lists/2024-11-15/top_efficiency.json`
- `served/top_lists/2024-11-15/top_true_shooting.json`

**Note:** Path follows ADR-028 specification. Version identification is via `schema_version` field in JSON.

### Supported Metrics
- `top_scorers`: Top points scorers
- `top_efficiency`: Top player efficiency rating
- `top_true_shooting`: Top true shooting percentage
- `top_assists`: Top assists leaders
- `top_rebounds`: Top rebounders
- `top_blocks`: Top shot blockers
- `top_steals`: Top steals leaders
- `top_three_pointers`: Top three-point makers

### Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "schema_version",
    "metric",
    "date",
    "top_performers"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "enum": ["v1"],
      "description": "Schema version for this artifact"
    },
    "metric": {
      "type": "string",
      "enum": [
        "top_scorers",
        "top_efficiency",
        "top_true_shooting",
        "top_assists",
        "top_rebounds",
        "top_blocks",
        "top_steals",
        "top_three_pointers"
      ],
      "description": "The metric being ranked"
    },
    "date": {
      "type": "string",
      "format": "date",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
      "description": "Date for this leaderboard (YYYY-MM-DD)"
    },
    "season": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}$",
      "description": "NBA season (e.g., '2024-25')"
    },
    "top_performers": {
      "type": "array",
      "minItems": 1,
      "maxItems": 100,
      "description": "Ranked list of top performers (max 100)",
      "items": {
        "type": "object",
        "required": [
          "rank",
          "player_id",
          "player_name",
          "team_abbr",
          "value"
        ],
        "properties": {
          "rank": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "description": "Ranking position (1 = best)"
          },
          "player_id": {
            "type": "string",
            "description": "NBA player ID"
          },
          "player_name": {
            "type": "string",
            "description": "Human-readable player name"
          },
          "team_id": {
            "type": "string",
            "description": "NBA team ID"
          },
          "team_abbr": {
            "type": "string",
            "minLength": 2,
            "maxLength": 3,
            "description": "Team abbreviation"
          },
          "value": {
            "type": "number",
            "description": "The metric value for this player"
          },
          "game_date": {
            "type": "string",
            "format": "date",
            "description": "Game date for this performance"
          },
          "minutes_played": {
            "type": "number",
            "description": "Minutes played in the game"
          },
          "points": {
            "type": "integer",
            "description": "Points scored (for context)"
          },
          "assists": {
            "type": "integer",
            "description": "Assists (for context)"
          },
          "rebounds": {
            "type": "integer",
            "description": "Rebounds (for context)"
          }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

### Required vs Optional Fields

**Top-Level Required:**
- `schema_version`, `metric`, `date`, `top_performers`

**Per-Performer Required:**
- `rank`, `player_id`, `player_name`, `team_abbr`, `value`

**Per-Performer Optional:**
- `team_id`: Team ID for lookups
- `game_date`: Specific game date if different from top-level date
- `minutes_played`, `points`, `assists`, `rebounds`: Contextual stats

### Example Payload

```json
{
  "schema_version": "v1",
  "metric": "top_scorers",
  "date": "2024-11-15",
  "season": "2024-25",
  "top_performers": [
    {
      "rank": 1,
      "player_id": "1629029",
      "player_name": "Luka Dončić",
      "team_id": "1610612742",
      "team_abbr": "DAL",
      "value": 42,
      "game_date": "2024-11-15",
      "minutes_played": 38.5,
      "points": 42,
      "assists": 10,
      "rebounds": 8
    },
    {
      "rank": 2,
      "player_id": "203507",
      "player_name": "Giannis Antetokounmpo",
      "team_id": "1610612749",
      "team_abbr": "MIL",
      "value": 38,
      "game_date": "2024-11-15",
      "minutes_played": 35.2,
      "points": 38,
      "assists": 6,
      "rebounds": 12
    },
    {
      "rank": 3,
      "player_id": "1630162",
      "player_name": "Anthony Edwards",
      "team_id": "1610612750",
      "team_abbr": "MIN",
      "value": 35,
      "game_date": "2024-11-15",
      "minutes_played": 37.0,
      "points": 35,
      "assists": 5,
      "rebounds": 7
    }
  ]
}
```

**Size for 100 players:** ~15-25KB (well within 100KB limit)

## Human-Readable Field Requirements

### Player Names
- **Format:** Full name with proper capitalization (e.g., "LeBron James", "Giannis Antetokounmpo")
- **Special Characters:** Preserve accents and diacritics (e.g., "Luka Dončić", "Nikola Jokić")
- **Purpose:** Direct display in UIs without additional lookups

### Team Abbreviations
- **Format:** 2-3 uppercase letters (e.g., "LAL", "BOS", "GSW")
- **Consistency:** Use official NBA team abbreviations
- **Purpose:** Compact display and filtering

### Team Names
- **Format:** Full official team name (e.g., "Los Angeles Lakers", "Boston Celtics")
- **Purpose:** Display in headers and titles

### Date Formats
- **Format:** ISO 8601 date strings: `YYYY-MM-DD`
- **Purpose:** Universal parsing and sorting across all platforms

### Numeric Precision
- **Percentages:** Store as decimals (0.0 to 1.0), display as percentages (multiply by 100)
- **Ratings:** Round to 1 decimal place for display
- **Counts:** Always integers for counting stats

## Access Patterns and CORS

### CloudFront Distribution
- **Access:** Public read via CloudFront distribution with Origin Access Control (OAC)
- **S3 Bucket:** Private (Block Public Access enabled); CloudFront OAC provides signed access
- **CORS:** Configured via CloudFront response headers policy to allow browser access from any origin
- **Cache-Control:** `max-age=3600` (1 hour) for recent data
- **Content-Type:** `application/json; charset=utf-8`

### Example CORS Configuration
CloudFront response headers policy:
```json
{
  "access_control_allow_credentials": false,
  "access_control_allow_headers": ["*"],
  "access_control_allow_methods": ["GET", "HEAD", "OPTIONS"],
  "access_control_allow_origins": ["*"],
  "access_control_max_age_sec": 3600
}
```

### URL Access Pattern
```
https://<cloudfront-domain>.cloudfront.net/{artifact_type}/{date}/{id}.json
```

Example:
```
https://<cloudfront-domain>.cloudfront.net/player_daily/2024-11-15/2544.json
```

**Note:** The exact CloudFront domain is available from the infrastructure Terraform outputs. See [PUBLIC_ACCESS_GUIDE.md](../infrastructure/PUBLIC_ACCESS_GUIDE.md) for details on retrieving the CloudFront URL.

## Discovery and Index Files

### Latest Data Index
**Path:** `served/index/latest.json`

**Purpose:** Help clients discover the most recent data available

```json
{
  "schema_version": "v1",
  "last_updated": "2024-11-15T23:30:00Z",
  "latest_date": "2024-11-15",
  "season": "2024-25",
  "available_artifacts": {
    "player_daily": {
      "last_date": "2024-11-15",
      "player_count": 420
    },
    "team_daily": {
      "last_date": "2024-11-15",
      "team_count": 30
    },
    "top_lists": {
      "last_date": "2024-11-15",
      "available_metrics": [
        "top_scorers",
        "top_efficiency",
        "top_true_shooting",
        "top_assists",
        "top_rebounds"
      ]
    }
  }
}
```

## Validation and Quality Assurance

### Pre-Upload Validation
Gold analytics processor must validate:
1. Schema compliance (all required fields present)
2. Size limit (artifact ≤100KB)
3. Data types match schema
4. Value ranges are valid (e.g., percentages 0-1)
5. Human-readable fields are populated

### Client-Side Validation
Frontend clients should:
1. Check `schema_version` field matches expected version
2. Handle missing optional fields gracefully
3. Validate date formats before parsing
4. Display error messages for malformed data

## Future Enhancements (Out of Scope for v1)

Potential future artifact types:
- `player_season_summary`: Full season aggregations per player
- `team_season_summary`: Full season aggregations per team
- `league_leaders`: Season-long leaderboards
- `matchup_history`: Head-to-head team comparison data
- `trending_players`: Players with recent performance changes

## References

- [ADR-027: Stateless Gold Access via JSON Artifacts](../meta/adr/ADR-027-hybrid_gold_architecture.md)
- [ADR-028: Gold Layer Architecture and Serving Strategy](../meta/adr/ADR-028-gold_layer_final.md)
- [Gold Layer Analytics Strategy](../meta/GOLD_LAYER_ANALYTICS_STRATEGY.md)
- [Development Philosophy](DEVELOPMENT_PHILOSOPHY.md)
