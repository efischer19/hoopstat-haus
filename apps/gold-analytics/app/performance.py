"""
Performance monitoring utilities for Gold Analytics data pipeline.

This module provides performance monitoring decorators and context managers
following the same patterns as the example calculator app.
"""

import json
import logging
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any, TypeVar

# Configure logger for structured JSON output
logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def performance_monitor(
    job_name: str | None = None,
    records_processed_key: str = "records_processed",
) -> Callable[[F], F]:
    """
    Decorator to monitor performance of Gold analytics functions.

    Args:
        job_name: Name of the job (defaults to function name)
        records_processed_key: Key to extract record count from return value

    Returns:
        Decorated function with performance monitoring

    Example:
        @performance_monitor("silver_data_loading")
        def load_silver_data(date):
            # ... processing logic ...
            return {"records_processed": 1500, "data": df}
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            actual_job_name = job_name or func.__name__
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                records_processed = _extract_records_processed(
                    result, records_processed_key
                )

                _log_performance_metrics(
                    job_name=actual_job_name,
                    duration_in_seconds=duration,
                    records_processed=records_processed,
                    status="success",
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                _log_performance_metrics(
                    job_name=actual_job_name,
                    duration_in_seconds=duration,
                    records_processed=0,
                    status="failed",
                    error=str(e),
                )

                raise

        return wrapper

    return decorator


@contextmanager
def performance_context(
    job_name: str,
    records_processed: int = 0,
) -> Generator[dict[str, Any], None, None]:
    """
    Context manager to monitor Gold analytics pipeline performance.

    Automatically logs execution duration and allows dynamic record count tracking.

    Args:
        job_name: Name of the Gold analytics job.
        records_processed: Initial record count (default: 0).

    Yields:
        Context dict with 'records_processed' key that can be updated during execution.

    Example:
        with performance_context("gold_analytics_processing", 0) as ctx:
            for batch in process_silver_data():
                analytics = calculate_analytics(batch)
                store_analytics(analytics)
                ctx["records_processed"] += len(analytics)
    """
    start_time = time.time()
    context = {"records_processed": records_processed}

    try:
        yield context
        duration = time.time() - start_time

        _log_performance_metrics(
            job_name=job_name,
            duration_in_seconds=duration,
            records_processed=context["records_processed"],
            status="success",
        )

    except Exception as e:
        duration = time.time() - start_time

        _log_performance_metrics(
            job_name=job_name,
            duration_in_seconds=duration,
            records_processed=context["records_processed"],
            status="failed",
            error=str(e),
        )

        raise


def _extract_records_processed(
    result: Any, records_processed_key: str = "records_processed"
) -> int:
    """
    Extract the number of records processed from function result.

    Args:
        result: Function return value
        records_processed_key: Key to look for in result

    Returns:
        Number of records processed (0 if not found or not extractable)
    """
    try:
        if isinstance(result, dict) and records_processed_key in result:
            return int(result[records_processed_key])
        elif hasattr(result, "__len__"):
            return len(result)
        else:
            return 0
    except (TypeError, ValueError):
        return 0


def _log_performance_metrics(
    job_name: str,
    duration_in_seconds: float,
    records_processed: int,
    status: str,
    error: str | None = None,
) -> None:
    """
    Log performance metrics in structured JSON format.

    Args:
        job_name: Name of the job
        duration_in_seconds: How long the job took
        records_processed: Number of records processed
        status: Job status ("success" or "failed")
        error: Error message if status is "failed"
    """
    log_data = {
        "event_type": "performance_metric",
        "job_name": job_name,
        "duration_seconds": round(duration_in_seconds, 3),
        "records_processed": records_processed,
        "status": status,
        "timestamp": time.time(),
    }

    if error:
        log_data["error"] = error

    # Calculate throughput if we have both duration and records
    if duration_in_seconds > 0 and records_processed > 0:
        log_data["records_per_second"] = round(
            records_processed / duration_in_seconds, 2
        )

    if status == "success":
        logger.info(json.dumps(log_data))
    else:
        logger.error(json.dumps(log_data))
