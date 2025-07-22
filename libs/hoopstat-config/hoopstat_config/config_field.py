"""
Configuration field definition for type-safe configuration management.
"""

import os
from typing import Any, TypeVar

from pydantic import Field

from .exceptions import ConfigEnvironmentError

T = TypeVar("T")


class ConfigField:
    """
    Defines a configuration field with support for environment variables and validation.

    This class provides a declarative way to define configuration fields with:
    - Default values
    - Environment variable mapping
    - Type conversion
    - Documentation
    - Validation
    """

    def __init__(
        self,
        default: Any = ...,
        env_var: str | None = None,
        description: str | None = None,
        **field_kwargs,
    ):
        """
        Initialize a configuration field.

        Args:
            default: Default value for the field. Use ... for required fields.
            env_var: Environment variable name to read the value from.
            description: Human-readable description of the field.
            **field_kwargs: Additional arguments passed to pydantic.Field()
        """
        self.env_var = env_var
        self.description = description
        self.default = default
        self.field_kwargs = field_kwargs

        # Create the underlying Pydantic field
        field_args = {}
        if default is not ...:
            field_args["default"] = default

        if description:
            field_args["description"] = description

        field_args.update(field_kwargs)
        self.pydantic_field = Field(**field_args)

    def get_env_value(self, field_type: type[T]) -> T | None:
        """
        Get and convert value from environment variable.

        Args:
            field_type: The expected type for the field value.

        Returns:
            Converted value from environment variable, or None if not set.

        Raises:
            ConfigEnvironmentError: If environment variable exists but cannot be
                converted.
        """
        if not self.env_var:
            return None

        env_value = os.getenv(self.env_var)
        if env_value is None:
            return None

        try:
            return self._convert_env_value(env_value, field_type)
        except (ValueError, TypeError) as e:
            raise ConfigEnvironmentError(
                f"Failed to convert environment variable to {field_type.__name__}: {e}",
                env_var=self.env_var,
                env_value=env_value,
            ) from e

    def _convert_env_value(self, value: str, field_type: type[T]) -> T:
        """
        Convert string environment variable value to the target type.

        Args:
            value: String value from environment variable.
            field_type: Target type for conversion.

        Returns:
            Converted value.

        Raises:
            ValueError: If conversion fails.
        """
        import typing

        # Handle None and Optional types
        if hasattr(field_type, "__origin__"):
            origin = field_type.__origin__
            if origin is typing.Union:
                # Get the non-None type from Optional[T]
                args = getattr(field_type, "__args__", ())
                if len(args) == 2 and type(None) in args:
                    # This is Optional[T], get T
                    field_type = next(arg for arg in args if arg is not type(None))

            # Handle List types
            elif origin is list:
                list_type = getattr(field_type, "__args__", (str,))[0]
                items = [item.strip() for item in value.split(",") if item.strip()]
                return [self._convert_single_value(item, list_type) for item in items]

        # Handle modern union types (Python 3.10+)
        elif (
            hasattr(field_type, "__class__")
            and field_type.__class__.__name__ == "UnionType"
        ):
            # This is a modern union like str | None
            args = getattr(field_type, "__args__", ())
            if len(args) == 2 and type(None) in args:
                # This is Optional[T], get T
                field_type = next(arg for arg in args if arg is not type(None))

        return self._convert_single_value(value, field_type)

    def _convert_single_value(self, value: str, target_type: type[T]) -> T:
        """
        Convert a single string value to the target type.

        Args:
            value: String value to convert.
            target_type: Target type for conversion.

        Returns:
            Converted value.

        Raises:
            ValueError: If conversion fails.
        """
        # String type - return as-is
        if target_type is str:
            return value

        # Boolean type - handle common boolean representations
        if target_type is bool:
            lower_value = value.lower()
            if lower_value in ("true", "1", "yes", "on", "enabled"):
                return True
            elif lower_value in ("false", "0", "no", "off", "disabled"):
                return False
            else:
                raise ValueError(f"Cannot convert '{value}' to boolean")

        # Numeric types
        if target_type is int:
            return int(value)

        if target_type is float:
            return float(value)

        # For other types, try direct conversion
        try:
            return target_type(value)
        except (ValueError, TypeError) as e:
            # Handle modern union types which don't have __name__
            type_name = getattr(target_type, "__name__", str(target_type))
            raise ValueError(f"Cannot convert '{value}' to {type_name}") from e


def config_field(
    default: Any = ...,
    env_var: str | None = None,
    description: str | None = None,
    **kwargs,
) -> Any:
    """
    Create a configuration field with environment variable support.

    This is a convenience function that creates a ConfigField and returns
    its Pydantic field for use in class definitions.

    Args:
        default: Default value for the field.
        env_var: Environment variable name to read the value from.
        description: Human-readable description of the field.
        **kwargs: Additional arguments passed to pydantic.Field()

    Returns:
        Pydantic Field object for use in model definitions.
    """
    config_field_obj = ConfigField(
        default=default, env_var=env_var, description=description, **kwargs
    )

    # Store the ConfigField on the Pydantic field for later retrieval
    pydantic_field = config_field_obj.pydantic_field

    # Use a more compatible way to attach the config field
    if not hasattr(pydantic_field, "__dict__"):
        # If it doesn't have a __dict__, we'll use a different approach
        # This will be handled in the ConfigManager
        pass
    else:
        pydantic_field.__dict__["config_field"] = config_field_obj

    return pydantic_field
