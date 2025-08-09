# hoopstat-observability

**Version:** 0.1.0

## Description

Hoopstat Observability Library

Standardized logging and observability utilities for Hoopstat Haus applications.
Implements structured JSON logging per ADR-015, CloudWatch integration per ADR-018,
and semantic versioning per ADR-016.

This library consolidates logging functionality to ensure consistent observability
across all applications while eliminating code duplication.

## Installation

Add to your application's `pyproject.toml`:

```toml
[tool.poetry.dependencies]
hoopstat-observability = {path = "../libs/hoopstat-observability", develop = true}
```

## Usage

```python
from hoopstat_observability import JSONLogger, get_logger, performance_monitor, performance_context, CorrelationContext, correlation_context, DiagnosticLogger
```

## API Reference

### Classes

#### JSONFormatter

Custom logging formatter that outputs structured JSON logs per ADR-015.

Ensures consistent format across all log entries with required fields
for CloudWatch metric extraction and observability.

**Methods:**

- `format(self, record: Any) -> str`
  - Format log record as structured JSON.

#### JSONLogger

Standardized logger that outputs structured JSON per ADR-015.

Provides convenience methods for common logging patterns and ensures
consistent structure across all log entries.

**Methods:**

- `info(self, message: str) -> None`
  - Log info level message with optional extra fields.
- `warning(self, message: str) -> None`
  - Log warning level message with optional extra fields.
- `error(self, message: str) -> None`
  - Log error level message with optional extra fields.
- `debug(self, message: str) -> None`
  - Log debug level message with optional extra fields.
- `critical(self, message: str) -> None`
  - Log critical level message with optional extra fields.
- `log_performance(self, job_name: str, duration_in_seconds: float, records_processed: int, status: str) -> None`
  - Log performance metrics in ADR-015 standard format.
- `log_with_correlation(self, level: str, message: str, correlation_id: Any) -> None`
  - Log message with correlation ID for request tracing.

#### DiagnosticLogger

Enhanced logger for debugging and diagnostic information.

Provides utilities for capturing system state, performance metrics,
and detailed debugging information with structured logging.

**Methods:**

- `log_system_info(self) -> None`
  - Log system and environment information for diagnostics.
- `log_function_entry(self, func_name: str, args: tuple, kwargs: Any) -> None`
  - Log function entry with parameters for debugging.
- `log_function_exit(self, func_name: str, result: Any, duration: Any) -> None`
  - Log function exit with result information.
- `log_exception(self, exception: Exception, context: Any) -> None`
  - Log exception with full traceback and context.
- `log_performance_warning(self, operation: str, duration: float, threshold: float, context: Any) -> None`
  - Log performance warning when operation exceeds threshold.
- `log_memory_usage(self) -> None`
  - Log current memory usage for diagnostics.
- `trace_execution(self, func) -> Any`
  - Decorator for detailed function execution tracing.

#### CorrelationContext

Manages correlation IDs for request tracing.

Provides thread-safe storage and retrieval of correlation IDs
to enable tracking requests across multiple services and operations.

**Methods:**

- `get_correlation_id() -> Any`
  - Get the current correlation ID for this thread.
- `set_correlation_id(correlation_id: str) -> None`
  - Set the correlation ID for this thread.
- `generate_correlation_id() -> str`
  - Generate a new UUID-based correlation ID.
- `clear_correlation_id() -> None`
  - Clear the correlation ID for this thread.

### Functions

#### get_logger

```python
get_logger(name: str, level: int) -> JSONLogger
```

Get a standardized JSON logger instance.

Args:
    name: Logger name (typically __name__ of calling module)
    level: Logging level (default: INFO)

Returns:
    Configured JSONLogger instance

Example:
    logger = get_logger(__name__)
    logger.info("Application started", version="1.0.0")

#### format

```python
format(self, record: Any) -> str
```

Format log record as structured JSON.

Args:
    record: Python logging record to format

Returns:
    JSON string formatted according to ADR-015 standards

#### info

```python
info(self, message: str) -> None
```

Log info level message with optional extra fields.

#### warning

```python
warning(self, message: str) -> None
```

Log warning level message with optional extra fields.

#### error

```python
error(self, message: str) -> None
```

Log error level message with optional extra fields.

#### debug

```python
debug(self, message: str) -> None
```

Log debug level message with optional extra fields.

#### critical

```python
critical(self, message: str) -> None
```

Log critical level message with optional extra fields.

#### log_performance

```python
log_performance(self, job_name: str, duration_in_seconds: float, records_processed: int, status: str) -> None
```

Log performance metrics in ADR-015 standard format.

Args:
    job_name: Name of the job or operation
    duration_in_seconds: Execution time in seconds
    records_processed: Number of records processed
    status: Job status (success/failed)
    **kwargs: Additional context fields

#### log_with_correlation

```python
log_with_correlation(self, level: str, message: str, correlation_id: Any) -> None
```

Log message with correlation ID for request tracing.

Args:
    level: Log level (info, warning, error, debug, critical)
    message: Log message
    correlation_id: Correlation ID for request tracing
    **kwargs: Additional context fields

