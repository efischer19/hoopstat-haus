"""
Tests for the correlation context functionality.

Tests the correlation ID management and request tracing capabilities.
"""

import threading
import time
from unittest.mock import patch

import pytest

from hoopstat_observability.correlation import (
    CorrelationContext,
    correlation_context,
    with_correlation,
)


class TestCorrelationContext:
    """Test cases for CorrelationContext class."""

    def setup_method(self):
        """Clear correlation context before each test."""
        CorrelationContext.clear_correlation_id()

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID."""
        test_id = "test-correlation-123"

        # Initially no correlation ID
        assert CorrelationContext.get_correlation_id() is None

        # Set correlation ID
        CorrelationContext.set_correlation_id(test_id)
        assert CorrelationContext.get_correlation_id() == test_id

        # Clear correlation ID
        CorrelationContext.clear_correlation_id()
        assert CorrelationContext.get_correlation_id() is None

    def test_generate_correlation_id(self):
        """Test correlation ID generation."""
        id1 = CorrelationContext.generate_correlation_id()
        id2 = CorrelationContext.generate_correlation_id()

        # Should generate unique IDs
        assert id1 != id2
        assert len(id1) > 0
        assert len(id2) > 0

        # Should be valid UUID format
        assert "-" in id1
        assert "-" in id2

    def test_thread_isolation(self):
        """Test that correlation IDs are isolated between threads."""
        results = {}

        def thread_worker(thread_id):
            correlation_id = f"thread-{thread_id}"
            CorrelationContext.set_correlation_id(correlation_id)
            time.sleep(0.01)  # Small delay to ensure threads overlap
            results[thread_id] = CorrelationContext.get_correlation_id()

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=thread_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify each thread maintained its own correlation ID
        assert results[0] == "thread-0"
        assert results[1] == "thread-1"
        assert results[2] == "thread-2"


class TestCorrelationContextManager:
    """Test cases for correlation_context context manager."""

    def setup_method(self):
        """Clear correlation context before each test."""
        CorrelationContext.clear_correlation_id()

    def test_context_with_provided_id(self):
        """Test context manager with provided correlation ID."""
        test_id = "provided-123"

        with correlation_context(test_id) as ctx_id:
            assert ctx_id == test_id
            assert CorrelationContext.get_correlation_id() == test_id

        # Should be cleared after context
        assert CorrelationContext.get_correlation_id() is None

    def test_context_with_generated_id(self):
        """Test context manager with auto-generated correlation ID."""
        with correlation_context() as ctx_id:
            assert ctx_id is not None
            assert len(ctx_id) > 0
            assert CorrelationContext.get_correlation_id() == ctx_id

        # Should be cleared after context
        assert CorrelationContext.get_correlation_id() is None

    def test_context_restoration(self):
        """Test that previous correlation ID is restored."""
        # Set initial correlation ID
        initial_id = "initial-123"
        CorrelationContext.set_correlation_id(initial_id)

        # Use context with different ID
        with correlation_context("temporary-456") as temp_id:
            assert temp_id == "temporary-456"
            assert CorrelationContext.get_correlation_id() == "temporary-456"

        # Should restore initial ID
        assert CorrelationContext.get_correlation_id() == initial_id

    def test_context_with_exception(self):
        """Test that correlation ID is properly restored even with exceptions."""
        initial_id = "initial-789"
        CorrelationContext.set_correlation_id(initial_id)

        with pytest.raises(ValueError, match="Test exception"):
            with correlation_context("exception-test"):
                raise ValueError("Test exception")

        # Should restore initial ID even after exception
        assert CorrelationContext.get_correlation_id() == initial_id

    def test_nested_contexts(self):
        """Test nested correlation contexts."""
        with correlation_context("outer-123"):
            assert CorrelationContext.get_correlation_id() == "outer-123"

            with correlation_context("inner-456") as inner_id:
                assert CorrelationContext.get_correlation_id() == "inner-456"
                assert inner_id == "inner-456"

            # Should restore outer context
            assert CorrelationContext.get_correlation_id() == "outer-123"

        # Should be cleared after all contexts
        assert CorrelationContext.get_correlation_id() is None


class TestWithCorrelationDecorator:
    """Test cases for with_correlation decorator."""

    def setup_method(self):
        """Clear correlation context before each test."""
        CorrelationContext.clear_correlation_id()

    @patch("hoopstat_observability.correlation.logger")
    def test_decorator_with_correlation_id(self, mock_logger):
        """Test decorator when correlation ID is set."""
        CorrelationContext.set_correlation_id("test-correlation")

        @with_correlation
        def test_function():
            return "result"

        result = test_function()
        assert result == "result"

        # Verify debug logging was called at least once for the function call
        # (may be called multiple times due to correlation ID setting)
        assert mock_logger.debug.call_count >= 1

        # Check that at least one call was for the function
        function_calls = [
            call
            for call in mock_logger.debug.call_args_list
            if len(call[1]) > 0 and call[1].get("function") == "test_function"
        ]
        assert len(function_calls) >= 1

        call_args = function_calls[0][1]
        assert call_args["function"] == "test_function"
        assert call_args["correlation_id"] == "test-correlation"

    @patch("hoopstat_observability.correlation.logger")
    def test_decorator_without_correlation_id(self, mock_logger):
        """Test decorator when no correlation ID is set."""

        @with_correlation
        def test_function():
            return "result"

        result = test_function()
        assert result == "result"

        # Should not log when no correlation ID
        mock_logger.debug.assert_not_called()

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""

        @with_correlation
        def test_function():
            """Test function docstring."""
            return "result"

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function docstring."
