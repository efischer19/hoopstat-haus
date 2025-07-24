# NBA Season Data Backfill Application

A containerized Python application for backfilling NBA 2024-25 season data from the NBA API to the Bronze layer S3 storage.

## Overview

This application implements a robust, resumable data backfill process that:
- Retrieves NBA 2024-25 season data from the NBA API using the nba-api library
- Stores data in Parquet format in S3 Bronze layer storage
- Implements respectful rate limiting (5 seconds between requests)
- Provides checkpoint-based resumability for long-running operations
- Includes comprehensive error handling and structured JSON logging

## Architecture

The application follows the project's architectural decisions:
- **ADR-006**: Docker containerization
- **ADR-013**: NBA API data source
- **ADR-014**: Parquet storage format
- **ADR-015**: JSON structured logging
- **ADR-009**: AWS S3 integration

## Configuration

The application is configured via environment variables:

```bash
# Required
AWS_REGION=us-east-1
S3_BUCKET_NAME=hoopstat-haus-bronze
SEASON=2024-25

# Optional
RATE_LIMIT_SECONDS=5
STATE_FILE_PREFIX=backfill-state
LOG_LEVEL=INFO
DRY_RUN=false
```

## Usage

### Docker Run

```bash
docker run --rm \
  -e AWS_REGION=us-east-1 \
  -e S3_BUCKET_NAME=hoopstat-haus-bronze \
  -e SEASON=2024-25 \
  nba-season-backfill:latest
```

### Development

```bash
# Install dependencies
poetry install

# Run locally
poetry run python -m app.main

# Run tests
poetry run pytest

# Check code quality
poetry run ruff format --check .
poetry run ruff check .
```

## Data Output

Data is stored in S3 with the following structure:

```
s3://hoopstat-haus-bronze/
├── historical-backfill/
│   ├── games/season=2024-25/month=10/
│   ├── box-scores/season=2024-25/month=10/
│   ├── play-by-play/season=2024-25/month=10/
│   └── players/season=2024-25/
└── backfill-state/
    ├── checkpoint.json
    └── daily-progress/date=2024-12-15/
```

## State Management

The application maintains checkpoint files in S3 to enable resumability:
- Tracks completed games and failed operations
- Stores progress statistics and ETAs
- Enables resume from any checkpoint after interruption

## Performance

- Conservative rate limiting: 1 request every 5 seconds
- Memory-efficient processing with streaming
- Concurrent S3 uploads (3 parallel threads)
- Estimated runtime: 2-3 days for complete season

## Monitoring

The application provides structured JSON logs with:
- Processing rate and ETA calculations
- Error rates by type
- Data quality scores
- Storage utilization metrics
- API response time tracking