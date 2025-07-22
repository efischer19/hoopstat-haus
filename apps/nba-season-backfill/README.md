# NBA Season Backfill Application

Containerized Python application for backfilling NBA 2024-25 season data from NBA API to Bronze layer S3 storage. Implements rate limiting, state management, and comprehensive error handling per project ADRs.

## Features

- **NBA API Integration**: Respectful data collection with rate limiting (ADR-013)
- **S3 Bronze Layer Storage**: Parquet format with proper partitioning (ADR-014)
- **Structured JSON Logging**: Comprehensive observability (ADR-015)
- **State Management**: Resumable operations with checkpoint capability
- **Error Handling**: Comprehensive retry logic and failure recovery
- **Containerized**: Docker support following project standards (ADR-006)

## Quick Start

### Using Docker (Recommended)

Build from repository root:
```bash
docker build -f apps/nba-season-backfill/Dockerfile -t nba-backfill:latest .
```

Run with basic configuration:
```bash
docker run --rm \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e AWS_REGION=us-east-1 \
  nba-backfill:latest \
  --season 2024-25 \
  --s3-bucket your-bronze-bucket
```

Run in dry-run mode (no API calls or uploads):
```bash
docker run --rm nba-backfill:latest --dry-run
```

### Local Development

Install dependencies:
```bash
cd apps/nba-season-backfill
poetry install
```

Run application:
```bash
poetry run backfill --help
poetry run backfill --dry-run
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NBA_TARGET_SEASON` | `2024-25` | NBA season to backfill |
| `NBA_RATE_LIMIT_SECONDS` | `5.0` | Seconds between API requests |
| `AWS_S3_BUCKET` | `hoopstat-haus-bronze` | S3 bucket for storage |
| `AWS_S3_PREFIX` | `historical-backfill` | S3 prefix for data |
| `AWS_REGION` | `us-east-1` | AWS region |
| `STATE_FILE_PATH` | `s3://hoopstat-haus-bronze/backfill-state/checkpoint.json` | Checkpoint location |
| `DRY_RUN` | `false` | Run without API calls/uploads |
| `RESUME_FROM_CHECKPOINT` | `false` | Resume from existing state |

### CLI Options

```bash
Usage: python -m app.main [OPTIONS]

Options:
  --season TEXT              NBA season to backfill (format: YYYY-YY)
  --rate-limit FLOAT         Seconds to wait between NBA API requests
  --s3-bucket TEXT           S3 bucket for Bronze layer storage
  --s3-prefix TEXT           S3 prefix for backfill data
  --state-file-path TEXT     Path to state/checkpoint file
  --dry-run                  Run in dry-run mode without making API calls or uploads
  --resume                   Resume from existing checkpoint
  --max-retries INTEGER      Maximum retry attempts for transient failures
  --no-box-scores           Skip box score collection
  --no-play-by-play         Skip play-by-play collection
  --no-player-info          Skip player info collection
  --help                     Show this message and exit.
```

## Data Collection

The application collects the following data types for each game:

- **Traditional Box Scores**: Player and team statistics
- **Advanced Box Scores**: Advanced metrics and analytics
- **Play-by-Play Data**: Detailed game events and sequences

Data is stored in S3 with the following structure:
```
s3://bucket/historical-backfill/
├── box-scores-traditional/season=2024-25/month=10/
├── box-scores-advanced/season=2024-25/month=10/
└── play-by-play/season=2024-25/month=10/
```

## State Management

The application maintains comprehensive state for resumability:

- **Completed Games**: Games successfully processed
- **Failed Games**: Games that failed with retry counts
- **Progress Statistics**: Performance metrics and ETA
- **Configuration Snapshot**: Settings used for the run

State is automatically saved every 10 games processed and can be used to resume interrupted operations.

## Monitoring

The application provides structured JSON logging with:

- **Performance Metrics**: Duration and record counts per ADR-015
- **API Statistics**: Request rates and response times
- **Progress Tracking**: Real-time completion status
- **Error Handling**: Detailed failure analysis

## Development

### Running Tests

```bash
poetry run test
```

### Code Quality

```bash
poetry run lint      # Check code quality
poetry run format    # Format code
```

### Local Testing

```bash
# Test with dry run
poetry run backfill --dry-run --season 2024-25

# Test with small date range (when implemented)
poetry run backfill --dry-run --start-date 2024-10-01 --end-date 2024-10-07
```

## Architecture

The application follows the project's architectural standards:

- **Configuration**: Pydantic models with validation
- **Logging**: hoopstat-observability library integration
- **Storage**: S3 with Parquet format and proper metadata
- **Error Handling**: Classified errors with appropriate retry logic
- **Rate Limiting**: Adaptive rate limiting with NBA API courtesy

## Production Deployment

1. **Build Container**: From repository root with proper context
2. **Configure Secrets**: AWS credentials and S3 access
3. **Set Environment**: Production-appropriate settings
4. **Monitor Execution**: Track progress through structured logs
5. **Handle Failures**: Use resume capability for interruptions

## Performance

Expected performance characteristics:

- **Processing Rate**: ~120 games/hour (conservative estimate)
- **API Rate**: 1 request per 5 seconds (720 requests/hour)
- **Season Completion**: 2-3 days for full 2024-25 season
- **Resource Usage**: 2-4GB RAM, minimal CPU

## Troubleshooting

### Common Issues

1. **Rate Limiting**: Application automatically handles NBA API rate limits
2. **Network Failures**: Retry logic handles transient connectivity issues
3. **AWS Credentials**: Ensure proper AWS configuration for S3 access
4. **Resume Failures**: Check state file integrity and S3 permissions

### Log Analysis

Key log fields to monitor:
- `duration_in_seconds`: Job performance metrics
- `records_processed`: Data collection progress
- `error_type`: Classify failures for resolution
- `correlation_id`: Track related operations

## License

This application is part of the Hoopstat Haus project and follows the same licensing terms.