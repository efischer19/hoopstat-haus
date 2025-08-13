"""
Tests for Lambda handler functionality.

These tests verify that the Lambda handler properly parses event payloads
and invokes the correct CLI commands with appropriate parameters.
"""

import json
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from app.lambda_handler import lambda_handler, status_handler


class TestLambdaHandler:
    """Test cases for the main Lambda handler."""

    def test_lambda_handler_with_valid_event(self):
        """Test Lambda handler with a valid event payload."""
        # Arrange
        event = {
            "source": "github-actions-daily",
            "trigger_type": "workflow_dispatch",
            "parameters": {"date": "2024-12-25", "dry_run": True, "force_run": False},
            "metadata": {
                "workflow_run_id": "16935785442",
                "workflow_run_number": "2",
                "repository": "efischer19/hoopstat-haus",
                "triggered_at": "2025-08-13T11:25:09Z",
            },
        }

        context = MagicMock()
        context.aws_request_id = "test-request-id"
        context.function_name = "test-function"

        # Mock the ingestion class and its run method
        with patch("app.lambda_handler.DateScopedIngestion") as mock_ingestion_class:
            mock_ingestion = MagicMock()
            mock_ingestion.run.return_value = True
            mock_ingestion_class.return_value = mock_ingestion

            # Act
            result = lambda_handler(event, context)

            # Assert
            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["status"] == "success"
            assert body["target_date"] == "2024-12-25"
            assert body["dry_run"] is True
            assert body["correlation_id"] == "test-request-id"

            # Verify ingestion was called with correct parameters
            mock_ingestion.run.assert_called_once_with(
                target_date=date(2024, 12, 25), dry_run=True
            )

    def test_lambda_handler_with_missing_date(self):
        """Test Lambda handler when no date is provided (should use today)."""
        # Arrange
        event = {
            "source": "github-actions-daily",
            "trigger_type": "schedule",
            "parameters": {"dry_run": False, "force_run": False},
        }

        context = MagicMock()
        context.aws_request_id = "test-request-id"
        context.function_name = "test-function"

        today = date(2024, 12, 25)  # Use a fixed date for predictable testing

        with patch("app.lambda_handler.DateScopedIngestion") as mock_ingestion_class:
            mock_ingestion = MagicMock()
            mock_ingestion.run.return_value = True
            mock_ingestion_class.return_value = mock_ingestion

            with patch("app.lambda_handler.datetime") as mock_datetime:
                # Create a mock datetime that behaves correctly
                real_datetime = datetime(2024, 12, 25, 10, 30, 0)
                mock_datetime.utcnow.return_value = real_datetime
                mock_datetime.strptime = datetime.strptime

                # Act
                result = lambda_handler(event, context)

                # Assert
                assert result["statusCode"] == 200
                body = json.loads(result["body"])
                assert body["status"] == "success"
                assert body["target_date"] == today.isoformat()
                assert body["dry_run"] is False

    def test_lambda_handler_with_invalid_date(self):
        """Test Lambda handler with invalid date format."""
        # Arrange
        event = {
            "source": "github-actions-daily",
            "trigger_type": "workflow_dispatch",
            "parameters": {
                "date": "invalid-date",
                "dry_run": False,
                "force_run": False,
            },
        }

        context = MagicMock()
        context.aws_request_id = "test-request-id"
        context.function_name = "test-function"

        # Act
        result = lambda_handler(event, context)

        # Assert
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert body["status"] == "error"
        assert "Invalid date format" in body["message"]
        assert body["error_type"] == "ValueError"

    def test_lambda_handler_with_ingestion_failure(self):
        """Test Lambda handler when ingestion fails."""
        # Arrange
        event = {
            "source": "github-actions-daily",
            "trigger_type": "workflow_dispatch",
            "parameters": {"date": "2024-12-25", "dry_run": False, "force_run": False},
        }

        context = MagicMock()
        context.aws_request_id = "test-request-id"
        context.function_name = "test-function"

        with patch("app.lambda_handler.DateScopedIngestion") as mock_ingestion_class:
            mock_ingestion = MagicMock()
            mock_ingestion.run.return_value = False  # Simulate failure
            mock_ingestion_class.return_value = mock_ingestion

            # Act
            result = lambda_handler(event, context)

            # Assert
            assert result["statusCode"] == 500
            body = json.loads(result["body"])
            assert body["status"] == "error"
            assert "Bronze layer ingestion failed" in body["message"]

    def test_lambda_handler_with_exception(self):
        """Test Lambda handler when ingestion raises an exception."""
        # Arrange
        event = {
            "source": "github-actions-daily",
            "trigger_type": "workflow_dispatch",
            "parameters": {"date": "2024-12-25", "dry_run": False, "force_run": False},
        }

        context = MagicMock()
        context.aws_request_id = "test-request-id"
        context.function_name = "test-function"

        with patch("app.lambda_handler.DateScopedIngestion") as mock_ingestion_class:
            mock_ingestion_class.side_effect = RuntimeError("Test error")

            # Act
            result = lambda_handler(event, context)

            # Assert
            assert result["statusCode"] == 500
            body = json.loads(result["body"])
            assert body["status"] == "error"
            assert "Test error" in body["message"]
            assert body["error_type"] == "RuntimeError"


class TestStatusHandler:
    """Test cases for the status handler."""

    def test_status_handler_healthy(self):
        """Test status handler when service is healthy."""
        # Arrange
        context = MagicMock()
        context.aws_request_id = "test-request-id"
        context.function_name = "test-function"

        with patch("app.lambda_handler.DateScopedIngestion") as mock_ingestion_class:
            # Mock successful instantiation
            mock_ingestion_class.return_value = MagicMock()

            # Act
            result = status_handler({}, context)

            # Assert
            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["status"] == "healthy"
            assert "pipeline is ready" in body["message"]
            assert body["correlation_id"] == "test-request-id"

    def test_status_handler_unhealthy(self):
        """Test status handler when service is unhealthy."""
        # Arrange
        context = MagicMock()
        context.aws_request_id = "test-request-id"
        context.function_name = "test-function"

        with patch("app.lambda_handler.DateScopedIngestion") as mock_ingestion_class:
            # Mock instantiation failure
            mock_ingestion_class.side_effect = RuntimeError("Configuration error")

            # Act
            result = status_handler({}, context)

            # Assert
            assert result["statusCode"] == 500
            body = json.loads(result["body"])
            assert body["status"] == "unhealthy"
            assert "Configuration error" in body["message"]
            assert body["error_type"] == "RuntimeError"
            assert body["correlation_id"] == "test-request-id"
