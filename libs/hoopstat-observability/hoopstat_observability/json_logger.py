"""
JSON logging utilities implementing ADR-015 structured logging standards.

Provides standardized JSON logging functionality with consistent format,
automatic timestamp handling, and CloudWatch integration support.
"""

import json
import logging
import time
from typing import Any


class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs structured JSON logs per ADR-015.

    Ensures consistent format across all log entries with required fields
    for CloudWatch metric extraction and observability.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured JSON.

        Args:
            record: Python logging record to format

        Returns:
            JSON string formatted according to ADR-015 standards
        """
        log_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields from the record
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "exc_info",
                "exc_text",
                "stack_info",
            }:
                log_data[key] = value

        return json.dumps(log_data)


class JSONLogger:
    """
    Standardized logger that outputs structured JSON per ADR-015.

    Provides convenience methods for common logging patterns and ensures
    consistent structure across all log entries.
    """

    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize JSON logger.

        Args:
            name: Logger name (typically __name__ of calling module)
            level: Logging level (default: INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Remove existing handlers to avoid duplication
        self.logger.handlers.clear()

        # Create handler with JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info level message with optional extra fields."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning level message with optional extra fields."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error level message with optional extra fields."""
        self.logger.error(message, extra=kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug level message with optional extra fields."""
        self.logger.debug(message, extra=kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical level message with optional extra fields."""
        self.logger.critical(message, extra=kwargs)

    def log_performance(
        self,
        job_name: str,
        duration_in_seconds: float,
        records_processed: int,
        status: str = "success",
        **kwargs: Any,
    ) -> None:
        """
        Log performance metrics in ADR-015 standard format.

        Args:
            job_name: Name of the job or operation
            duration_in_seconds: Execution time in seconds
            records_processed: Number of records processed
            status: Job status (success/failed)
            **kwargs: Additional context fields
        """
        level_method = self.info if status == "success" else self.error
        level_method(
            f"Data pipeline job {status}",
            job_name=job_name,
            duration_in_seconds=round(duration_in_seconds, 3),
            records_processed=records_processed,
            status=status,
            **kwargs,
        )

    def log_with_correlation(
        self,
        level: str,
        message: str,
        correlation_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Log message with correlation ID for request tracing.

        Args:
            level: Log level (info, warning, error, debug, critical)
            message: Log message
            correlation_id: Correlation ID for request tracing
            **kwargs: Additional context fields
        """
        log_method = getattr(self, level.lower())
        extra_fields = kwargs.copy()

        if correlation_id:
            extra_fields["correlation_id"] = correlation_id

        log_method(message, **extra_fields)


def get_logger(name: str, level: int = logging.INFO) -> JSONLogger:
    """
    Get a standardized JSON logger instance.

    Args:
        name: Logger name (typically __name__ of calling module)
        level: Logging level (default: INFO)

    Returns:
        Configured JSONLogger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Application started", version="1.0.0")
    """
    return JSONLogger(name, level)
