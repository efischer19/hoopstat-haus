"""
Lambda handler entry point for gold-analytics.

This module provides the lambda_handler function that matches the expected
module structure for Lambda deployment health checks.
"""

from .handlers import lambda_handler

# Re-export the lambda_handler function for Lambda runtime
__all__ = ["lambda_handler"]
