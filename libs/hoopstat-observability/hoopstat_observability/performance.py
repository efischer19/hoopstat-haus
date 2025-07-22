"""
Performance monitoring utilities implementing ADR-015 performance metrics.

Consolidates performance monitoring functionality from existing applications,
providing decorators and context managers for automatic performance logging
with structured JSON output.
"""

import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any, TypeVar

from .json_logger import get_logger

# Type variable for function decorators
F = TypeVar("F", bound=Callable[..., Any])

# Get logger for performance monitoring
logger = get_logger(__name__)


def performance_monitor(
    job_name: str | None = None,
    records_processed_key: str = "records_processed",
) -> Callable[[F], F]:
    """
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
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            function_job_name = job_name or func.__name__

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Extract record count from result
                records_count = _extract_records_processed(
                    result, records_processed_key
                )

                # Log performance metrics
                logger.log_performance(
                    job_name=function_job_name,
                    duration_in_seconds=duration,
                    records_processed=records_count,
                    status="success",
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                # Log performance metrics for failed job
                logger.log_performance(
                    job_name=function_job_name,
                    duration_in_seconds=duration,
                    records_processed=0,
                    status="failed",
                    error=str(e),
                    error_type=type(e).__name__,
                )

                raise

        return wrapper  # type: ignore

    return decorator


@contextmanager
def performance_context(
    job_name: str,
    records_processed: int = 0,
) -> Generator[dict[str, Any], None, None]:
    """
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
    """
    start_time = time.time()
    context = {"records_processed": records_processed}

    try:
        yield context
        duration = time.time() - start_time

        logger.log_performance(
            job_name=job_name,
            duration_in_seconds=duration,
            records_processed=context["records_processed"],
            status="success",
        )

    except Exception as e:
        duration = time.time() - start_time

        logger.log_performance(
            job_name=job_name,
            duration_in_seconds=duration,
            records_processed=context["records_processed"],
            status="failed",
            error=str(e),
            error_type=type(e).__name__,
        )

        raise


def _extract_records_processed(
    result: Any, records_processed_key: str = "records_processed"
) -> int:
    """
    Extract record count from function result.

    Args:
        result: The return value from the monitored function.
        records_processed_key: Key to look for in dict results.

    Returns:
        Number of records processed.
    """
    if isinstance(result, int | float):
        return int(result)
    elif isinstance(result, dict) and records_processed_key in result:
        return int(result[records_processed_key])
    elif hasattr(result, "records_processed"):
        return int(result.records_processed)
    else:
        # Default to 0 if we can't determine record count
        return 0
