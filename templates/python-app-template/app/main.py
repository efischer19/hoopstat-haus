"""
Hello World Python Application Template for Hoopstat Haus.

This is a simple template application that demonstrates the standard
project structure and tooling setup for Python applications in the
Hoopstat Haus project.
"""


def greet(name: str = "World") -> str:
    """
    Generate a greeting message.

    Args:
        name: The name to greet. Defaults to "World".

    Returns:
        A greeting message string.
    """
    return f"Hello, {name}! Welcome to Hoopstat Haus!"


def main() -> None:
    """Main entry point for the application."""
    message = greet()
    print(message)
    print("This is a template Python application.")
    print("It demonstrates the standard project structure and tooling.")


if __name__ == "__main__":
    main()