#### get_diagnostic_logger

```python
get_diagnostic_logger(name: str) -> DiagnosticLogger
```

Get a diagnostic logger instance.

Args:
    name: Logger name (typically __name__ of calling module)

Returns:
    Configured DiagnosticLogger instance

Example:
    diagnostics = get_diagnostic_logger(__name__)
    diagnostics.log_system_info()

#### log_system_info

```python
log_system_info(self) -> None
```

Log system and environment information for diagnostics.

#### log_function_entry

```python
log_function_entry(self, func_name: str, args: tuple, kwargs: Any) -> None
```

Log function entry with parameters for debugging.

Args:
    func_name: Name of the function being entered
    args: Positional arguments (sensitive data will be masked)
    kwargs: Keyword arguments (sensitive data will be masked)

#### log_function_exit

```python
log_function_exit(self, func_name: str, result: Any, duration: Any) -> None
```

Log function exit with result information.

Args:
    func_name: Name of the function being exited
    result: Function result (will be summarized, not logged in full)
    duration: Function execution duration in seconds

#### log_exception

```python
log_exception(self, exception: Exception, context: Any) -> None
```

Log exception with full traceback and context.

Args:
    exception: Exception that occurred
    context: Additional context information

#### log_performance_warning

```python
log_performance_warning(self, operation: str, duration: float, threshold: float, context: Any) -> None
```

Log performance warning when operation exceeds threshold.

Args:
    operation: Name of the operation
    duration: Actual duration in seconds
    threshold: Warning threshold in seconds
    context: Additional context information

#### log_memory_usage

```python
log_memory_usage(self) -> None
```

Log current memory usage for diagnostics.

#### trace_execution

```python
trace_execution(self, func) -> Any
```

Decorator for detailed function execution tracing.

Logs entry, exit, duration, and any exceptions for the decorated function.

Example:
    @diagnostics.trace_execution
    def complex_operation():
        # Function implementation
        pass

#### wrapper

```python
wrapper() -> Any
```

#### performance_monitor

```python
performance_monitor(job_name: Any, records_processed_key: str) -> Any
```

Decorator to monitor data pipeline performance.

Automatically logs execution duration and record count in structured JSON format
according to ADR-015 standards. The decorated function should return a value that
either:
1. Is the record count (if it returns an integer)
2. Is a dict containing the record count under records_processed_key
3. Has a records_processed attribute

Args:
    job_name: Name of the data pipeline job. If None, uses function name.
    records_processed_key: Key to look for record count in return value dict.

Returns:
    Decorated function that logs performance metrics.

Example:
    @performance_monitor(job_name="user_data_sync")
    def sync_users():
        # Process data...
        return {"records_processed": 1500, "status": "success"}

    @performance_monitor()
    def process_records():
        # Process data...
        return 250  # Return record count directly

#### performance_context

```python
performance_context(job_name: str, records_processed: int) -> Any
```

Context manager to monitor data pipeline performance.

Automatically logs execution duration and allows dynamic record count tracking.
Provides more flexibility than the decorator for complex workflows.

Args:
    job_name: Name of the data pipeline job.
    records_processed: Initial record count (default: 0).

Yields:
    Context dict with 'records_processed' key that can be updated during execution.

Example:
    with performance_context("data_export", 0) as ctx:
        for batch in get_data_batches():
            process_batch(batch)
            ctx["records_processed"] += len(batch)

#### decorator

```python
decorator(func: F) -> F
```

#### wrapper

```python
wrapper() -> Any
```

#### correlation_context

```python
correlation_context(correlation_id: Any) -> Any
```

Context manager for managing correlation IDs.

Automatically sets and clears correlation ID for the duration of the context.
Generates a new correlation ID if none provided.

Args:
    correlation_id: Existing correlation ID to use, or None to generate new one

Yields:
    The correlation ID being used in this context

Example:
    # Use existing correlation ID
    with correlation_context("req-123") as corr_id:
        process_request(corr_id)

    # Generate new correlation ID
    with correlation_context() as corr_id:
        start_new_operation(corr_id)

#### with_correlation

```python
with_correlation(func) -> Any
```

Decorator to automatically include correlation ID in function logging.

Any logging performed within the decorated function will automatically
include the current correlation ID.

Example:
    @with_correlation
    def process_data():
        logger.info("Processing started")  # Will include correlation_id

#### get_correlation_id

```python
get_correlation_id() -> Any
```

Get the current correlation ID for this thread.

Returns:
    Current correlation ID or None if not set

#### set_correlation_id

```python
set_correlation_id(correlation_id: str) -> None
```

Set the correlation ID for this thread.

Args:
    correlation_id: Unique identifier for request correlation

#### generate_correlation_id

```python
generate_correlation_id() -> str
```

Generate a new UUID-based correlation ID.

Returns:
    New correlation ID

#### clear_correlation_id

```python
clear_correlation_id() -> None
```

Clear the correlation ID for this thread.

#### wrapper

```python
wrapper() -> Any
```
