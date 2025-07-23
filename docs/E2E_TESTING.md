# E2E Pipeline Testing Framework

This document provides comprehensive setup and usage instructions for the localstack-based pipeline testing framework.

## Overview

The E2E testing framework simulates the complete data pipeline flow from bronze → silver → gold layers using Localstack S3 simulation. This enables local development and CI testing without requiring actual AWS resources.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Bronze Layer  │    │  Silver Layer   │    │   Gold Layer    │
│                 │    │                 │    │                 │
│ Raw NBA data    │──▶ │ Cleaned &       │──▶ │ Business        │
│ (JSON format)   │    │ normalized      │    │ metrics         │
│                 │    │ (Parquet)       │    │ (Parquet/JSON)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Components

- **Localstack**: AWS S3 simulation for local testing
- **S3TestUtils**: Utilities for S3 bucket operations (create, read, write, delete)
- **PipelineTestRunner**: Orchestrates the complete pipeline testing
- **LocalstackManager**: Manages Localstack container lifecycle
- **Docker Compose**: Multi-service orchestration for testing

## Local Development Setup

### Prerequisites

- Docker and Docker Compose
- Poetry (Python dependency management)
- Python 3.12+

### Quick Start

1. **Clone and navigate to the repository:**
   ```bash
   git clone <repository-url>
   cd hoopstat-haus
   ```

2. **Start the E2E testing environment:**
   ```bash
   docker-compose -f docker-compose.test.yml up --build
   ```

3. **Run tests manually (alternative approach):**
   ```bash
   cd libs/hoopstat-e2e-testing
   poetry install
   poetry run pytest -v
   ```

### Development Workflow

1. **Start Localstack for development:**
   ```bash
   docker run --rm -d \
     --name localstack-dev \
     -p 4566:4566 \
     -e SERVICES=s3 \
     -e DEBUG=1 \
     localstack/localstack:3.8
   ```

2. **Run specific tests:**
   ```bash
   cd libs/hoopstat-e2e-testing
   poetry run pytest tests/test_s3_utils.py -v
   poetry run pytest tests/test_pipeline_runner.py -v
   ```

3. **Run integration tests:**
   ```bash
   cd testing
   poetry run pytest tests/test_integration_pipeline.py -v
   ```

## Usage Examples

### Basic S3 Operations

```python
from hoopstat_e2e_testing import S3TestUtils

# Initialize S3 utilities
s3_utils = S3TestUtils(endpoint_url="http://localhost:4566")

# Create a bucket
s3_utils.create_bucket("my-test-bucket")

# Upload data
test_data = {"message": "Hello, World!", "count": 42}
s3_utils.put_object("my-test-bucket", "data/test.json", test_data)

# Download data
retrieved_data = s3_utils.get_object("my-test-bucket", "data/test.json", "json")
print(retrieved_data)  # {"message": "Hello, World!", "count": 42}

# Clean up
s3_utils.delete_bucket("my-test-bucket", delete_objects=True)
```

### Complete Pipeline Testing

```python
from hoopstat_e2e_testing import S3TestUtils, PipelineTestRunner

# Initialize components
s3_utils = S3TestUtils(endpoint_url="http://localhost:4566")
pipeline = PipelineTestRunner(s3_utils, project_name="my-test")

# Run complete pipeline
success = pipeline.run_full_pipeline(num_teams=4, num_players_per_team=5)

if success:
    # Verify results
    verification = pipeline.verify_pipeline_output()
    print("Pipeline verification:", verification)
    
    # Clean up
    pipeline.cleanup_environment()
```

### DataFrame Operations

```python
import pandas as pd
from hoopstat_e2e_testing import S3TestUtils

s3_utils = S3TestUtils()
s3_utils.create_bucket("data-bucket")

# Upload DataFrame as Parquet
df = pd.DataFrame({
    "player": ["LeBron James", "Stephen Curry", "Kevin Durant"],
    "points": [25.7, 24.8, 27.1],
    "team": ["Lakers", "Warriors", "Nets"]
})

s3_utils.put_object("data-bucket", "stats/players.parquet", df)

# Download DataFrame
retrieved_df = s3_utils.get_object("data-bucket", "stats/players.parquet", "dataframe")
print(retrieved_df)
```

## CI Integration

The E2E testing framework integrates with the existing GitHub Actions CI workflow:

### Automatic Triggering

