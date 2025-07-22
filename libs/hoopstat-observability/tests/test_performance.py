"""
Tests for the performance monitoring functionality.

Tests the performance monitoring decorators and context managers,
ensuring proper metric collection and logging per ADR-015.
"""

import json
import pytest
import time
from io import StringIO
from unittest.mock import patch

from hoopstat_observability.performance import (
    performance_monitor, 
    performance_context,
    _extract_records_processed
)


class TestPerformanceMonitor:
    """Test cases for performance_monitor decorator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.log_output = StringIO()
    
    @patch('hoopstat_observability.performance.logger')
    def test_performance_monitor_success(self, mock_logger):
        """Test performance monitoring for successful function."""
        @performance_monitor(job_name="test_job")
        def test_function():
            time.sleep(0.01)  # Small delay for measurable duration
            return 100  # Return record count
        
        result = test_function()
        
        assert result == 100
        
        # Verify performance logging was called
        mock_logger.log_performance.assert_called_once()
        call_args = mock_logger.log_performance.call_args[1]
        
        assert call_args["job_name"] == "test_job"
        assert call_args["records_processed"] == 100
        assert call_args["status"] == "success"
        assert call_args["duration_in_seconds"] > 0
    
    @patch('hoopstat_observability.performance.logger')
    def test_performance_monitor_default_job_name(self, mock_logger):
        """Test performance monitoring with default job name."""
        @performance_monitor()
        def my_function():
            return {"records_processed": 50, "status": "complete"}
        
        result = my_function()
        
        assert result["records_processed"] == 50
        
        # Verify job name defaults to function name
        call_args = mock_logger.log_performance.call_args[1]
        assert call_args["job_name"] == "my_function"
        assert call_args["records_processed"] == 50
    
    @patch('hoopstat_observability.performance.logger')
    def test_performance_monitor_exception(self, mock_logger):
        """Test performance monitoring when exception occurs."""
        @performance_monitor(job_name="failing_job")
        def failing_function():
            time.sleep(0.01)
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            failing_function()
        
        # Verify error logging
        call_args = mock_logger.log_performance.call_args[1]
        assert call_args["job_name"] == "failing_job"
        assert call_args["records_processed"] == 0
        assert call_args["status"] == "failed"
        assert call_args["error"] == "Test error"
        assert call_args["error_type"] == "ValueError"
        assert call_args["duration_in_seconds"] > 0
    
    @patch('hoopstat_observability.performance.logger')
    def test_performance_monitor_custom_key(self, mock_logger):
        """Test performance monitoring with custom records key."""
        @performance_monitor(records_processed_key="total_items")
        def process_items():
            return {"total_items": 75, "other_data": "value"}
        
        result = process_items()
        
        # Verify custom key extraction
        call_args = mock_logger.log_performance.call_args[1]
        assert call_args["records_processed"] == 75


class TestPerformanceContext:
    """Test cases for performance_context context manager."""
    
    @patch('hoopstat_observability.performance.logger')
    def test_performance_context_success(self, mock_logger):
        """Test performance context for successful operation."""
        with performance_context("context_job") as ctx:
            time.sleep(0.01)
            ctx["records_processed"] = 200
        
        # Verify performance logging
        call_args = mock_logger.log_performance.call_args[1]
        assert call_args["job_name"] == "context_job"
        assert call_args["records_processed"] == 200
        assert call_args["status"] == "success"
        assert call_args["duration_in_seconds"] > 0
    
    @patch('hoopstat_observability.performance.logger')
    def test_performance_context_with_initial_count(self, mock_logger):
        """Test performance context with initial record count."""
        with performance_context("context_job", records_processed=50) as ctx:
            ctx["records_processed"] += 25
        
        call_args = mock_logger.log_performance.call_args[1]
        assert call_args["records_processed"] == 75
    
    @patch('hoopstat_observability.performance.logger')
    def test_performance_context_exception(self, mock_logger):
        """Test performance context when exception occurs."""
        with pytest.raises(RuntimeError, match="Context error"):
            with performance_context("failing_context") as ctx:
                ctx["records_processed"] = 10
                raise RuntimeError("Context error")
        
        # Verify error logging
        call_args = mock_logger.log_performance.call_args[1]
        assert call_args["job_name"] == "failing_context"
        assert call_args["records_processed"] == 10
        assert call_args["status"] == "failed"
        assert call_args["error"] == "Context error"
        assert call_args["error_type"] == "RuntimeError"


class TestExtractRecordsProcessed:
    """Test cases for _extract_records_processed function."""
    
    def test_extract_integer_result(self):
        """Test extracting record count from integer result."""
        assert _extract_records_processed(100) == 100
        assert _extract_records_processed(42.7) == 42
    
    def test_extract_dict_result_default_key(self):
        """Test extracting record count from dict with default key."""
        result = {"records_processed": 150, "status": "success"}
        assert _extract_records_processed(result) == 150
    
    def test_extract_dict_result_custom_key(self):
        """Test extracting record count from dict with custom key."""
        result = {"total_records": 75, "processed": True}
        assert _extract_records_processed(result, "total_records") == 75
    
    def test_extract_object_attribute(self):
        """Test extracting record count from object attribute."""
        class Result:
            def __init__(self):
                self.records_processed = 200
        
        result = Result()
        assert _extract_records_processed(result) == 200
    
    def test_extract_no_match(self):
        """Test extracting when no record count can be determined."""
        assert _extract_records_processed("string_result") == 0
        assert _extract_records_processed({"other_key": 100}) == 0
        assert _extract_records_processed(None) == 0
    
    def test_extract_dict_missing_key(self):
        """Test extracting from dict missing the target key."""
        result = {"total": 50, "complete": True}
        assert _extract_records_processed(result, "records") == 0