"""
Development scripts for the MCP server.
"""

import subprocess


def test():
    """Run tests."""
    subprocess.run(["python", "-m", "pytest"], check=True)


def lint():
    """Run linting."""
    subprocess.run(["ruff", "check", "."], check=True)


def format_code():
    """Format code."""
    subprocess.run(["ruff", "format", "."], check=True)


def dev():
    """Run development server with MCP debugging."""
    print("Starting MCP server in development mode...")
    print("Use MCP Inspector or connect via stdio for debugging")
    from .main import main

    main()
