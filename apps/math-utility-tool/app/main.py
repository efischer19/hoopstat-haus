"""
Math Utility Tool for Hoopstat Haus.

A simple command-line utility demonstrating the non-deployable application pattern.
This tool uses the example-math-utils shared library to perform calculations.
"""

import sys

from example_math_utils import add, divide, multiply, subtract


def calculate_from_args(args: list[str]) -> None:
    """Perform calculation based on command-line arguments."""
    if len(args) < 3:
        print("Usage: poetry run calculate <operation> <num1> <num2>")
        print("Operations: add, subtract, multiply, divide")
        sys.exit(1)

    operation = args[0].lower()
    try:
        num1 = float(args[1])
        num2 = float(args[2])
    except ValueError:
        print("Error: Please provide valid numbers")
        sys.exit(1)

    result = None
    if operation == "add":
        result = add(num1, num2)
    elif operation == "subtract":
        result = subtract(num1, num2)
    elif operation == "multiply":
        result = multiply(num1, num2)
    elif operation == "divide":
        try:
            result = divide(num1, num2)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print(f"Error: Unknown operation '{operation}'")
        print("Available operations: add, subtract, multiply, divide")
        sys.exit(1)

    print(f"{num1} {operation} {num2} = {result}")


def run_batch_calculations() -> None:
    """Run a set of example calculations."""
    print("Math Utility Tool - Batch Calculations")
    print("=" * 40)

    calculations = [
        ("add", 10, 5),
        ("subtract", 20, 8),
        ("multiply", 6, 7),
        ("divide", 100, 4),
    ]

    for operation, a, b in calculations:
        if operation == "add":
            result = add(a, b)
        elif operation == "subtract":
            result = subtract(a, b)
        elif operation == "multiply":
            result = multiply(a, b)
        elif operation == "divide":
            result = divide(a, b)

        print(f"{a} {operation} {b} = {result}")


def main() -> None:
    """Main entry point for the utility tool."""
    args = sys.argv[1:]

    if not args:
        print("Math Utility Tool")
        print("================")
        print("No arguments provided. Running batch calculations...")
        print()
        run_batch_calculations()
        print()
        print("For manual calculations, use:")
        print("poetry run calculate <operation> <num1> <num2>")
    else:
        calculate_from_args(args)


if __name__ == "__main__":
    main()
