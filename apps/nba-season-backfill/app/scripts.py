"""
Development scripts for NBA season backfill application.

Provides consistent test, lint, and format commands following
project conventions.
"""

import subprocess
import sys


def test():
    """Run test suite with coverage."""
    result = subprocess.run(
        [
            "python",
            "-m",
            "pytest",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "-v",
        ]
    )
    sys.exit(result.returncode)


def lint():
    """Run linting checks."""
    print("Running Ruff...")
    ruff_result = subprocess.run(["python", "-m", "ruff", "check", "app", "tests"])

    print("Running type checking...")
    # Note: mypy not included in dependencies yet, so we skip it for now
    # mypy_result = subprocess.run(["python", "-m", "mypy", "app"])

    if ruff_result.returncode != 0:
        sys.exit(1)


def format_code():
    """Format code with Black and Ruff."""
    print("Running Ruff auto-fix...")
    subprocess.run(["python", "-m", "ruff", "check", "--fix", "app", "tests"])

    print("Running Black...")
    result = subprocess.run(["python", "-m", "black", "app", "tests"])
    sys.exit(result.returncode)