Tests run automatically when:
- Changes are made to `hoopstat-e2e-testing`, `hoopstat-mock-data`, or `hoopstat-data` libraries
- Pull request body contains `[e2e]` tag
- Changes are pushed to the main branch

### Manual Triggering

Add `[e2e]` to your pull request description to force E2E tests to run:

```
## Changes
- Updated data processing logic
- Fixed bug in player statistics calculation

[e2e] - Run E2E pipeline tests
```

### CI Workflow Steps

1. **Environment Setup**: Builds Docker containers with all dependencies
2. **Localstack Startup**: Starts S3 simulation service with health checks
3. **Test Execution**: Runs complete pipeline tests in isolated environment
4. **Result Validation**: Verifies bronze → silver → gold data flow
5. **Cleanup**: Removes containers and volumes

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_ENDPOINT_URL` | `http://localhost:4566` | Localstack endpoint |
| `AWS_ACCESS_KEY_ID` | `test` | Test AWS access key |
| `AWS_SECRET_ACCESS_KEY` | `test` | Test AWS secret key |
| `AWS_DEFAULT_REGION` | `us-east-1` | AWS region for testing |

### Docker Compose Configuration

The `docker-compose.test.yml` file defines:

- **Localstack service**: S3 simulation with health checks
- **Test runner service**: Python environment with all dependencies
- **Network isolation**: Dedicated network for test communication
- **Volume management**: Temporary storage for test data

## Testing Strategy

### Test Layers

1. **Unit Tests**: Individual component testing (S3Utils, PipelineRunner)
2. **Integration Tests**: End-to-end pipeline validation
3. **Performance Tests**: Large dataset processing validation
4. **Data Quality Tests**: Cross-layer consistency validation

### Test Data

- **Mock NBA Data**: Realistic team, player, and game statistics
- **Deterministic Generation**: Seeded random data for reproducible tests
- **Scalable Volumes**: From small test sets to large-scale simulations

### Validation Checks

- **Data Consistency**: Record counts match across pipeline layers
- **Schema Compliance**: Data structures meet expected formats
- **Business Logic**: Statistical calculations are accurate
- **Performance**: Processing times meet acceptable thresholds

## Troubleshooting

### Common Issues

**1. Localstack Connection Failed**
```bash
# Check if Localstack is running
curl http://localhost:4566/health

# Restart Localstack
docker-compose -f docker-compose.test.yml restart localstack
```

**2. Permission Errors**
```bash
# Fix Docker permissions
sudo chmod 666 /var/run/docker.sock

# Clean up containers
docker-compose -f docker-compose.test.yml down --volumes
```

**3. Port Conflicts**
```bash
# Check port usage
netstat -tulpn | grep 4566

# Kill conflicting processes
sudo fuser -k 4566/tcp
```

**4. Memory Issues**
```bash
# Increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory → 4GB+

# Clean up unused containers
docker system prune -f
```

### Debug Mode

Enable verbose logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from hoopstat_e2e_testing import S3TestUtils
s3_utils = S3TestUtils()
# Detailed logs will be displayed
```

### Log Analysis

Check Localstack logs for S3 operations:
```bash
docker-compose -f docker-compose.test.yml logs localstack
```

Check test runner logs for application errors:
```bash
docker-compose -f docker-compose.test.yml logs test-runner
```

## Performance Considerations

### Resource Usage

- **Memory**: ~2GB recommended for Docker environment
- **CPU**: Tests run in parallel where possible
- **Storage**: Temporary data cleaned up automatically
- **Network**: Isolated container communication

### Optimization Tips

1. **Parallel Execution**: Use pytest-xdist for faster test runs
2. **Data Caching**: Reuse generated mock data between tests
3. **Selective Testing**: Run only changed components during development
4. **Resource Limits**: Configure appropriate Docker memory/CPU limits

## Contributing

### Adding New Tests

1. Create test files in `libs/hoopstat-e2e-testing/tests/`
2. Follow existing naming conventions (`test_*.py`)
3. Use pytest fixtures for setup/teardown
4. Include both positive and negative test cases

### Extending Pipeline

1. Add new transformation logic to `PipelineTestRunner`
2. Create corresponding validation methods
3. Update integration tests to cover new functionality
4. Document new features in this README

### Best Practices

- **Isolation**: Each test should clean up after itself
- **Determinism**: Use seeded random data for reproducible results
- **Documentation**: Comment complex test scenarios
- **Performance**: Avoid unnecessary data generation in tests