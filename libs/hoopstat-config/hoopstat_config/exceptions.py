"""
Configuration-related exceptions for clear error handling.
"""

from typing import Any


class ConfigValidationError(Exception):
    """
    Raised when configuration validation fails.

    This exception provides detailed information about validation failures
    to help developers quickly identify and fix configuration issues.
    """

    def __init__(self, message: str, errors: list[dict[str, Any]] = None):
        """
        Initialize validation error.

        Args:
            message: Human-readable error summary
            errors: List of detailed error information with field names and messages
        """
        super().__init__(message)
        self.errors = errors or []

    def __str__(self) -> str:
        """Return formatted error message with details."""
        if not self.errors:
            return super().__str__()

        error_details = []
        for error in self.errors:
            field = error.get("field", "unknown")
            msg = error.get("message", "unknown error")
            error_details.append(f"  - {field}: {msg}")

        return f"{super().__str__()}\nValidation errors:\n" + "\n".join(error_details)


class ConfigFileError(Exception):
    """
    Raised when configuration file loading or parsing fails.

    This exception is used for file system errors, parsing errors,
    and other file-related issues during configuration loading.
    """

    def __init__(
        self, message: str, file_path: str = None, original_error: Exception = None
    ):
        """
        Initialize file error.

        Args:
            message: Human-readable error message
            file_path: Path to the configuration file that caused the error
            original_error: The original exception that caused this error
        """
        super().__init__(message)
        self.file_path = file_path
        self.original_error = original_error

    def __str__(self) -> str:
        """Return formatted error message with file path and original error."""
        msg = super().__str__()

        if self.file_path:
            msg = f"{msg} (file: {self.file_path})"

        if self.original_error:
            msg = f"{msg}\nCaused by: {self.original_error}"

        return msg


class ConfigEnvironmentError(Exception):
    """
    Raised when environment variable processing fails.

    This exception is used when environment variables cannot be parsed
    or converted to the expected types.
    """

    def __init__(self, message: str, env_var: str = None, env_value: str = None):
        """
        Initialize environment error.

        Args:
            message: Human-readable error message
            env_var: Name of the environment variable that caused the error
            env_value: Value of the environment variable that caused the error
        """
        super().__init__(message)
        self.env_var = env_var
        self.env_value = env_value

    def __str__(self) -> str:
        """Return formatted error message with environment variable details."""
        msg = super().__str__()

        if self.env_var:
            msg = f"{msg} (environment variable: {self.env_var}"
            if self.env_value is not None:
                msg = f"{msg}={self.env_value}"
            msg = f"{msg})"

        return msg
