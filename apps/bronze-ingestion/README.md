# Bronze Layer Ingestion Application

The Bronze Layer Ingestion application is responsible for collecting raw NBA statistics data from the NBA API and storing it in the bronze layer of our data lake following the medallion architecture pattern.

## Overview

This application ingests NBA data and provides the foundation for downstream data processing in the silver and gold layers. It handles:

- NBA API data collection with rate limiting
- Data validation and quality checks
- Raw data storage in S3 (bronze layer) 
- Automatic quarantine of invalid data
- Retry logic for reliable ingestion
- Comprehensive observability and monitoring

## Installation

This application uses Poetry for dependency management. From the app directory:

```bash
# Install dependencies
poetry install

# Run the application
poetry run python -m app.main --help
```

## Usage

### Basic Commands

```bash
# Show help
poetry run python -m app.main --help

# Ingest data for current date
poetry run python -m app.main ingest

# Ingest data for specific date  
poetry run python -m app.main ingest --date 2023-12-25

# Dry run (no data written)
poetry run python -m app.main ingest --dry-run

# Check pipeline status
poetry run python -m app.main status

# Enable debug logging
poetry run python -m app.main --debug ingest
```

## Data Validation and Quality

This application includes comprehensive data validation and quality checks:

- **JSON Schema Validation**: All NBA API responses are validated against predefined schemas
- **Data Completeness Checks**: Ensures expected number of games and players for each date
- **Date Consistency Validation**: Verifies data is for the correct date range
- **Quality Metrics Logging**: Comprehensive quality scoring and monitoring
- **Automatic Quarantine**: Invalid data is quarantined for manual review instead of being discarded

See [VALIDATION_GUIDE.md](./VALIDATION_GUIDE.md) for detailed information about the validation system.

## Configuration

The application uses the shared `hoopstat-config` library for configuration management. Configuration includes:

- AWS S3 bucket settings
- NBA API settings
- Logging configuration
- Retry policies

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
./scripts/local-ci-check.sh apps/bronze-ingestion
```

## Docker

### Building

Build from the repository root to include shared libraries:

```bash
# Development build
docker build -f apps/bronze-ingestion/Dockerfile -t bronze-ingestion:dev --target development .

# Production build
docker build -f apps/bronze-ingestion/Dockerfile -t bronze-ingestion:latest .
```

### Running

```bash
# Run with default command
docker run bronze-ingestion:latest

# Run with custom command
docker run bronze-ingestion:latest poetry run python -m app.main status

# Run interactively
docker run -it bronze-ingestion:dev bash
```

## Architecture

This application follows the established patterns:

- **Shared Libraries**: Uses `hoopstat-config`, `hoopstat-observability`, and `hoopstat-data` libraries
- **Click CLI**: Command-line interface with multiple commands
- **Error Handling**: Proper error handling with structured logging
- **Retry Logic**: Uses `tenacity` for robust API calls
- **Data Formats**: Stores data in Parquet format for efficient processing

## Dependencies

### Production
- `nba-api`: NBA statistics API client
- `boto3`: AWS S3 client
- `pandas`: Data manipulation
- `pyarrow`: Parquet file support
- `tenacity`: Retry logic
- `click`: CLI framework
- `jsonschema`: JSON schema validation
- Shared libraries: `hoopstat-config`, `hoopstat-observability`, `hoopstat-data`, `hoopstat-nba_api`

### Development
- `pytest`: Testing framework
- `pytest-cov`: Coverage reporting
- `pytest-mock`: Mocking utilities
- `moto`: AWS service mocking
- `ruff`: Linting and formatting
- `black`: Code formatting

## Contributing

1. Follow the development philosophy in `meta/DEVELOPMENT_PHILOSOPHY.md`
2. Review relevant ADRs in `meta/adr/`
3. Run local CI checks before submitting PRs
4. Write tests for new functionality
5. Update documentation as needed