"""
End-to-end testing utilities for basketball data pipeline.

This package provides utilities for testing the complete data pipeline
using Localstack S3 simulation and Docker Compose orchestration.
"""

__version__ = "0.1.0"

from .localstack_manager import LocalstackManager
from .pipeline_runner import PipelineTestRunner
from .s3_utils import S3TestUtils

__all__ = ["S3TestUtils", "PipelineTestRunner", "LocalstackManager"]
