"""
Utility Tool for Hoopstat Haus.

This utility tool demonstrates using shared libraries but is NOT intended
for deployment (no Dockerfile).
"""

from test_utils import add_numbers, greet as lib_greet


def greet(name: str = "World") -> str:
    """
    Generate a greeting message using the shared library.

    Args:
        name: The name to greet. Defaults to "World".

    Returns:
        A greeting message string.
    """
    base_greeting = lib_greet(name)
    return f"{base_greeting} This is a utility tool!"


def process_numbers(*numbers: int) -> dict:
    """Process a list of numbers using shared utilities.
    
    Args:
        numbers: Variable number of integers
        
    Returns:
        Dictionary with processing results
    """
    if len(numbers) < 2:
        return {"error": "Need at least 2 numbers"}
    
    total = numbers[0]
    for num in numbers[1:]:
        total = add_numbers(total, num)
    
    return {
        "total": total,
        "count": len(numbers),
        "average": total / len(numbers),
        "inputs": list(numbers)
    }


def main() -> None:
    """Main entry point for the utility."""
    message = greet("Developer")
    print(message)
    print("This is a utility tool (not for deployment).")
    
    # Use shared library functionality
    result = process_numbers(1, 2, 3, 4, 5)
    print(f"Processing numbers: {result}")


if __name__ == "__main__":
    main()
