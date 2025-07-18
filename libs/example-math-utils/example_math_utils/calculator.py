"""
calculator module for example-math-utils.

This module demonstrates standard patterns for shared library modules.
"""


def add(a: float, b: float) -> float:
    """
    Add two numbers together.

    This function demonstrates proper documentation and type hints
    for shared library functions.

    Args:
        a: The first number to add
        b: The second number to add

    Returns:
        The sum of a and b

    Example:
        >>> add(2, 3)
        5.0
    """
    return a + b


def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers together.

    Args:
        a: The first number to multiply
        b: The second number to multiply

    Returns:
        The product of a and b

    Example:
        >>> multiply(4, 5)
        20.0
    """
    return a * b


def divide(a: float, b: float) -> float:
    """
    Divide the first number by the second number.

    Args:
        a: The dividend
        b: The divisor

    Returns:
        The quotient of a divided by b

    Raises:
        ValueError: If divisor is zero

    Example:
        >>> divide(10, 2)
        5.0
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def subtract(a: float, b: float) -> float:
    """
    Subtract the second number from the first number.

    This function was added to demonstrate hot reloading!

    Args:
        a: The minuend (number to subtract from)
        b: The subtrahend (number to subtract)

    Returns:
        The difference of a minus b

    Example:
        >>> subtract(10, 3)
        7.0
    """
    return a - b
