# Gold Analytics

Gold layer analytics processing for NBA statistics.

## Overview

This application processes Silver layer NBA data and transforms it into advanced analytics metrics. Per [ADR-028](../../meta/adr/ADR-028-gold_layer_final.md), internal Gold data is stored as Parquet and a public presentation layer is produced as small JSON artifacts under a `served/` prefix.

## Trigger Mechanism

Gold processing is triggered by **silver-ready markers** written by the Silver layer (ADR-028). This ensures Gold runs exactly once per day after all Silver data for a date is ready:

- **Marker Path**: `metadata/{YYYY-MM-DD}/silver-ready.json`
- **Trigger**: S3 event notification on marker creation
- **Processing**: Idempotent - safe under retries/duplicate events
- **Benefit**: Prevents over-invocation (previously triggered on every Silver file write)

## Features

### Analytics Metrics
- **Player Analytics**: True Shooting %, Player Efficiency Rating, Usage Rate, Effective FG%
- **Team Analytics**: Offensive/Defensive Rating, Pace, Net Rating, Four Factors
- **Season Aggregations**: Full season summaries for players and teams

### Storage & Partitions
- **Internal Parquet**: Partition by season/date/team_id/player_id to match access patterns
- **Public JSON Artifacts**: Small JSON files (≤100KB each) served via the `served/` prefix for browser/app consumption, validated by Pydantic models (`GoldPlayerDailyStats`, `GoldTeamDailyStats`, `GoldPlayerSeasonSummary`, `GoldTeamSeasonSummary`)
- **Schema Evolution**: Versioned JSON schemas backed by Pydantic; Parquet schemas evolve with manifests

### Performance Features
- **Memory-Optimized Processing**: Streaming processing for Lambda constraints
- **Chunked Processing**: Large datasets split for optimal processing
- **Decimal Precision**: Proper data types for analytics percentages

### Data Flow
```
Silver S3 (Parquet) → Gold Lambda → Gold S3 Parquet (internal) + JSON artifacts (served/)
```

## Development

### Prerequisites
- Python 3.12+
- Poetry
- AWS CLI configured

### Setup
```bash
# Install dependencies
poetry install

# Run linting and formatting
poetry run ruff format .
poetry run ruff check .

# Run tests
poetry run pytest
```

### Local Testing
```bash
# Process a specific date (dry run)
poetry run start process --date 2024-01-15 --dry-run

# Process player season aggregation
poetry run start season-players --season 2023-24 --dry-run

# Process team season aggregation
poetry run start season-teams --season 2023-24 --dry-run

# Process specific player or team
poetry run start season-players --season 2023-24 --player-id 2544 --dry-run
poetry run start season-teams --season 2023-24 --team-id 1610612747 --dry-run

# Process a date range
poetry run start process-range --start-date 2024-01-10 --end-date 2024-01-15 --dry-run

# Incremental processing (discovers new data from last 7 days)
poetry run start incremental --dry-run

# Check status
poetry run start status
```

### Configuration

Environment variables:
- `SILVER_BUCKET`: S3 bucket containing Silver layer data
- `GOLD_BUCKET`: S3 bucket for Gold layer data (Parquet internal storage and JSON artifacts)

## Architecture

### Outputs
```
Silver Parquet → Gold Parquet (internal) + JSON artifacts (served/) per ADR-028
```

JSON artifacts are written to the `served/` prefix for player daily stats, team daily stats, top lists, player season summaries, team season summaries, and the latest index.

### Lambda Deployment
```bash
# Build Docker image (from repo root)
docker build -f apps/gold-analytics/Dockerfile -t gold-analytics:dev .

# Deploy via Terraform (see infrastructure/)
```

## Public JSON Artifacts

Per [ADR-028](../../meta/adr/ADR-028-gold_layer_final.md), the Gold layer produces public JSON artifacts for consumption by the frontend app, MCP tools, and external clients:

