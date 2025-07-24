# Player Daily Aggregator

AWS Lambda function for aggregating player daily statistics from Silver to Gold layer.

## Overview

This Lambda function processes NBA player game statistics from the Silver layer and creates daily and season-to-date aggregations in the Gold layer. It is triggered by S3 events when new Silver layer data is available.

## Features

- **Daily Aggregations**: Points, rebounds, assists per game
- **Season-to-Date Statistics**: Cumulative season statistics
- **Shooting Percentages**: Field goal %, 3-point %, free throw %
- **Data Validation**: Basic row count and null value checks
- **Season Totals Validation**: Compares calculated season stats against Silver layer season totals for data integrity verification
- **Partitioned Output**: Parquet files partitioned by season/player_id

## Architecture

```
Silver Layer: s3://bucket/silver/player_games/season=2023/date=2024-01-15/
    ↓ [S3 Event Trigger]
Lambda Function: player_daily_aggregator
    ↓ [Transform Logic]
Gold Layer: s3://bucket/gold/player_daily_stats/season=2023/player_id=123/
```

## Season Totals Validation

The function includes an optional validation feature that compares calculated season statistics against existing Silver layer season totals. This provides data integrity verification by:

1. **Looking for Silver Layer Season Totals**: Searches for files in `silver/player_season_stats/season={season}/`
2. **Comparing Key Statistics**: Validates games played, points, rebounds, assists, shooting stats, etc.
3. **Logging Discrepancies**: Reports any differences above the configured tolerance level
4. **Non-Blocking Validation**: Validation failures are logged as warnings but don't halt processing

This feature can be enabled/disabled via the `ENABLE_SEASON_TOTALS_VALIDATION` environment variable and tolerance can be adjusted with `SEASON_TOTALS_TOLERANCE`.

## Data Flow

## Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Format code
poetry run ruff format .

# Lint code
poetry run ruff check .

# Run all CI checks
../../scripts/local-ci-check.sh .
```

## Configuration

The function uses environment variables for configuration:

### Required Configuration
- `SILVER_BUCKET`: S3 bucket containing Silver layer data
- `GOLD_BUCKET`: S3 bucket for Gold layer output

### Optional Configuration
- `AWS_REGION`: AWS region for S3 operations (default: us-east-1)
- `MAX_WORKERS`: Maximum number of worker threads (default: 4)
- `CHUNK_SIZE`: Data processing chunk size (default: 10000)
- `MIN_EXPECTED_PLAYERS`: Minimum expected players for validation (default: 1)
- `MAX_NULL_PERCENTAGE`: Maximum null percentage allowed (default: 0.1)

### Season Validation Configuration
- `ENABLE_SEASON_TOTALS_VALIDATION`: Enable validation against Silver layer season totals (default: true)
- `SEASON_TOTALS_TOLERANCE`: Tolerance for discrepancies as a decimal (default: 0.01 for 1%)

## Deployment

This function is designed to be deployed as an AWS Lambda with:
- Python 3.12 runtime
- S3 event trigger on Silver layer updates
- Appropriate IAM permissions for S3 read/write