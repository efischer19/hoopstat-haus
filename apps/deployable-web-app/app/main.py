"""
Deployable Web Application for Hoopstat Haus.

This application demonstrates using shared libraries and is intended
for deployment (has a Dockerfile).
"""

from test_utils import add_numbers
from test_utils import greet as lib_greet


def greet(name: str = "World") -> str:
    """
    Generate a greeting message using the shared library.

    Args:
        name: The name to greet. Defaults to "World".

    Returns:
        A greeting message string.
    """
    base_greeting = lib_greet(name)
    return f"{base_greeting} Welcome to Hoopstat Haus!"


def calculate_stats(a: int, b: int) -> dict:
    """Calculate some simple stats using shared utilities.

    Args:
        a: First number
        b: Second number

    Returns:
        Dictionary with calculated stats
    """
    sum_val = add_numbers(a, b)
    return {"sum": sum_val, "average": sum_val / 2, "inputs": [a, b]}


def main() -> None:
    """Main entry point for the application."""
    message = greet()
    print(message)
    print("This is a deployable web application.")

    # Use shared library functionality
    stats = calculate_stats(10, 5)
    print(f"Sample calculation: {stats}")


if __name__ == "__main__":
    main()