- **Anonymous Read Access**: Small JSON payloads (≤100KB) under `served/` prefix with CORS enabled
- **CDN-Cacheable**: Deterministic keys with differentiated Cache-Control headers per [ADR-038](../../meta/adr/ADR-038-cloudfront-cache-tuning.md)
- **Advanced Metrics**: Player efficiency, team ratings, top-list leaderboards, season aggregations
- **Schema Validated**: Every artifact is serialized through Pydantic models for type safety and consistent structure

### Artifact Structure
```
s3://gold-bucket/served/
├── player_daily/{date}/{player_id}.json     # Per-player game stats + advanced metrics
├── team_daily/{date}/{team_id}.json         # Per-team game stats + advanced metrics
├── top_lists/{date}/{metric}.json           # Daily leaderboards (top 10)
├── season_player/{season}/{player_id}.json  # Player full-season aggregation
├── season_team/{season}/{team_id}.json      # Team full-season aggregation
└── index/latest.json                        # Discovery index for latest data
```

#### Example Artifact Keys

| Artifact Type | Example Key | Description |
|---|---|---|
| Player Daily | `served/player_daily/2024-01-15/2544.json` | LeBron James box score + analytics for Jan 15 |
| Team Daily | `served/team_daily/2024-01-15/1610612747.json` | Lakers game stats + analytics for Jan 15 |
| Top List | `served/top_lists/2024-01-15/points.json` | Points leaders for Jan 15 |
| Player Season | `served/season_player/2023-24/2544.json` | LeBron James 2023-24 season summary |
| Team Season | `served/season_team/2023-24/1610612747.json` | Lakers 2023-24 season summary |
| Index | `served/index/latest.json` | Latest data pointers for client discovery |

### Example JSON Structures

**Player Daily** (`served/player_daily/2024-01-15/2544.json`):
```json
{
  "player_id": "2544",
  "player_name": "LeBron James",
  "team": "LAL",
  "position": "SF",
  "points": 30,
  "rebounds": 8,
  "assists": 11,
  "steals": 2,
  "blocks": 1,
  "turnovers": 3,
  "field_goals_made": 12,
  "field_goals_attempted": 22,
  "three_pointers_made": 3,
  "three_pointers_attempted": 7,
  "free_throws_made": 3,
  "free_throws_attempted": 4,
  "minutes_played": 36.5,
  "game_id": "0022300123",
  "game_date": "2024-01-15",
  "season": "2023-24",
  "efficiency_rating": 38.5,
  "true_shooting_percentage": 0.632,
  "usage_rate": 0.31
}
```

**Team Daily** (`served/team_daily/2024-01-15/1610612747.json`):
```json
{
  "team_id": "1610612747",
  "team_name": "Los Angeles Lakers",
  "game_id": "0022300123",
  "game_date": "2024-01-15",
  "season": "2023-24",
  "points": 118,
  "field_goals_made": 44,
  "field_goals_attempted": 89,
  "three_pointers_made": 12,
  "three_pointers_attempted": 33,
  "rebounds": 45,
  "assists": 28,
  "turnovers": 14,
  "offensive_rating": 115.2,
  "defensive_rating": 108.7,
  "pace": 100.3,
  "true_shooting_percentage": 0.587,
  "opponent_team_id": "1610612738",
  "home_game": true,
  "win": true
}
```

**Top List** (`served/top_lists/2024-01-15/points.json`, truncated to 2 of 10 entries):
```json
{
  "metric": "Points Leaders",
  "date": "2024-01-15",
  "players": [
    {
      "rank": 1,
      "player_id": "201566",
      "player_name": "Russell Westbrook",
      "team": "LAC",
      "value": 45.0
    },
    {
      "rank": 2,
      "player_id": "2544",
      "player_name": "LeBron James",
      "team": "LAL",
      "value": 30.0
    }
  ]
}
```

Available top-list metrics: `points`, `efficiency_rating`, `true_shooting_percentage`, `assists`, `rebounds` (each list contains the top 10 players for that date).

