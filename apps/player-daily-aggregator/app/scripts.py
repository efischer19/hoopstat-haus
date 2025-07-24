"""Development scripts for the player daily aggregator app."""

import subprocess
import sys


def test() -> None:
    """Run pytest with coverage."""
    subprocess.run([sys.executable, "-m", "pytest", "--cov=app", "tests/"], check=True)


def lint() -> None:
    """Run ruff linting."""
    subprocess.run([sys.executable, "-m", "ruff", "check", "."], check=True)


def format_code() -> None:
    """Format code with ruff."""
    subprocess.run([sys.executable, "-m", "ruff", "format", "."], check=True)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "test":
            test()
        elif command == "lint":
            lint()
        elif command == "format":
            format_code()
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    else:
        print("Available commands: test, lint, format")
