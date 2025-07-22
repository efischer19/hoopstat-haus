"""
Integration tests for the hoopstat-observability library.

Tests the complete integration of all observability components
to ensure they work together properly.
"""

import json
import logging
import pytest
import time
from io import StringIO
from unittest.mock import patch, MagicMock

from hoopstat_observability import (
    JSONLogger,
    get_logger,
    performance_monitor,
    performance_context,
    correlation_context,
    CorrelationContext,
    DiagnosticLogger
)


class TestIntegratedObservability:
    """Integration tests for observability components."""
    
    def test_performance_monitoring_with_correlation(self):
        """Test performance monitoring with correlation tracking."""
        with patch('hoopstat_observability.performance.logger') as mock_perf_logger:
            with correlation_context("integration-test-123"):
                @performance_monitor(job_name="integrated_job")
                def test_operation():
                    # Verify correlation ID is available during execution
                    assert CorrelationContext.get_correlation_id() == "integration-test-123"
                    return 42
                
                result = test_operation()
                assert result == 42
            
            # Verify performance logging occurred
            mock_perf_logger.log_performance.assert_called_once()
    
    def test_diagnostic_tracing_with_performance_monitoring(self):
        """Test diagnostic tracing combined with performance monitoring."""
        diagnostics = DiagnosticLogger("integration_test")
        
        with patch.object(diagnostics, 'log_function_entry') as mock_entry, \
             patch.object(diagnostics, 'log_function_exit') as mock_exit:
            
            @diagnostics.trace_execution
            @performance_monitor(job_name="traced_job")
            def complex_operation(data_size):
                time.sleep(0.01)  # Simulate work
                return {"records_processed": data_size, "status": "complete"}
            
            result = complex_operation(100)
            
            assert result["records_processed"] == 100
            
            # Verify diagnostic tracing occurred
            mock_entry.assert_called_once()
            mock_exit.assert_called_once()
    
    def test_full_observability_stack(self):
        """Test complete observability stack integration."""
        with patch('hoopstat_observability.performance.logger') as mock_perf_logger:
            with patch('hoopstat_observability.diagnostics.get_logger') as mock_get_diag_logger:
                # Create mock diagnostic logger
                mock_diag_logger = MagicMock()
                mock_get_diag_logger.return_value = mock_diag_logger
                
                diagnostics = DiagnosticLogger("full_stack_test") 
                
                with correlation_context("full-stack-456") as corr_id:
                    # Log system information
                    diagnostics.log_system_info()
                    
                    # Perform monitored operation
                    with performance_context("full_stack_operation") as ctx:
                        # Simulate processing
                        for i in range(10):
                            ctx["records_processed"] += 1
                        
                        # Log custom metrics
                        logger = get_logger("test")
                        logger.log_with_correlation(
                            "info",
                            "Processing batch completed",
                            correlation_id=corr_id,
                            batch_size=10,
                            processing_time=0.05
                        )
                    
                    # Log memory usage if possible
                    diagnostics.log_memory_usage()
                
                # Verify various logging occurred
                mock_perf_logger.log_performance.assert_called_once()
                mock_diag_logger.info.assert_called()
    
    def test_error_handling_integration(self):
        """Test error handling across observability components."""
        logger = get_logger("error_test")
        diagnostics = DiagnosticLogger("error_test")
        
        with patch.object(logger.logger, 'error') as mock_error:
            with correlation_context("error-test-789"):
                @performance_monitor(job_name="error_job")
                def failing_operation():
                    raise RuntimeError("Integration test error")
                
                # Test that exceptions propagate correctly
                with pytest.raises(RuntimeError, match="Integration test error"):
                    failing_operation()
                
                # Test diagnostic exception logging
                try:
                    raise ValueError("Diagnostic test error")
                except ValueError as e:
                    diagnostics.log_exception(e, {"test": "context"})
            
            # Verify error logging occurred
            assert mock_error.called
    
    def test_adr_015_compliance(self):
        """Test that all logging output complies with ADR-015 standards."""
        log_output = StringIO()
        
        # Create logger with custom handler to capture output
        logger = get_logger("adr_compliance_test")
        logger.logger.handlers[0].stream = log_output
        
        with correlation_context("adr-test-compliance"):
            # Log performance metrics
            logger.log_performance(
                job_name="compliance_test",
                duration_in_seconds=1.234,
                records_processed=100,
                status="success"
            )
            
            # Log with correlation
            logger.log_with_correlation(
                "info",
                "ADR compliance test message",
                correlation_id="adr-test-compliance",
                test_field="test_value"
            )
        
        # Verify output format
        output_lines = log_output.getvalue().strip().split('\n')
        
        for line in output_lines:
            if line.strip():  # Skip empty lines
                # Parse as JSON to verify structure
                log_data = json.loads(line)
                
                # Verify required ADR-015 fields
                assert "timestamp" in log_data
                assert "level" in log_data
                assert "message" in log_data
                assert log_data["timestamp"].endswith("Z")  # ISO format
                
                # Verify structured format
                assert isinstance(log_data, dict)
    
    def test_cloudwatch_integration_fields(self):
        """Test that logs include fields needed for CloudWatch metric extraction."""
        # Create a real logger to test the actual behavior
        logger = get_logger("cloudwatch_test")
        
        # Capture the actual logging output
        from io import StringIO
        import json
        from hoopstat_observability.json_logger import JSONFormatter
        
        log_output = StringIO()
        handler = logging.StreamHandler(log_output)
        handler.setFormatter(JSONFormatter())
        
        # Replace logger's handler temporarily
        original_handlers = logger.logger.handlers.copy()
        logger.logger.handlers.clear()
        logger.logger.addHandler(handler)
        
        try:
            # Test performance logging with CloudWatch fields
            logger.log_performance(
                job_name="cloudwatch_test_job",
                duration_in_seconds=2.567,
                records_processed=500,
                status="success"
            )
            
            # Parse the logged output
            output = log_output.getvalue().strip()
            data = json.loads(output)
            
            # Verify required CloudWatch extraction fields per ADR-015
            assert "duration_in_seconds" in data
            assert "records_processed" in data
            assert "job_name" in data
            
            # Verify field types and values
            assert isinstance(data["duration_in_seconds"], (int, float))
            assert isinstance(data["records_processed"], int)
            assert isinstance(data["job_name"], str)
            assert data["job_name"] == "cloudwatch_test_job"
            assert data["duration_in_seconds"] == 2.567
            assert data["records_processed"] == 500
            
        finally:
            # Restore original handlers
            logger.logger.handlers.clear()
            for handler in original_handlers:
                logger.logger.addHandler(handler)