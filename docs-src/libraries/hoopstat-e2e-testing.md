# hoopstat-e2e-testing

**Version:** 0.1.0

## Description

End-to-end testing utilities for basketball data pipeline.

This package provides utilities for testing the complete data pipeline
using Localstack S3 simulation and Docker Compose orchestration.

## Installation

Add to your application's `pyproject.toml`:

```toml
[tool.poetry.dependencies]
hoopstat-e2e-testing = {path = "../libs/hoopstat-e2e-testing", develop = true}
```

## Usage

```python
from hoopstat_e2e_testing import S3TestUtils, PipelineTestRunner, LocalstackManager
```

## API Reference

### Classes

#### LocalstackManager

Manages Localstack container for testing.

**Methods:**

- `start(self, timeout: int) -> bool`
  - Start Localstack container.
- `stop(self) -> bool`
  - Stop and remove Localstack container.
- `wait_for_ready(self, timeout: int) -> bool`
  - Wait for Localstack to be ready to accept requests.
- `is_running(self) -> bool`
  - Check if Localstack container is running.
- `get_logs(self) -> str`
  - Get logs from Localstack container.

#### PipelineTestRunner

Orchestrates end-to-end pipeline testing.

**Methods:**

- `setup_environment(self) -> bool`
  - Set up the testing environment with medallion architecture buckets.
- `cleanup_environment(self) -> bool`
  - Clean up the testing environment.
- `ingest_bronze_data(self, num_teams: int, num_players_per_team: int) -> bool`
  - Ingest raw mock data into the bronze layer.
- `transform_silver_data(self) -> bool`
  - Transform bronze data into silver layer (cleaned and normalized).
- `aggregate_gold_data(self) -> bool`
  - Aggregate silver data into gold layer (business metrics).
- `run_full_pipeline(self, num_teams: int, num_players_per_team: int) -> bool`
  - Run the complete pipeline test from bronze to gold.
- `verify_pipeline_output(self) -> Any`
  - Verify the pipeline output and return validation results.

#### DateTimeEncoder

Custom JSON encoder that handles datetime objects.

**Methods:**

- `default(self, obj) -> Any`

#### S3TestUtils

Utilities for S3 operations during testing with Localstack.

**Methods:**

- `create_bucket(self, bucket_name: str) -> bool`
  - Create an S3 bucket.
- `delete_bucket(self, bucket_name: str, delete_objects: bool) -> bool`
  - Delete an S3 bucket.
- `bucket_exists(self, bucket_name: str) -> bool`
  - Check if a bucket exists.
- `put_object(self, bucket_name: str, key: str, data: Any, content_type: Any) -> bool`
  - Put an object in S3.
- `get_object(self, bucket_name: str, key: str, return_type: str) -> Any`
  - Get an object from S3.
- `delete_object(self, bucket_name: str, key: str) -> bool`
  - Delete an object from S3.
- `list_objects(self, bucket_name: str, prefix: str) -> Any`
  - List objects in a bucket.
- `cleanup_test_buckets(self, prefix: str) -> None`
  - Clean up all test buckets with a given prefix.
- `setup_medallion_buckets(self, project_name: str) -> Any`
  - Set up bronze, silver, and gold buckets for medallion architecture testing.

### Functions

#### start

```python
start(self, timeout: int) -> bool
```

Start Localstack container.

Args:
    timeout: Maximum time to wait for container to be ready

Returns:
    True if container started successfully, False otherwise

#### stop

```python
stop(self) -> bool
```

Stop and remove Localstack container.

Returns:
    True if container stopped successfully, False otherwise

#### wait_for_ready

```python
wait_for_ready(self, timeout: int) -> bool
```

Wait for Localstack to be ready to accept requests.

Args:
    timeout: Maximum time to wait in seconds

Returns:
    True if Localstack is ready, False if timeout

#### is_running

```python
is_running(self) -> bool
```

Check if Localstack container is running.

Returns:
    True if container is running, False otherwise

#### get_logs

```python
get_logs(self) -> str
```

Get logs from Localstack container.

