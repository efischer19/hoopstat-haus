"""Tests for the performance monitoring utilities."""

import json
import logging
import time
from unittest.mock import patch

import pytest

from hoopstat_common.performance import (
    _extract_records_processed,
    _log_performance_metrics,
    performance_context,
    performance_monitor,
)


class TestPerformanceMonitor:
    """Test cases for the performance_monitor decorator."""

    def test_monitor_function_returning_int(self, caplog):
        """Test monitoring function that returns record count as integer."""
        caplog.set_level(logging.INFO)

        @performance_monitor(job_name="test_job")
        def process_data():
            time.sleep(0.01)  # Small delay to test duration
            return 100

        result = process_data()

        assert result == 100
        assert len(caplog.records) == 1

        log_entry = json.loads(caplog.records[0].message)
        assert log_entry["job_name"] == "test_job"
        assert log_entry["records_processed"] == 100
        assert log_entry["status"] == "success"
        assert log_entry["duration_in_seconds"] >= 0.01
        assert "timestamp" in log_entry

    def test_monitor_function_returning_dict(self, caplog):
        """Test monitoring function that returns dict with record count."""
        caplog.set_level(logging.INFO)

        @performance_monitor()
        def process_users():
            return {"records_processed": 250, "status": "completed"}

        result = process_users()

        assert result["records_processed"] == 250
        assert len(caplog.records) == 1

        log_entry = json.loads(caplog.records[0].message)
        assert log_entry["job_name"] == "process_users"
        assert log_entry["records_processed"] == 250

    def test_monitor_function_with_custom_key(self, caplog):
        """Test monitoring function with custom records key."""
        caplog.set_level(logging.INFO)

        @performance_monitor(records_processed_key="total_rows")
        def import_data():
            return {"total_rows": 500, "errors": 0}

        result = import_data()

        assert result["total_rows"] == 500
        log_entry = json.loads(caplog.records[0].message)
        assert log_entry["records_processed"] == 500

    def test_monitor_function_with_object_attribute(self, caplog):
        """Test monitoring function returning object with records_processed."""
        caplog.set_level(logging.INFO)

        class ProcessResult:
            def __init__(self, count):
                self.records_processed = count

        @performance_monitor()
        def process_with_object():
            return ProcessResult(75)

        result = process_with_object()

        assert result.records_processed == 75
        log_entry = json.loads(caplog.records[0].message)
        assert log_entry["records_processed"] == 75

    def test_monitor_function_with_exception(self, caplog):
        """Test monitoring function that raises an exception."""
        caplog.set_level(logging.ERROR)

        @performance_monitor(job_name="failing_job")
        def failing_function():
            time.sleep(0.01)
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

        assert len(caplog.records) == 1
        log_entry = json.loads(caplog.records[0].message)
        assert log_entry["job_name"] == "failing_job"
        assert log_entry["status"] == "failed"
        assert log_entry["error"] == "Test error"
        assert log_entry["records_processed"] == 0
        assert log_entry["duration_in_seconds"] >= 0.01

    def test_monitor_function_unknown_return_type(self, caplog):
        """Test monitoring function with unknown return type defaults to 0 records."""
        caplog.set_level(logging.INFO)

        @performance_monitor()
        def unknown_return():
            return "some string"

        result = unknown_return()

        assert result == "some string"
        log_entry = json.loads(caplog.records[0].message)
        assert log_entry["records_processed"] == 0


class TestPerformanceContext:
    """Test cases for the performance_context context manager."""

    def test_context_basic_usage(self, caplog):
        """Test basic usage of performance context."""
        caplog.set_level(logging.INFO)

        with performance_context("test_context_job") as ctx:
            time.sleep(0.01)
            ctx["records_processed"] = 300

        assert len(caplog.records) == 1
        log_entry = json.loads(caplog.records[0].message)
        assert log_entry["job_name"] == "test_context_job"
        assert log_entry["records_processed"] == 300
        assert log_entry["status"] == "success"
        assert log_entry["duration_in_seconds"] >= 0.01

    def test_context_with_initial_count(self, caplog):
        """Test context manager with initial record count."""
        caplog.set_level(logging.INFO)

        with performance_context("batch_job", records_processed=50) as ctx:
            ctx["records_processed"] += 25

        log_entry = json.loads(caplog.records[0].message)
        assert log_entry["records_processed"] == 75

    def test_context_with_exception(self, caplog):
        """Test context manager when exception occurs."""
        caplog.set_level(logging.ERROR)

        with pytest.raises(RuntimeError, match="Context error"):
            with performance_context("error_job") as ctx:
                ctx["records_processed"] = 10
                time.sleep(0.01)
                raise RuntimeError("Context error")

        assert len(caplog.records) == 1
        log_entry = json.loads(caplog.records[0].message)
        assert log_entry["job_name"] == "error_job"
        assert log_entry["status"] == "failed"
        assert log_entry["error"] == "Context error"
        assert log_entry["records_processed"] == 10
        assert log_entry["duration_in_seconds"] >= 0.01

    def test_context_incremental_updates(self, caplog):
        """Test context manager with incremental record updates."""
        caplog.set_level(logging.INFO)

        with performance_context("batch_processor") as ctx:
            for _ in range(5):
                ctx["records_processed"] += 10

        log_entry = json.loads(caplog.records[0].message)
        assert log_entry["records_processed"] == 50


