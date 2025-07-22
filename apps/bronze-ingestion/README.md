# Bronze Layer Data Ingestion

## Overview

The Bronze Layer Data Ingestion application is responsible for fetching raw NBA data from various sources and storing it in the Bronze layer of our Medallion Architecture. This application forms the foundation of our data pipeline by ingesting fresh NBA statistics daily.

## Architecture

This application follows the established Hoopstat Haus patterns:
- **Containerized microservice** approach using Docker
- **Scheduled execution** via GitHub Actions
- **Stateless design** with external state management in S3
- **Structured logging** with JSON format for observability

## Data Sources

- **NBA API**: Primary source for games, players, and statistics
- **Rate limiting**: Respectful API usage with exponential backoff
- **Data validation**: Schema validation and quality checks

## Data Output

The application stores data in the Bronze layer with the following structure:
```
s3://hoopstat-haus-bronze/
├── nba-api/
│   ├── games/year=2024/month=01/day=15/hour=04/
│   ├── players/year=2024/month=01/day=15/hour=04/
│   ├── teams/year=2024/month=01/day=15/hour=04/
│   └── statistics/year=2024/month=01/day=15/hour=04/
└── ingestion-metadata/
    └── run-logs/year=2024/month=01/day=15/hour=04/
```

## Dependencies

- **nba-api**: For accessing NBA statistics and data
- **pyarrow**: For Parquet file processing and optimization
- **boto3**: For AWS S3 storage operations

## Usage

### Local Development

```bash
# Install dependencies
poetry install

# Run the application
poetry run python -m app.main

# Run tests
poetry run pytest

# Lint and format
poetry run ruff check .
poetry run black .
```

### Docker

```bash
# Build the container (from repository root)
docker build -f apps/bronze-ingestion/Dockerfile -t bronze-ingestion:latest .

# Run the container
docker run bronze-ingestion:latest
```

## Configuration

The application uses environment variables for configuration:
- `AWS_REGION`: AWS region for S3 operations (default: us-east-1)
- `S3_BUCKET_PREFIX`: S3 bucket prefix (default: hoopstat-haus-bronze)
- `LOG_LEVEL`: Logging level (default: INFO)

## Error Handling

- **Exponential backoff** for API rate limiting
- **Partial failure recovery** continues processing other data sources
- **Circuit breaker pattern** for API failure protection
- **Comprehensive logging** for debugging and monitoring

## Monitoring

The application provides structured JSON logging compatible with CloudWatch:
- Pipeline execution metrics
- Data quality validation results
- API response times and rate limit usage
- Storage utilization tracking

## Development Notes

This application is part of the Bronze Layer Ingestion epic and follows the patterns established in the project's ADRs:
- ADR-003: Poetry for dependency management
- ADR-004: pytest for testing
- ADR-006: Docker containerization
- ADR-008: Monorepo application structure