Returns:
    Container logs as string

#### setup_environment

```python
setup_environment(self) -> bool
```

Set up the testing environment with medallion architecture buckets.

Returns:
    True if setup successful, False otherwise

#### cleanup_environment

```python
cleanup_environment(self) -> bool
```

Clean up the testing environment.

Returns:
    True if cleanup successful, False otherwise

#### ingest_bronze_data

```python
ingest_bronze_data(self, num_teams: int, num_players_per_team: int) -> bool
```

Ingest raw mock data into the bronze layer.

Args:
    num_teams: Number of teams to generate
    num_players_per_team: Number of players per team

Returns:
    True if ingestion successful, False otherwise

#### transform_silver_data

```python
transform_silver_data(self) -> bool
```

Transform bronze data into silver layer (cleaned and normalized).

Returns:
    True if transformation successful, False otherwise

#### aggregate_gold_data

```python
aggregate_gold_data(self) -> bool
```

Aggregate silver data into gold layer (business metrics).

Returns:
    True if aggregation successful, False otherwise

#### run_full_pipeline

```python
run_full_pipeline(self, num_teams: int, num_players_per_team: int) -> bool
```

Run the complete pipeline test from bronze to gold.

Args:
    num_teams: Number of teams to generate
    num_players_per_team: Number of players per team

Returns:
    True if entire pipeline completed successfully, False otherwise

#### verify_pipeline_output

```python
verify_pipeline_output(self) -> Any
```

Verify the pipeline output and return validation results.

Returns:
    Dictionary with validation results

#### default

```python
default(self, obj) -> Any
```

#### create_bucket

```python
create_bucket(self, bucket_name: str) -> bool
```

Create an S3 bucket.

Args:
    bucket_name: Name of the bucket to create

Returns:
    True if bucket was created successfully, False otherwise

#### delete_bucket

```python
delete_bucket(self, bucket_name: str, delete_objects: bool) -> bool
```

Delete an S3 bucket.

Args:
    bucket_name: Name of the bucket to delete
    delete_objects: Whether to delete all objects in the bucket first

Returns:
    True if bucket was deleted successfully, False otherwise

#### bucket_exists

```python
bucket_exists(self, bucket_name: str) -> bool
```

Check if a bucket exists.

Args:
    bucket_name: Name of the bucket to check

Returns:
    True if bucket exists, False otherwise

#### put_object

```python
put_object(self, bucket_name: str, key: str, data: Any, content_type: Any) -> bool
```

Put an object in S3.

Args:
    bucket_name: Name of the bucket
    key: Object key (path)
    data: Data to upload (string, bytes, dict, or DataFrame)
    content_type: Content type of the object

Returns:
    True if object was uploaded successfully, False otherwise

#### get_object

```python
get_object(self, bucket_name: str, key: str, return_type: str) -> Any
```

Get an object from S3.

Args:
    bucket_name: Name of the bucket
    key: Object key (path)
    return_type: Type to return data as ('string', 'bytes', 'json', 'dataframe')

Returns:
    Object data in the specified format, or None if error

#### delete_object

```python
delete_object(self, bucket_name: str, key: str) -> bool
```

Delete an object from S3.

Args:
    bucket_name: Name of the bucket
    key: Object key (path)

Returns:
    True if object was deleted successfully, False otherwise

#### list_objects

```python
list_objects(self, bucket_name: str, prefix: str) -> Any
```

List objects in a bucket.

Args:
    bucket_name: Name of the bucket
    prefix: Prefix to filter objects

Returns:
    List of object information dictionaries

#### cleanup_test_buckets

```python
cleanup_test_buckets(self, prefix: str) -> None
```

Clean up all test buckets with a given prefix.

Args:
    prefix: Prefix to identify test buckets

#### setup_medallion_buckets

```python
setup_medallion_buckets(self, project_name: str) -> Any
```

Set up bronze, silver, and gold buckets for medallion architecture testing.

Args:
    project_name: Project name prefix for buckets

Returns:
    Dictionary with bucket names for each layer