class TestExtractRecordsProcessed:
    """Test cases for _extract_records_processed helper function."""

    def test_extract_from_int(self):
        """Test extracting record count from integer."""
        assert _extract_records_processed(42) == 42

    def test_extract_from_dict_default_key(self):
        """Test extracting record count from dict with default key."""
        data = {"records_processed": 100, "other": "value"}
        assert _extract_records_processed(data) == 100

    def test_extract_from_dict_custom_key(self):
        """Test extracting record count from dict with custom key."""
        data = {"total_count": 75, "status": "done"}
        assert _extract_records_processed(data, "total_count") == 75

    def test_extract_from_object_attribute(self):
        """Test extracting record count from object attribute."""

        class Result:
            def __init__(self):
                self.records_processed = 33

        result = Result()
        assert _extract_records_processed(result) == 33

    def test_extract_from_unknown_type(self):
        """Test extracting record count from unknown type defaults to 0."""
        assert _extract_records_processed("unknown") == 0
        assert _extract_records_processed([1, 2, 3]) == 0
        assert _extract_records_processed({"wrong_key": 50}) == 0

    def test_extract_converts_to_int(self):
        """Test that extracted values are converted to integers."""
        assert _extract_records_processed(42.7) == 42
        assert _extract_records_processed({"records_processed": "123"}) == 123


class TestLogPerformanceMetrics:
    """Test cases for _log_performance_metrics helper function."""

    @patch("hoopstat_common.performance.time.strftime")
    def test_log_success_metrics(self, mock_strftime, caplog):
        """Test logging successful job metrics."""
        mock_strftime.return_value = "2025-01-27T10:00:00.000000Z"
        caplog.set_level(logging.INFO)

        _log_performance_metrics(
            job_name="test_job",
            duration_in_seconds=1.234567,
            records_processed=500,
            status="success",
        )

        assert len(caplog.records) == 1
        log_entry = json.loads(caplog.records[0].message)

        expected = {
            "timestamp": "2025-01-27T10:00:00.000000Z",
            "level": "INFO",
            "message": "Data pipeline job success",
            "job_name": "test_job",
            "duration_in_seconds": 1.235,  # Rounded to 3 decimal places
            "records_processed": 500,
            "status": "success",
        }

        assert log_entry == expected

    @patch("hoopstat_common.performance.time.strftime")
    def test_log_failed_metrics(self, mock_strftime, caplog):
        """Test logging failed job metrics."""
        mock_strftime.return_value = "2025-01-27T10:00:00.000000Z"
        caplog.set_level(logging.ERROR)

        _log_performance_metrics(
            job_name="failed_job",
            duration_in_seconds=0.5,
            records_processed=0,
            status="failed",
            error="Connection timeout",
        )

        assert len(caplog.records) == 1
        log_entry = json.loads(caplog.records[0].message)

        expected = {
            "timestamp": "2025-01-27T10:00:00.000000Z",
            "level": "ERROR",
            "message": "Data pipeline job failed",
            "job_name": "failed_job",
            "duration_in_seconds": 0.5,
            "records_processed": 0,
            "status": "failed",
            "error": "Connection timeout",
        }

        assert log_entry == expected


# Integration tests that demonstrate real-world usage patterns
class TestIntegrationExamples:
    """Integration tests showing real-world usage patterns."""

    def test_decorator_data_processing_pipeline(self, caplog):
        """Test decorator usage in a typical data processing pipeline."""
        caplog.set_level(logging.INFO)

        @performance_monitor(job_name="user_analytics_daily")
        def process_user_analytics():
            # Simulate data processing
            users_processed = 0
            for _ in range(5):  # 5 batches
                time.sleep(0.001)  # Simulate processing time
                users_processed += 50  # 50 users per batch

            return {"records_processed": users_processed, "errors": 0}

        result = process_user_analytics()

        assert result["records_processed"] == 250
        log_entry = json.loads(caplog.records[0].message)
        assert log_entry["job_name"] == "user_analytics_daily"
        assert log_entry["records_processed"] == 250
        assert log_entry["status"] == "success"

    def test_context_manager_streaming_pipeline(self, caplog):
        """Test context manager usage in a streaming data pipeline."""
        caplog.set_level(logging.INFO)

        def simulate_data_batches():
            """Simulate streaming data batches."""
            for _ in range(3):
                yield [f"record_{j}" for j in range(10)]

        with performance_context("streaming_processor") as ctx:
            for batch in simulate_data_batches():
                time.sleep(0.001)  # Simulate processing
                ctx["records_processed"] += len(batch)

        log_entry = json.loads(caplog.records[0].message)
        assert log_entry["job_name"] == "streaming_processor"
        assert log_entry["records_processed"] == 30
        assert log_entry["status"] == "success"
