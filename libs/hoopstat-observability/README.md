# Hoopstat Observability Library

Standardized logging and observability utilities for Hoopstat Haus applications. This library consolidates logging functionality to ensure consistent observability across all applications while implementing ADR-015 JSON logging standards, ADR-018 CloudWatch integration, and ADR-016 versioning strategy.

## Features

- **Structured JSON Logging**: Consistent JSON format per ADR-015 with automatic timestamp and metadata handling
- **Performance Monitoring**: Decorators and context managers for automatic performance metric collection
- **Correlation Tracking**: Request tracing capabilities across distributed components
- **Diagnostic Utilities**: Enhanced debugging and diagnostic logging capabilities
- **CloudWatch Integration**: Seamless integration with AWS CloudWatch per ADR-018
- **Thread Safety**: Safe for use in multi-threaded applications

## Installation

This library is designed for use within the Hoopstat Haus monorepo. Add it as a dependency in your application's `pyproject.toml`:

```toml
[tool.poetry.dependencies]
hoopstat-observability = {path = "../../libs/hoopstat-observability", develop = true}
```

## Quick Start

### Basic JSON Logging

```python
from hoopstat_observability import get_logger

# Get a structured JSON logger
logger = get_logger(__name__)

# Log with automatic JSON formatting
logger.info("Application started", version="1.0.0", environment="production")

# Log with correlation ID
logger.log_with_correlation(
    "info", 
    "Processing request", 
    correlation_id="req-123",
    user_id="user456"
)
```

### Performance Monitoring

```python
from hoopstat_observability import performance_monitor, performance_context

# Using decorator for simple functions
@performance_monitor(job_name="data_processing")
def process_data():
    # Your processing logic here
    return 1000  # Return record count

# Using context manager for complex workflows
with performance_context("batch_processing") as ctx:
    for batch in data_batches:
        process_batch(batch)
        ctx["records_processed"] += len(batch)
```

### Correlation Tracking

```python
from hoopstat_observability import correlation_context, CorrelationContext

# Auto-generate correlation ID
with correlation_context() as corr_id:
    logger.info("Operation started", correlation_id=corr_id)
    perform_operation()

# Use existing correlation ID
with correlation_context("existing-correlation-123"):
    # All logging within this context will include the correlation ID
    process_request()
```

### Diagnostic Logging

```python
from hoopstat_observability import DiagnosticLogger

diagnostics = DiagnosticLogger(__name__)

# Log system information
diagnostics.log_system_info()

# Trace function execution
@diagnostics.trace_execution
def complex_operation():
    # Function implementation
    pass

# Log exceptions with context
try:
    risky_operation()
except Exception as e:
    diagnostics.log_exception(e, {"operation": "risky_operation", "retry_count": 3})
```

## ADR Compliance

This library implements the following Architecture Decision Records:

### ADR-015: JSON Logging Standards

All log output follows structured JSON format with required fields:
- `timestamp`: ISO 8601 format with Z suffix
- `level`: Log level (INFO, ERROR, etc.)
- `message`: Human-readable message
- `duration_in_seconds`: For performance metrics (CloudWatch extraction)
- `records_processed`: For data pipeline metrics (CloudWatch extraction)

### ADR-016: Shared Library Versioning

Uses semantic versioning (MAJOR.MINOR.PATCH) with monorepo local path dependencies.

### ADR-018: CloudWatch Observability

Structured logs include fields required for CloudWatch metric extraction and automated alerting.

## API Reference

### JSONLogger

Main logging class providing structured JSON output.

```python
from hoopstat_observability import JSONLogger, get_logger

# Create logger instance
logger = get_logger(__name__)

# Logging methods
logger.info(message, **extra_fields)
logger.warning(message, **extra_fields)
logger.error(message, **extra_fields)
logger.debug(message, **extra_fields)
logger.critical(message, **extra_fields)

# Performance logging
logger.log_performance(
    job_name="my_job",
    duration_in_seconds=1.234,
    records_processed=100,
    status="success"  # or "failed"
)
```

### Performance Monitoring

Utilities for automatic performance metric collection.

```python
from hoopstat_observability import performance_monitor, performance_context

# Decorator
@performance_monitor(job_name="optional_name", records_processed_key="custom_key")
def my_function():
    return {"custom_key": 100}  # Or return integer directly

# Context manager
with performance_context("job_name", records_processed=0) as ctx:
    ctx["records_processed"] = 50  # Update during execution
```

### Correlation Context

Request tracing and correlation ID management.

```python
from hoopstat_observability import correlation_context, CorrelationContext

# Context manager
with correlation_context("optional-id") as corr_id:
    # Use corr_id in your code
    pass

# Direct access
CorrelationContext.set_correlation_id("custom-id")
current_id = CorrelationContext.get_correlation_id()
CorrelationContext.clear_correlation_id()
```

### Diagnostic Logger

Enhanced debugging and diagnostic utilities.

```python
from hoopstat_observability import DiagnosticLogger

diagnostics = DiagnosticLogger(__name__)

# System information
diagnostics.log_system_info()

# Function tracing
@diagnostics.trace_execution
def traced_function():
    pass

# Exception logging
diagnostics.log_exception(exception, context={"key": "value"})

# Performance warnings
diagnostics.log_performance_warning("operation", duration=2.0, threshold=1.0)

# Memory usage
diagnostics.log_memory_usage()  # Requires psutil
```

## Migration from Existing Code

If you have existing `performance.py` modules in your applications, you can migrate by:

1. Adding the library dependency to your `pyproject.toml`
2. Replacing imports:
   ```python
   # Old
   from app.performance import performance_monitor
   
   # New
   from hoopstat_observability import performance_monitor
   ```
3. Removing the local `performance.py` file
4. Testing to ensure functionality is preserved

## Development

### Running Tests

```bash
cd libs/hoopstat-observability
python -m pytest tests/ -v
```

### Code Quality

```bash
# Lint code
ruff check hoopstat_observability/

# Format code
black hoopstat_observability/

# Type checking (if using mypy)
mypy hoopstat_observability/
```

## Contributing

This library follows the Hoopstat Haus development philosophy:

1. **Code is for Humans First**: Prioritize readability and clarity
2. **Favor Simplicity**: Avoid unnecessary complexity
3. **Test What Matters**: Focus on critical functionality
4. **Leave Code Better**: Apply the Boy Scout Rule

See the main repository's `CONTRIBUTING.md` for detailed guidelines.

## Version History

- **0.1.0**: Initial release with JSON logging, performance monitoring, correlation tracking, and diagnostic utilities