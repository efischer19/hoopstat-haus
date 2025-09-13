"""Tests for the handlers module."""

from unittest.mock import MagicMock

from app.handlers import lambda_handler


class TestLambdaHandler:
    """Test cases for the Lambda handler."""

    def test_lambda_handler_basic(self):
        """Test basic lambda handler invocation."""
        event = {"Records": []}
        context = MagicMock()

        response = lambda_handler(event, context)

        assert response["statusCode"] == 200
        assert "message" in response["body"]
        assert response["body"]["records_processed"] == 0

    def test_lambda_handler_with_records(self):
        """Test lambda handler with S3 event records."""
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "test-key"},
                    }
                },
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "test-key-2"},
                    }
                },
            ]
        }
        context = MagicMock()

        response = lambda_handler(event, context)

        assert response["statusCode"] == 200
        assert response["body"]["records_processed"] == 2

    def test_lambda_handler_no_records(self):
        """Test lambda handler with event that has no Records."""
        event = {"test": "data"}
        context = MagicMock()

        response = lambda_handler(event, context)

        assert response["statusCode"] == 200
        assert response["body"]["records_processed"] == 0
