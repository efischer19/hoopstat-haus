# Gold Analytics

Gold layer analytics processing for NBA statistics.

## Overview

This application processes Silver layer NBA data and transforms it into advanced analytics metrics. Per [ADR-028](../../meta/adr/ADR-028-gold_layer_final.md), internal Gold data is stored as Parquet and a public presentation layer should be produced as small JSON artifacts under a `served/` prefix.

**Note**: S3 Tables/Iceberg functionality has been removed per ADR-028. The application currently needs to be updated to write JSON artifacts to the `served/` prefix instead of Iceberg tables.

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

### Storage & Partitions (Target for v1)
- **Internal Parquet**: Partition by season/date/team_id/player_id to match access patterns
- **Public JSON Artifacts**: Small, versioned JSON files (≤100KB) for browser/app consumption (TODO: Not yet implemented)
- **Schema Evolution**: Versioned JSON schemas; Parquet schemas evolve with manifests

### Performance Features
- **Memory-Optimized Processing**: Streaming processing for Lambda constraints
- **Chunked Processing**: Large datasets split for optimal processing
- **Decimal Precision**: Proper data types for analytics percentages

### Data Flow (Target)
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

# Check status
poetry run start status
```

### Configuration

Environment variables:
- `SILVER_BUCKET`: S3 bucket containing Silver layer data
- `GOLD_BUCKET`: S3 bucket for Gold layer data (Parquet internal storage and JSON artifacts)

## Architecture

### Outputs (Target for v1)
```
Silver Parquet → Gold Parquet (internal) + JSON artifacts (served/) per ADR-028
```

**Current Status**: Analytics calculation logic exists, but storage layer needs to be implemented
to write JSON artifacts instead of S3 Tables/Iceberg.

### Lambda Deployment
```bash
# Build Docker image (from repo root)
docker build -f apps/gold-analytics/Dockerfile -t gold-analytics:dev .

# Deploy via Terraform (see infrastructure/)
```

### Lambda Deployment
```bash
# Build Docker image (from repo root)
docker build -f apps/gold-analytics/Dockerfile -t gold-analytics:dev .

# Deploy via Terraform (see infrastructure/)
```

## Public JSON Artifacts (TODO)

Per ADR-028, the Gold layer should serve public JSON artifacts for consumption:

- **Anonymous Read Access**: Small JSON payloads (≤100KB) under `served/` prefix
- **Low Latency**: CDN-cacheable, deterministic keys
- **Advanced Metrics**: Player efficiency, team ratings, season aggregations
- **Schema Versioned**: Documented JSON schemas for each artifact type

### Target Artifact Structure
```
s3://gold-bucket/served/
├── player_daily/{date}/{player_id}.json
├── team_daily/{date}/{team_id}.json
├── top_lists/{date}/{metric}.json
└── index/latest.json
```

**Current Status**: Artifact writing not yet implemented. S3 Tables/Iceberg functionality 
has been removed per ADR-028.

**Details**: See [ADR-028](../../meta/adr/ADR-028-gold_layer_final.md)

## Related

- [ADR-028: Gold Layer Architecture and Serving Strategy (Final)](../../meta/adr/ADR-028-gold_layer_final.md)
- [ADR-026: S3 Tables for Gold Layer Analytics](../../meta/adr/ADR-026-s3_tables_gold_layer.md) (Superseded)
- [Silver Processing App](../silver-processing/)