**Player Season** (`served/season_player/2023-24/2544.json`):
```json
{
  "player_id": "2544",
  "player_name": "LeBron James",
  "season": "2023-24",
  "team": "LAL",
  "total_games": 71,
  "total_minutes": 2475.0,
  "points_per_game": 25.7,
  "rebounds_per_game": 7.3,
  "assists_per_game": 8.3,
  "steals_per_game": 1.3,
  "blocks_per_game": 0.5,
  "turnovers_per_game": 3.5,
  "field_goal_percentage": 0.54,
  "three_point_percentage": 0.41,
  "free_throw_percentage": 0.75,
  "efficiency_rating": 32.1,
  "true_shooting_percentage": 0.63,
  "usage_rate": 0.30,
  "scoring_trend": 0.02,
  "efficiency_trend": 0.01
}
```

**Team Season** (`served/season_team/2023-24/1610612747.json`):
```json
{
  "team_id": "1610612747",
  "team_name": "Los Angeles Lakers",
  "season": "2023-24",
  "total_games": 82,
  "total_points": 9430,
  "total_points_allowed": 9280,
  "points_per_game": 115.0,
  "points_allowed_per_game": 113.2,
  "assists_per_game": 27.1,
  "total_rebounds_per_game": 44.5,
  "turnovers_per_game": 13.8,
  "field_goal_percentage": 0.48,
  "three_point_percentage": 0.37,
  "free_throw_percentage": 0.78,
  "offensive_rating": 115.0,
  "defensive_rating": 113.2,
  "net_rating": 1.8,
  "pace": 100.1
}
```

**Index** (`served/index/latest.json`):
```json
{
  "latest_date": "2024-01-15",
  "available_data": {
    "player_daily": "served/player_daily/2024-01-15/",
    "team_daily": "served/team_daily/2024-01-15/",
    "top_lists": "served/top_lists/2024-01-15/"
  },
  "updated_at": "2024-01-15"
}
```

### Cache-Control Strategy

Per [ADR-038](../../meta/adr/ADR-038-cloudfront-cache-tuning.md), artifacts use differentiated caching based on data mutability:

| Path Pattern | Cache-Control | TTL | Reason |
|---|---|---|---|
| `served/index/*` | `public, max-age=300` | 5 minutes | Must stay fresh so clients discover newly published data |
| `served/player_daily/*` | `public, max-age=31536000, immutable` | 1 year | Game data is immutable once published |
| `served/team_daily/*` | `public, max-age=31536000, immutable` | 1 year | Game data is immutable once published |
| `served/top_lists/*` | `public, max-age=31536000, immutable` | 1 year | Game data is immutable once published |
| `served/season_player/*` | `public, max-age=31536000, immutable` | 1 year | Season data is immutable once published |
| `served/season_team/*` | `public, max-age=31536000, immutable` | 1 year | Season data is immutable once published |

Cache-Control headers are set at two layers for defense in depth:
1. **S3 object metadata** — `JSONArtifactWriter` sets `CacheControl` per-object at upload time
2. **CloudFront response headers policies** — Edge-level fallback with `override = false` so S3 headers take precedence

### Status Command

The `status` command (`poetry run start status`) validates the Gold layer artifact pipeline:

1. **Artifact prefixes** — Lists all `served/` sub-prefixes to confirm artifact types are present
2. **Index file** — Fetches and parses `served/index/latest.json`, reporting the latest date
3. **Artifact counts** — Counts objects under each artifact type (`player_daily`, `team_daily`, `top_lists`)

If any check fails (missing prefixes, unparseable index, S3 errors), the command exits with a non-zero status code.

## Related

- [ADR-028: Gold Layer Architecture and Serving Strategy (Final)](../../meta/adr/ADR-028-gold_layer_final.md)
- [ADR-038: CloudFront Cache Tuning for Immutable Historical Data](../../meta/adr/ADR-038-cloudfront-cache-tuning.md)
- [Silver Processing App](../silver-processing/)