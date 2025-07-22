"""
Tests for the diagnostic utilities.

Tests the debugging and diagnostic logging functionality.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from hoopstat_observability.diagnostics import DiagnosticLogger, get_diagnostic_logger


class TestDiagnosticLogger:
    """Test cases for DiagnosticLogger class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.diagnostic_logger = DiagnosticLogger("test_diagnostics")

    @patch("hoopstat_observability.diagnostics.CorrelationContext")
    def test_log_system_info(self, mock_correlation):
        """Test logging system information."""
        mock_correlation.get_correlation_id.return_value = "test-123"

        with patch.object(self.diagnostic_logger.logger, "info") as mock_info:
            self.diagnostic_logger.log_system_info()

            mock_info.assert_called_once()
            call_args = mock_info.call_args[1]

            assert "system_info" in call_args
            assert call_args["correlation_id"] == "test-123"

            # Verify system info contains expected fields
            system_info = call_args["system_info"]
            assert "python_version" in system_info
            assert "platform" in system_info
            assert "hostname" in system_info

    def test_log_function_entry(self):
        """Test logging function entry."""
        with patch.object(self.diagnostic_logger.logger, "debug") as mock_debug:
            self.diagnostic_logger.log_function_entry(
                "test_function",
                args=(1, 2),
                kwargs={"param1": "value1", "password": "secret"},
            )

            mock_debug.assert_called_once()
            call_args = mock_debug.call_args[1]

            assert call_args["function_name"] == "test_function"
            assert call_args["arg_count"] == 2
            assert call_args["kwargs"]["param1"] == "value1"
            assert (
                call_args["kwargs"]["password"] == "[MASKED]"
            )  # Sensitive data masked

    def test_log_function_exit(self):
        """Test logging function exit."""
        with patch.object(self.diagnostic_logger.logger, "debug") as mock_debug:
            result = {"data": "test", "count": 5}

            self.diagnostic_logger.log_function_exit(
                "test_function", result=result, duration=1.234
            )

            mock_debug.assert_called_once()
            call_args = mock_debug.call_args[1]

            assert call_args["function_name"] == "test_function"
            assert call_args["duration_seconds"] == 1.234
            assert call_args["result_info"]["type"] == "dict"
            assert call_args["result_info"]["length"] == 2

    def test_log_exception(self):
        """Test logging exceptions."""
        test_exception = ValueError("Test error message")
        context = {"operation": "test_operation", "data_size": 100}

        with patch.object(self.diagnostic_logger.logger, "error") as mock_error:
            self.diagnostic_logger.log_exception(test_exception, context)

            mock_error.assert_called_once()
            call_args = mock_error.call_args[1]

            assert call_args["context"] == context
            exception_info = call_args["exception_info"]
            assert exception_info["type"] == "ValueError"
            assert exception_info["message"] == "Test error message"
            assert "traceback" in exception_info

    def test_log_performance_warning_exceeds_threshold(self):
        """Test performance warning when threshold is exceeded."""
        with patch.object(self.diagnostic_logger.logger, "warning") as mock_warning:
            self.diagnostic_logger.log_performance_warning(
                operation="slow_operation",
                duration=2.5,
                threshold=1.0,
                context={"batch_size": 1000},
            )

            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[1]

            assert call_args["operation"] == "slow_operation"
            assert call_args["duration_seconds"] == 2.5
            assert call_args["threshold_seconds"] == 1.0
            assert call_args["exceeded_by_seconds"] == 1.5
            assert call_args["context"]["batch_size"] == 1000

    def test_log_performance_warning_under_threshold(self):
        """Test no warning when under threshold."""
        with patch.object(self.diagnostic_logger.logger, "warning") as mock_warning:
            self.diagnostic_logger.log_performance_warning(
                operation="fast_operation", duration=0.5, threshold=1.0
            )

            # Should not log warning when under threshold
            mock_warning.assert_not_called()

    @patch("builtins.__import__")
    def test_log_memory_usage_success(self, mock_import):
        """Test successful memory usage logging."""
        # Mock psutil module and its components
        mock_psutil = MagicMock()
        mock_process = MagicMock()
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100MB
        mock_memory_info.vms = 200 * 1024 * 1024  # 200MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.memory_percent.return_value = 15.5
        mock_psutil.Process.return_value = mock_process

        # Setup import mock to return our mock psutil
        def import_side_effect(name, *args, **kwargs):
            if name == "psutil":
                return mock_psutil
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = import_side_effect

        with patch.object(self.diagnostic_logger.logger, "info") as mock_info:
            self.diagnostic_logger.log_memory_usage()

            mock_info.assert_called_once()
            call_args = mock_info.call_args[1]

            assert call_args["memory_rss_mb"] == 100.0
            assert call_args["memory_vms_mb"] == 200.0
            assert call_args["memory_percent"] == 15.5

    @patch("builtins.__import__")
    def test_log_memory_usage_psutil_not_available(self, mock_import):
        """Test memory usage logging when psutil is not available."""

        # Setup import mock to raise ImportError for psutil
        def import_side_effect(name, *args, **kwargs):
            if name == "psutil":
                raise ImportError("No module named 'psutil'")
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = import_side_effect

        with patch.object(self.diagnostic_logger.logger, "debug") as mock_debug:
            self.diagnostic_logger.log_memory_usage()

            mock_debug.assert_called_once_with(
                "psutil not available for memory monitoring"
            )

    def test_trace_execution_decorator_success(self):
        """Test trace_execution decorator for successful function."""
        with (
            patch.object(self.diagnostic_logger, "log_function_entry") as mock_entry,
            patch.object(self.diagnostic_logger, "log_function_exit") as mock_exit,
            patch.object(
                self.diagnostic_logger, "log_performance_warning"
            ) as mock_warning,
        ):

            @self.diagnostic_logger.trace_execution
            def test_function(arg1, kwarg1="test"):
                time.sleep(0.01)  # Small delay
                return "result"

            result = test_function("value1", kwarg1="value2")

            assert result == "result"

            # Verify all logging methods were called
            mock_entry.assert_called_once_with(
                "test_function", ("value1",), {"kwarg1": "value2"}
            )
            mock_exit.assert_called_once()
            mock_warning.assert_called_once()

            # Check exit call arguments
            exit_args = mock_exit.call_args[0]
            assert exit_args[0] == "test_function"
            assert exit_args[1] == "result"
            assert exit_args[2] > 0  # Duration should be positive

    def test_trace_execution_decorator_exception(self):
        """Test trace_execution decorator when exception occurs."""
        with (
            patch.object(self.diagnostic_logger, "log_function_entry") as mock_entry,
            patch.object(self.diagnostic_logger, "log_exception") as mock_exception,
        ):

            @self.diagnostic_logger.trace_execution
            def failing_function():
                time.sleep(0.01)
                raise ValueError("Test error")

            with pytest.raises(ValueError, match="Test error"):
                failing_function()

            # Verify entry and exception logging
            mock_entry.assert_called_once()
            mock_exception.assert_called_once()

            # Check exception call arguments
            exception_args = mock_exception.call_args
            exception_obj = exception_args[0][0]
            context = exception_args[0][1]

            assert isinstance(exception_obj, ValueError)
            assert str(exception_obj) == "Test error"
            assert context["function"] == "failing_function"
            assert context["duration_before_exception"] > 0


class TestGetDiagnosticLogger:
    """Test cases for get_diagnostic_logger function."""

    def test_get_diagnostic_logger(self):
        """Test getting diagnostic logger instance."""
        logger = get_diagnostic_logger("test_module")

        assert isinstance(logger, DiagnosticLogger)
        assert logger.name == "test_module"
