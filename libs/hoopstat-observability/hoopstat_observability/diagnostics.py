"""
Debugging and diagnostic utilities for enhanced observability.

Provides tools for debugging, system information gathering, and
diagnostic logging to support troubleshooting and monitoring.
"""

import os
import platform
import sys
import traceback
from typing import Any

from .correlation import CorrelationContext
from .json_logger import get_logger

# Get logger for diagnostics
logger = get_logger(__name__)


class DiagnosticLogger:
    """
    Enhanced logger for debugging and diagnostic information.

    Provides utilities for capturing system state, performance metrics,
    and detailed debugging information with structured logging.
    """

    def __init__(self, name: str):
        """
        Initialize diagnostic logger.

        Args:
            name: Logger name (typically __name__ of calling module)
        """
        self.logger = get_logger(name)
        self.name = name

    def log_system_info(self) -> None:
        """Log system and environment information for diagnostics."""
        system_info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "environment_variables": {
                k: v
                for k, v in os.environ.items()
                if not k.startswith(("AWS_", "SECRET_", "PASSWORD", "TOKEN"))
            },
        }

        self.logger.info(
            "System diagnostic information captured",
            system_info=system_info,
            correlation_id=CorrelationContext.get_correlation_id(),
        )

    def log_function_entry(
        self, func_name: str, args: tuple = (), kwargs: dict[str, Any] | None = None
    ) -> None:
        """
        Log function entry with parameters for debugging.

        Args:
            func_name: Name of the function being entered
            args: Positional arguments (sensitive data will be masked)
            kwargs: Keyword arguments (sensitive data will be masked)
        """
        # Mask sensitive parameter names
        sensitive_keys = {"password", "secret", "key", "token", "credential"}
        safe_kwargs = {}

        if kwargs:
            for key, value in kwargs.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    safe_kwargs[key] = "[MASKED]"
                else:
                    safe_kwargs[key] = str(value)[:100]  # Truncate long values

        self.logger.debug(
            f"Function entry: {func_name}",
            function_name=func_name,
            arg_count=len(args),
            kwargs=safe_kwargs,
            correlation_id=CorrelationContext.get_correlation_id(),
        )

    def log_function_exit(
        self, func_name: str, result: Any = None, duration: float | None = None
    ) -> None:
        """
        Log function exit with result information.

        Args:
            func_name: Name of the function being exited
            result: Function result (will be summarized, not logged in full)
            duration: Function execution duration in seconds
        """
        result_info = {
            "type": type(result).__name__,
            "is_none": result is None,
        }

        # Add safe result summary
        if hasattr(result, "__len__"):
            try:
                result_info["length"] = len(result)
            except (TypeError, AttributeError):
                pass

        log_data = {
            "function_name": func_name,
            "result_info": result_info,
            "correlation_id": CorrelationContext.get_correlation_id(),
        }

        if duration is not None:
            log_data["duration_seconds"] = round(duration, 3)

        self.logger.debug(f"Function exit: {func_name}", **log_data)

    def log_exception(
        self, exception: Exception, context: dict[str, Any] | None = None
    ) -> None:
        """
        Log exception with full traceback and context.

        Args:
            exception: Exception that occurred
            context: Additional context information
        """
        exception_info = {
            "type": type(exception).__name__,
            "message": str(exception),
            "traceback": traceback.format_exc(),
            "module": getattr(exception, "__module__", "unknown"),
        }

        log_data = {
            "exception_info": exception_info,
            "correlation_id": CorrelationContext.get_correlation_id(),
        }

        if context:
            log_data["context"] = context

        self.logger.error("Exception occurred", **log_data)

    def log_performance_warning(
        self,
        operation: str,
        duration: float,
        threshold: float = 1.0,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Log performance warning when operation exceeds threshold.

        Args:
            operation: Name of the operation
            duration: Actual duration in seconds
            threshold: Warning threshold in seconds
            context: Additional context information
        """
        if duration > threshold:
            log_data = {
                "operation": operation,
                "duration_seconds": round(duration, 3),
                "threshold_seconds": threshold,
                "exceeded_by_seconds": round(duration - threshold, 3),
                "correlation_id": CorrelationContext.get_correlation_id(),
            }

            if context:
                log_data["context"] = context

            self.logger.warning("Performance threshold exceeded", **log_data)

    def log_memory_usage(self) -> None:
        """Log current memory usage for diagnostics."""
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()

            self.logger.info(
                "Memory usage captured",
                memory_rss_mb=round(memory_info.rss / 1024 / 1024, 2),
                memory_vms_mb=round(memory_info.vms / 1024 / 1024, 2),
                memory_percent=round(process.memory_percent(), 2),
                correlation_id=CorrelationContext.get_correlation_id(),
            )
        except ImportError:
            self.logger.debug("psutil not available for memory monitoring")
        except Exception as e:
            self.logger.warning("Failed to capture memory usage", error=str(e))

    def trace_execution(self, func):
        """
        Decorator for detailed function execution tracing.

        Logs entry, exit, duration, and any exceptions for the decorated function.

        Example:
            @diagnostics.trace_execution
            def complex_operation():
                # Function implementation
                pass
        """

        def wrapper(*args, **kwargs):
            import time

            # Log function entry
            self.log_function_entry(func.__name__, args, kwargs)

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Log function exit
                self.log_function_exit(func.__name__, result, duration)

                # Check for performance issues
                self.log_performance_warning(func.__name__, duration)

                return result

            except Exception as e:
                duration = time.time() - start_time

                # Log exception with context
                context = {
                    "function": func.__name__,
                    "duration_before_exception": round(duration, 3),
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()) if kwargs else [],
                }
                self.log_exception(e, context)

                raise

        return wrapper


def get_diagnostic_logger(name: str) -> DiagnosticLogger:
    """
    Get a diagnostic logger instance.

    Args:
        name: Logger name (typically __name__ of calling module)

    Returns:
        Configured DiagnosticLogger instance

    Example:
        diagnostics = get_diagnostic_logger(__name__)
        diagnostics.log_system_info()
    """
    return DiagnosticLogger(name)
