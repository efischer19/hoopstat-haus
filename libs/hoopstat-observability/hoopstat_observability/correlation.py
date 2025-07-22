"""
Correlation context management for request tracing across services.

Provides utilities for tracking requests across distributed components
and maintaining correlation IDs for observability and debugging.
"""

import threading
import uuid
from collections.abc import Generator
from contextlib import contextmanager

from .json_logger import get_logger

# Thread-local storage for correlation context
_context = threading.local()

# Get logger for correlation tracking
logger = get_logger(__name__)


class CorrelationContext:
    """
    Manages correlation IDs for request tracing.

    Provides thread-safe storage and retrieval of correlation IDs
    to enable tracking requests across multiple services and operations.
    """

    @staticmethod
    def get_correlation_id() -> str | None:
        """
        Get the current correlation ID for this thread.

        Returns:
            Current correlation ID or None if not set
        """
        return getattr(_context, "correlation_id", None)

    @staticmethod
    def set_correlation_id(correlation_id: str) -> None:
        """
        Set the correlation ID for this thread.

        Args:
            correlation_id: Unique identifier for request correlation
        """
        _context.correlation_id = correlation_id
        logger.debug("Correlation ID set", correlation_id=correlation_id)

    @staticmethod
    def generate_correlation_id() -> str:
        """
        Generate a new UUID-based correlation ID.

        Returns:
            New correlation ID
        """
        return str(uuid.uuid4())

    @staticmethod
    def clear_correlation_id() -> None:
        """Clear the correlation ID for this thread."""
        if hasattr(_context, "correlation_id"):
            delattr(_context, "correlation_id")
            logger.debug("Correlation ID cleared")


@contextmanager
def correlation_context(
    correlation_id: str | None = None,
) -> Generator[str, None, None]:
    """
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
    """
    # Store previous correlation ID to restore later
    previous_id = CorrelationContext.get_correlation_id()

    # Use provided ID or generate new one
    current_id = correlation_id or CorrelationContext.generate_correlation_id()

    try:
        CorrelationContext.set_correlation_id(current_id)
        logger.info(
            "Started operation with correlation tracking", correlation_id=current_id
        )
        yield current_id

    finally:
        # Restore previous correlation ID
        if previous_id:
            CorrelationContext.set_correlation_id(previous_id)
        else:
            CorrelationContext.clear_correlation_id()

        logger.debug(
            "Correlation context restored",
            previous_id=previous_id,
            current_id=current_id,
        )


def with_correlation(func):
    """
    Decorator to automatically include correlation ID in function logging.

    Any logging performed within the decorated function will automatically
    include the current correlation ID.

    Example:
        @with_correlation
        def process_data():
            logger.info("Processing started")  # Will include correlation_id
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        correlation_id = CorrelationContext.get_correlation_id()
        if correlation_id:
            logger.debug(
                "Function called with correlation tracking",
                function=func.__name__,
                correlation_id=correlation_id,
            )
        return func(*args, **kwargs)

    return wrapper
