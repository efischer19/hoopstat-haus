"""Test utilities library for CI validation."""

__version__ = "0.1.0"


def add_numbers(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b


def greet(name: str) -> str:
    """Generate a greeting message.

    Args:
        name: Name to greet

    Returns:
        Greeting message
    """
    return f"Hello, {name}!"


__all__ = ["add_numbers", "greet"]
