# Player Daily Statistics Aggregator

AWS Lambda function that aggregates Silver layer player game data into basic Gold layer daily statistics.

## Overview

This Lambda function implements the Silver-to-Gold ETL pattern defined in `meta/plans/silver-to-gold-etl-jobs.md`. It:

- Reads player game statistics from Silver layer S3 bucket
- Calculates basic daily aggregations (points, rebounds, assists)
- Computes simple shooting percentages (FG%, 3P%, FT%)
- Generates season-to-date cumulative statistics
- Writes partitioned Parquet files to Gold layer (by season/player_id)
- Provides row count and null value validation

## Architecture

- **Trigger**: S3 events from Silver layer updates
- **Input**: `s3://hoopstat-haus-silver/player_games/season=YYYY/date=YYYY-MM-DD/`
- **Output**: `s3://hoopstat-haus-gold/player_daily_stats/season=YYYY/player_id=XXX/`
- **Monitoring**: CloudWatch logs with structured JSON per ADR-015

## Dependencies

- `pandas`: Data manipulation and aggregation
- `pyarrow`: Parquet file processing per ADR-014
- `boto3`: AWS S3 operations
- `hoopstat-data`: Shared data models and validation
- `hoopstat-observability`: Structured logging per ADR-015

## Deployment

Deployed via Terraform as part of the main infrastructure. See `infrastructure/main.tf` for Lambda configuration.

## Testing

```bash
poetry run pytest -v
```