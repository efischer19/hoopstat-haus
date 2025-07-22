"""
Tests for the JSON logging functionality.

Tests the structured JSON logging implementation, ensuring compliance
with ADR-015 logging standards and proper formatting.
"""

import json
import logging
from io import StringIO

from hoopstat_observability.json_logger import JSONFormatter, JSONLogger, get_logger


class TestJSONFormatter:
    """Test cases for JSONFormatter class."""

    def test_format_basic_record(self):
        """Test basic log record formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function",
            sinfo=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["logger"] == "test_logger"
        assert data["function"] == "test_function"
        assert data["line"] == 42
        assert "timestamp" in data
        assert data["timestamp"].endswith("Z")  # ISO format with Z suffix

    def test_format_with_extra_fields(self):
        """Test formatting with extra fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function",
            sinfo=None,
        )

        # Add extra fields
        record.job_name = "test_job"
        record.duration_in_seconds = 1.234
        record.records_processed = 100

        result = formatter.format(record)
        data = json.loads(result)

        assert data["job_name"] == "test_job"
        assert data["duration_in_seconds"] == 1.234
        assert data["records_processed"] == 100

    def test_format_with_exception(self):
        """Test formatting with exception information."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="/test/path.py",
                lineno=42,
                msg="Error occurred",
                args=(),
                exc_info=exc_info,
                func="test_function",
                sinfo=None,
            )

            result = formatter.format(record)
            data = json.loads(result)

            assert data["level"] == "ERROR"
            assert data["message"] == "Error occurred"
            assert "exception" in data
            assert "ValueError: Test exception" in data["exception"]


class TestJSONLogger:
    """Test cases for JSONLogger class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.log_output = StringIO()
        self.handler = logging.StreamHandler(self.log_output)

    def test_logger_initialization(self):
        """Test logger initialization and configuration."""
        logger = JSONLogger("test_logger")

        assert logger.logger.name == "test_logger"
        assert logger.logger.level == logging.INFO
        assert len(logger.logger.handlers) == 1
        assert isinstance(logger.logger.handlers[0].formatter, JSONFormatter)
        assert not logger.logger.propagate

    def test_info_logging(self):
        """Test info level logging."""
        from hoopstat_observability.json_logger import JSONFormatter

        logger = JSONLogger("test_logger")
        # Replace handler with our test handler that has JSON formatter
        logger.logger.handlers.clear()
        self.handler.setFormatter(JSONFormatter())
        logger.logger.addHandler(self.handler)

        logger.info("Test message", job_name="test_job")

        output = self.log_output.getvalue()
        data = json.loads(output.strip())

        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["job_name"] == "test_job"

    def test_error_logging(self):
        """Test error level logging."""
        from hoopstat_observability.json_logger import JSONFormatter

        logger = JSONLogger("test_logger")
        # Replace handler with our test handler that has JSON formatter
        logger.logger.handlers.clear()
        self.handler.setFormatter(JSONFormatter())
        logger.logger.addHandler(self.handler)

        logger.error("Error message", error_code=500)

        output = self.log_output.getvalue()
        data = json.loads(output.strip())

        assert data["level"] == "ERROR"
        assert data["message"] == "Error message"
        assert data["error_code"] == 500

    def test_log_performance_success(self):
        """Test performance logging for successful operations."""
        from hoopstat_observability.json_logger import JSONFormatter

        logger = JSONLogger("test_logger")
        # Replace handler with our test handler that has JSON formatter
        logger.logger.handlers.clear()
        self.handler.setFormatter(JSONFormatter())
        logger.logger.addHandler(self.handler)

        logger.log_performance(
            job_name="test_job",
            duration_in_seconds=1.234,
            records_processed=100,
            status="success",
        )

        output = self.log_output.getvalue()
        data = json.loads(output.strip())

        assert data["level"] == "INFO"
        assert data["message"] == "Data pipeline job success"
        assert data["job_name"] == "test_job"
        assert data["duration_in_seconds"] == 1.234
        assert data["records_processed"] == 100
        assert data["status"] == "success"

    def test_log_performance_failure(self):
        """Test performance logging for failed operations."""
        from hoopstat_observability.json_logger import JSONFormatter

        logger = JSONLogger("test_logger")
        # Replace handler with our test handler that has JSON formatter
        logger.logger.handlers.clear()
        self.handler.setFormatter(JSONFormatter())
        logger.logger.addHandler(self.handler)

        logger.log_performance(
            job_name="test_job",
            duration_in_seconds=0.567,
            records_processed=0,
            status="failed",
            error="Something went wrong",
        )

        output = self.log_output.getvalue()
        data = json.loads(output.strip())

        assert data["level"] == "ERROR"
        assert data["message"] == "Data pipeline job failed"
        assert data["job_name"] == "test_job"
        assert data["duration_in_seconds"] == 0.567
        assert data["records_processed"] == 0
        assert data["status"] == "failed"
        assert data["error"] == "Something went wrong"

    def test_log_with_correlation(self):
        """Test logging with correlation ID."""
        from hoopstat_observability.json_logger import JSONFormatter

        logger = JSONLogger("test_logger")
        # Replace handler with our test handler that has JSON formatter
        logger.logger.handlers.clear()
        self.handler.setFormatter(JSONFormatter())
        logger.logger.addHandler(self.handler)

        logger.log_with_correlation(
            level="info",
            message="Test message",
            correlation_id="test-123",
            extra_field="extra_value",
        )

        output = self.log_output.getvalue()
        data = json.loads(output.strip())

        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["correlation_id"] == "test-123"
        assert data["extra_field"] == "extra_value"


class TestGetLogger:
    """Test cases for get_logger function."""

    def test_get_logger_default_level(self):
        """Test get_logger with default level."""
        logger = get_logger("test_module")

        assert isinstance(logger, JSONLogger)
        assert logger.logger.name == "test_module"
        assert logger.logger.level == logging.INFO

    def test_get_logger_custom_level(self):
        """Test get_logger with custom level."""
        logger = get_logger("test_module", logging.DEBUG)

        assert isinstance(logger, JSONLogger)
        assert logger.logger.name == "test_module"
        assert logger.logger.level == logging.DEBUG
