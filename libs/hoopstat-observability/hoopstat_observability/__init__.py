"""
Hoopstat Observability Library

Standardized logging and observability utilities for Hoopstat Haus applications.
Implements structured JSON logging per ADR-015, CloudWatch integration per ADR-018,
and semantic versioning per ADR-016.

This library consolidates logging functionality to ensure consistent observability
across all applications while eliminating code duplication.
"""

from .json_logger import JSONLogger, get_logger
from .performance import performance_monitor, performance_context
from .correlation import CorrelationContext, correlation_context
from .diagnostics import DiagnosticLogger

__version__ = "0.1.0"

__all__ = [
    "JSONLogger",
    "get_logger", 
    "performance_monitor",
    "performance_context",
    "CorrelationContext",
    "correlation_context",
    "DiagnosticLogger",
]
