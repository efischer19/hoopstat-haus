# Silver Layer Processing Application

The Silver Layer Processing application transforms Bronze layer JSON data into validated, cleaned Silver layer data following the medallion architecture pattern.

## Overview

This application processes NBA statistics data and provides the transformation layer between raw Bronze data and analytics-ready Silver data. It handles:

- Bronze layer JSON data ingestion from S3
- Data validation using Silver models (PlayerStats, TeamStats, GameStats)
- Data cleaning and standardization
- Silver layer data storage in S3 (JSON format)
- S3 event-driven processing for real-time pipeline
- Comprehensive observability and monitoring

## Architecture

### Deployment
- **Runtime**: AWS Lambda for serverless processing
- **Trigger**: S3 events when Bronze layer summary.json is updated
- **Storage**: Reads from Bronze S3 bucket, writes to Silver S3 bucket
- **Format**: JSON storage following ADR-025

### Data Models
Uses existing Silver models from `hoopstat-data`:
- `PlayerStats`: Individual player statistics
- `TeamStats`: Team-level statistics  
- `GameStats`: Game-level statistics and metadata

## Usage

This application uses Poetry for dependency management. From the app directory:

```bash
# Install dependencies
poetry install

# Run the application
poetry run python -m app.main --help
```

### Basic Commands

```bash
# Show help
poetry run python -m app.main --help

# Process data for current date
poetry run python -m app.main process

# Process data for specific date  
poetry run python -m app.main process --date 2023-12-25

# Dry run (validation only, no data written)
poetry run python -m app.main process --dry-run

# Check pipeline status
poetry run python -m app.main status

# Enable debug logging
poetry run python -m app.main --debug process
```

### Lambda Deployment

The application is designed to run as an AWS Lambda function:

```python
# Lambda entry point
from app.handlers import lambda_handler

# S3 event processing
def lambda_handler(event, context):
    # Processes S3 events automatically
    return response
```

## Data Processing Pipeline

1. **S3 Event Trigger**: Lambda triggered when Bronze summary.json is updated
2. **Summary Reading**: Reads Bronze layer summary to get last ingestion date
3. **Data Loading**: Reads Bronze JSON from S3 for the target date
4. **Validation**: Applies Silver model validation 
5. **Transformation**: Cleans and standardizes data
6. **Quality Checks**: Validates data quality and completeness
7. **Storage**: Writes Silver JSON to S3
8. **Monitoring**: Logs processing results and metrics

### Trigger Mechanism

The Silver processing is triggered by updates to the Bronze layer summary file (`_metadata/summary.json`). When Bronze ingestion completes, it updates this summary file with metadata including the `last_ingestion_date`. The Silver Lambda reads this summary to determine which date's data to process, ensuring proper coordination between Bronze and Silver layers.

## Configuration

The application uses the shared `hoopstat-config` library for configuration management. Configuration includes:

- AWS S3 bucket settings (Bronze input, Silver output)
- Data validation rules and thresholds
- Processing parameters
- Logging configuration
- Error handling policies

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/test_main.py
```

### Code Quality

```bash
# Format code
poetry run ruff format .

# Check formatting
poetry run ruff format --check .

# Run linter
poetry run ruff check .
```

### Local CI Check

Run the same checks that CI runs:

```bash
# From repository root
./scripts/local-ci-check.sh apps/silver-processing
```

## Dependencies

### Production
- `click`: CLI framework (following ADR-022)
- `jsonschema`: JSON schema validation
- Shared libraries: `hoopstat-config`, `hoopstat-observability`, `hoopstat-data`, `hoopstat-s3`

### Development
- `pytest`: Testing framework
- `pytest-cov`: Coverage reporting
- `pytest-mock`: Mocking utilities
- `moto`: AWS service mocking
- `ruff`: Linting and formatting
- `black`: Code formatting

## Error Handling

- **Validation Failures**: Invalid data is logged and quarantined
- **Processing Errors**: Failed records are retried with exponential backoff
- **S3 Errors**: Network issues trigger automatic retries
- **Lambda Timeouts**: Large datasets are processed in batches

## Monitoring

- **CloudWatch Logs**: Structured logging for all processing events
- **CloudWatch Metrics**: Processing rates, error rates, data quality metrics
- **S3 Metrics**: Data volume and processing latency
- **Lambda Metrics**: Function performance and error tracking

## Contributing

1. Follow the development philosophy in `meta/DEVELOPMENT_PHILOSOPHY.md`
2. Review relevant ADRs in `meta/adr/`, especially ADR-025 (JSON Storage)
3. Run local CI checks before submitting PRs
4. Write tests for new functionality
5. Update documentation as needed

## Related Architecture Decisions

- **ADR-025**: JSON Storage for MVP Data Pipeline
- **ADR-022**: Click CLI Framework  
- **ADR-015**: JSON Logging
- **ADR-018**: CloudWatch Observability