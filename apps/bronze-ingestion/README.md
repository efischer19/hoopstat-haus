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

## Deployment Options

### Option 1: Local Execution via Docker (Recommended)

For environments where Lambda execution may be blocked (e.g., NBA API blocking AWS IPs), you can run bronze-ingestion locally using the same Docker image deployed to Lambda.

**Prerequisites:**
- Docker installed and running
- AWS CLI configured with appropriate credentials
- Access to the ECR repository

**Setup:**
```bash
# One-time setup (creates execution environment)
./setup-local.sh [optional_target_directory]

# Follow the instructions to add to crontab for daily 4:30 AM execution
```

**How it works:**
- Uses the same ECR Docker image built by CI/CD pipeline
- Pulls latest image automatically on each run
- Stores data to same S3 buckets as Lambda execution
- Comprehensive logging in `[target_directory]/logs/`

### Option 2: Local Development with Poetry

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

# Run integration tests
poetry run pytest tests/test_bronze_summary_integration.py

# Run S3 manager tests
poetry run pytest tests/test_s3_manager.py
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

- **JSON Storage Format**: Validates data accuracy and format consistency for JSON storage
- **S3 Operations**: Tests bucket management, key generation, and data retrieval
- **Data Validation**: Verifies JSON schema validation and quality checks  
- **Error Handling**: Tests resilience against malformed data and quarantine functionality
- **Ingestion Pipeline**: End-to-end validation of the complete ingestion workflow
- **Bronze Summary Generation**: Tests summary creation and metadata enrichment
- **Integration Testing**: Comprehensive integration tests across all components

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

## Local Execution Troubleshooting

### Common Issues

**Docker not running:**
```bash
# Start Docker (macOS/Windows)
open /Applications/Docker.app

# Check Docker status
docker info
```

**AWS credentials not configured:**
```bash
# Configure AWS CLI
aws configure

# Verify credentials
aws sts get-caller-identity
```

**ECR access denied:**
```bash
# Re-authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com
```

**Cron job not running:**
```bash
# Check cron service is running
sudo service cron status

# View system cron logs (location varies by system)
sudo tail -f /var/log/cron

# Test manual execution
cd ~/bronze-ingestion-local && ./run-daily.sh
```

### Monitoring

- **Daily logs:** `[target_directory]/logs/bronze-ingestion-YYYYMMDD.log`
- **Cron logs:** System default cron logging location
- **Test execution:** Run the daily script manually to verify functionality

## Architecture

This application follows the established patterns:

- **Shared Libraries**: Uses `hoopstat-config`, `hoopstat-observability`, and `hoopstat-data` libraries
- **Click CLI**: Command-line interface with multiple commands
- **Error Handling**: Proper error handling with structured logging
- **Retry Logic**: Uses `tenacity` for robust API calls
- **Data Formats**: Stores data in JSON format for efficient processing and debugging. JSON provides human-readable data that's easy to inspect via AWS console, integrates seamlessly with AI assistants for data analysis, and simplifies development workflows without additional dependencies.

## Dependencies

### Production
- `nba-api`: NBA statistics API client
- `boto3`: AWS S3 client
- `pandas`: Data manipulation
- `pyarrow`: Optional Parquet file support (legacy format support)
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