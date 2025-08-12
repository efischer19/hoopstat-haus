# Bronze Layer Ingestion Application

The Bronze Layer Ingestion application is responsible for collecting raw NBA statistics data from the NBA API and storing it in the bronze layer of our data lake following the medallion architecture pattern.

## Overview

This application ingests NBA data and provides the foundation for downstream data processing in the silver and gold layers. It handles:

- NBA API data collection
- Raw data storage in S3 (bronze layer) 
- Data quality validation
- Retry logic for reliable ingestion
- Observability and monitoring

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

# Ingest data for current season
poetry run python -m app.main ingest

# Ingest data for specific season
poetry run python -m app.main ingest --season 2023-24

# Dry run (no data written)
poetry run python -m app.main ingest --dry-run

# Check pipeline status
poetry run python -m app.main status

# Enable debug logging
poetry run python -m app.main --debug ingest
```

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

# Run bronze layer validation tests
poetry run pytest tests/test_bronze_layer_validation.py

# Run integration tests with mock data
poetry run pytest tests/test_mock_data_integration.py
```

### Bronze Layer Validation

This application includes comprehensive validation tests that cover all acceptance criteria for bronze layer ingestion:

```bash
# Run complete validation suite
python validate_bronze_layer.py --all

# Run specific validation categories
python validate_bronze_layer.py --core           # Core validation tests
python validate_bronze_layer.py --integration    # Integration tests
python validate_bronze_layer.py --performance    # Performance benchmarks

# Check acceptance criteria coverage
python validate_bronze_layer.py --check-criteria
```

#### Validation Coverage

The validation suite ensures:

- **JSON to Parquet Conversion**: Validates data accuracy during conversion
- **Partitioning Scheme**: Tests year/month/day/hour partitioning implementation  
- **Metadata Enrichment**: Verifies ingestion timestamps and source system tags
- **Error Handling**: Tests resilience against malformed data
- **Compression Optimization**: Validates Parquet compression and storage efficiency
- **Performance Benchmarks**: Asserts ingestion speed and throughput requirements
- **Mock Data Integration**: Tests with realistic NBA data simulation

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
- Shared libraries: `hoopstat-config`, `hoopstat-observability`, `hoopstat-data`

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