"""
Calculator Application for Hoopstat Haus.

This application demonstrates local development dependency management
by using the example-math-utils shared library with hot reloading support.
"""

import sys

from example_math_utils import add, divide, multiply, subtract


def calculate_expression() -> None:
    """Demonstrate calculator functionality using the shared library."""
    print("Calculator Application - Local Development Demo")
    print("=" * 50)

    # Basic arithmetic examples
    print("\nBasic Arithmetic Examples:")
    print(f"2 + 3 = {add(2, 3)}")
    print(f"4 * 5 = {multiply(4, 5)}")
    print(f"20 / 4 = {divide(20, 4)}")
    print(f"10 - 3 = {subtract(10, 3)}  <- NEW FUNCTION!")

    # More complex example
    print("\nComplex Calculation: (10 + 5) * 2 / 3")
    step1 = add(10, 5)  # 15
    step2 = multiply(step1, 2)  # 30
    result = divide(step2, 3)  # 10
    print(f"Result: {result}")

    # Interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        run_interactive_calculator()

    print("\nThis demonstrates hot reloading of shared libraries!")
    print("Try modifying libs/example-math-utils/example_math_utils/calculator.py")
    print("and run this app again to see changes immediately.")


def run_interactive_calculator() -> None:
    """Run an interactive calculator session."""
    print("\n" + "=" * 50)
    print("Interactive Calculator Mode")
    print("Enter 'quit' to exit")
    print("=" * 50)

    while True:
        try:
            print("\nAvailable operations: add, multiply, divide")
            operation = input("Enter operation: ").strip().lower()

            if operation == "quit":
                break

            if operation not in ["add", "multiply", "divide"]:
                print("Unknown operation. Try 'add', 'multiply', or 'divide'")
                continue

            a = float(input("Enter first number: "))
            b = float(input("Enter second number: "))

            if operation == "add":
                result = add(a, b)
            elif operation == "multiply":
                result = multiply(a, b)
            elif operation == "divide":
                result = divide(a, b)

            print(f"Result: {result}")

        except ValueError as e:
            if "Cannot divide by zero" in str(e):
                print("Error: Cannot divide by zero!")
            else:
                print("Error: Please enter valid numbers")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def main() -> None:
    """Main entry point for the application."""
    calculate_expression()


if __name__ == "__main__":
    main()
