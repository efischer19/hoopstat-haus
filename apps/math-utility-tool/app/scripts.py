"""Development scripts for the math utility tool."""

import subprocess
import sys


def test() -> None:
    """Run the test suite."""
    print("Running tests...")
    result = subprocess.run([sys.executable, "-m", "pytest", "-v"], check=False)
    sys.exit(result.returncode)


def lint() -> None:
    """Run linting checks."""
    print("Running linting checks...")
    ruff_result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."], check=False
    )

    if ruff_result.returncode != 0:
        print("❌ Linting failed")
        sys.exit(1)
    else:
        print("✅ Linting passed")


def format_code() -> None:
    """Format code using ruff and black."""
    print("Formatting code...")

    # Format with ruff
    ruff_result = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "."], check=False
    )

    # Format with black
    black_result = subprocess.run([sys.executable, "-m", "black", "."], check=False)

    if ruff_result.returncode != 0 or black_result.returncode != 0:
        print("❌ Formatting failed")
        sys.exit(1)
    else:
        print("✅ Code formatted successfully")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test()
        elif sys.argv[1] == "lint":
            lint()
        elif sys.argv[1] == "format":
            format_code()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            sys.exit(1)
    else:
        print("Available commands: test, lint, format")
