# Hoopstat E2E Testing

End-to-end testing utilities for the basketball data pipeline using Localstack S3 simulation.

## Features

- S3 bucket operations for testing (create, read, write, delete)
- Bronze → Silver → Gold pipeline testing utilities
- Localstack integration for local development
- Docker Compose orchestration for multi-service testing

## Usage

### Local Development

```bash
# Start localstack and run tests
docker-compose -f docker-compose.test.yml up --build

# Run tests manually
poetry install
poetry run pytest
```

### CI Integration

This library integrates with the existing GitHub Actions CI workflow to provide isolated testing environments.

## Architecture

The testing framework follows the medallion architecture pattern:

- **Bronze Layer**: Raw data ingestion and storage
- **Silver Layer**: Cleaned and transformed data  
- **Gold Layer**: Business-ready aggregated data

## Test Utilities

- `S3TestUtils`: Utilities for S3 bucket operations
- `PipelineTestRunner`: End-to-end pipeline testing
- `LocalstackManager`: Localstack lifecycle management