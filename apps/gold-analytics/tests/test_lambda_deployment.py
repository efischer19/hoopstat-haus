"""Tests for Lambda deployment module structure."""

from app import lambda_handler as lambda_module


class TestLambdaDeployment:
    """Test cases for Lambda deployment compatibility."""

    def test_lambda_handler_module_exists(self):
        """Test that lambda_handler module exists."""
        assert hasattr(lambda_module, "lambda_handler")

    def test_lambda_handler_function_callable(self):
        """Test that lambda_handler function is callable."""
        assert callable(lambda_module.lambda_handler)

    def test_lambda_handler_all_exports(self):
        """Test that lambda_handler is in __all__."""
        assert "lambda_handler" in lambda_module.__all__
