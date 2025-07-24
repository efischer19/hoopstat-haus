# Player Daily Aggregator

AWS Lambda function for aggregating player daily statistics from Silver to Gold layer.

## Overview

This Lambda function processes NBA player game statistics from the Silver layer and creates daily and season-to-date aggregations in the Gold layer. It is triggered by S3 events when new Silver layer data is available.

## Features

- **Daily Aggregations**: Points, rebounds, assists per game
- **Season-to-Date Statistics**: Cumulative season statistics
- **Shooting Percentages**: Field goal %, 3-point %, free throw %
- **Data Validation**: Basic row count and null value checks
- **Partitioned Output**: Parquet files partitioned by season/player_id

## Architecture

```
Silver Layer: s3://bucket/silver/player_games/season=2023/date=2024-01-15/
    ↓ [S3 Event Trigger]
Lambda Function: player_daily_aggregator
    ↓ [Transform Logic]
Gold Layer: s3://bucket/gold/player_daily_stats/season=2023/player_id=123/
```

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
- `SILVER_BUCKET`: S3 bucket containing Silver layer data
- `GOLD_BUCKET`: S3 bucket for Gold layer output
- `AWS_REGION`: AWS region for S3 operations

## Deployment

This function is designed to be deployed as an AWS Lambda with:
- Python 3.12 runtime
- S3 event trigger on Silver layer updates
- Appropriate IAM permissions for S3 read/write