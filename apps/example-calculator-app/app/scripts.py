"""
Development scripts for the Python application template.

This module provides entry points for common development tasks
that can be called via Poetry scripts.
"""

import subprocess
import sys
from pathlib import Path


def test() -> None:
    """Run tests using pytest."""
    result = subprocess.run([sys.executable, "-m", "pytest"], cwd=Path.cwd())
    sys.exit(result.returncode)


def lint() -> None:
    """Run linting using ruff."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."], cwd=Path.cwd()
    )
    sys.exit(result.returncode)


def format_code() -> None:
    """Format code using black."""
    result = subprocess.run([sys.executable, "-m", "black", "."], cwd=Path.cwd())
    sys.exit(result.returncode)
