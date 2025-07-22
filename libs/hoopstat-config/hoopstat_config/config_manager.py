"""
Main configuration manager class providing type-safe configuration handling.
"""

import logging
from typing import Any, TypeVar, get_type_hints

from pydantic import BaseModel, Field, ValidationError

from .config_field import ConfigField
from .exceptions import ConfigFileError, ConfigValidationError
from .loaders import load_config_file

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="ConfigManager")


def config_field(
    default: Any = ...,
    env_var: str | None = None,
    description: str | None = None,
    **kwargs,
) -> Any:
    """
    Create a configuration field with environment variable support.

    This function creates a Pydantic field with additional metadata
    for environment variable handling.

    Args:
        default: Default value for the field.
        env_var: Environment variable name to read the value from.
        description: Human-readable description of the field.
        **kwargs: Additional arguments passed to pydantic.Field()

    Returns:
        Pydantic Field for use in model definitions.
    """
    # Create the field metadata
    field_args = {}
    if default is not ...:
        field_args["default"] = default
    if description:
        field_args["description"] = description
    field_args.update(kwargs)

    # Store environment variable in json_schema_extra
    if env_var:
        field_args["json_schema_extra"] = field_args.get("json_schema_extra", {})
        field_args["json_schema_extra"]["env_var"] = env_var

    return Field(**field_args)


class ConfigManager(BaseModel):
    """
    Base class for type-safe configuration management.

    This class provides a foundation for creating configuration classes that:
    - Load from multiple sources (defaults, files, environment variables)
    - Provide type safety and validation
    - Support multiple file formats
    - Give clear error messages
    - Track configuration sources for debugging
    """

    model_config = {
        # Don't allow extra fields
        "extra": "forbid",
        # Validate on assignment
        "validate_assignment": True,
        # Use enum values
        "use_enum_values": True,
    }

    def __init__(self, **data):
        """Initialize configuration with provided data."""
        super().__init__(**data)
        # Track where each field value came from
        self._field_sources: dict[str, str] = {}

    @classmethod
    def load(
        cls: type[T],
        config_file: str | None = None,
        override_values: dict[str, Any] | None = None,
    ) -> T:
        """
        Load configuration from multiple sources with precedence rules.

        Configuration sources (in order of precedence, later overrides earlier):
        1. Class defaults
        2. Configuration file (if provided)
        3. Environment variables
        4. Override values (if provided)

        Args:
            config_file: Optional path to configuration file
            override_values: Optional dictionary of values to override

        Returns:
            Configured instance of the class

        Raises:
            ConfigValidationError: If configuration validation fails
            ConfigFileError: If configuration file cannot be loaded
        """
        logger.debug(f"Loading configuration for {cls.__name__}")

        # Start with an empty configuration
        config_data = {}
        field_sources = {}

        # Get field information from the class
        type_hints = get_type_hints(cls)

        # Step 1: Apply defaults from field definitions
        for field_name, field_info in cls.model_fields.items():
            if field_info.default is not ...:
                config_data[field_name] = field_info.default
                field_sources[field_name] = "default"
                logger.debug(f"Using default value for {field_name}")

        # Step 2: Load from configuration file (if provided)
        if config_file:
            try:
                file_data = load_config_file(config_file)
                for key, value in file_data.items():
                    if key in type_hints:
                        config_data[key] = value
                        field_sources[key] = "file"
                        logger.debug(f"Loaded {key} from config file")
                    else:
                        logger.warning(
                            f"Unknown configuration key '{key}' in file {config_file}"
                        )
            except Exception as e:
                if isinstance(e, ConfigFileError):
                    raise
                raise ConfigFileError(
                    f"Failed to load config file: {e}", config_file
                ) from e

        # Step 3: Apply environment variables
        for field_name, field_info in cls.model_fields.items():
            # Check for environment variable configuration
            env_var = None
            if (
                hasattr(field_info, "json_schema_extra")
                and field_info.json_schema_extra
            ):
                env_var = field_info.json_schema_extra.get("env_var")

            if env_var:
                field_type = type_hints.get(field_name, str)
                try:
                    config_field_obj = ConfigField(env_var=env_var)
                    env_value = config_field_obj.get_env_value(field_type)
                    if env_value is not None:
                        config_data[field_name] = env_value
                        field_sources[field_name] = "environment"
                        logger.debug(
                            f"Loaded {field_name} from environment variable {env_var}"
                        )
                except Exception as e:
                    raise ConfigValidationError(
                        f"Failed to process environment variable for {field_name}",
                        [{"field": field_name, "message": str(e)}],
                    ) from e

        # Step 4: Apply override values
        if override_values:
            for key, value in override_values.items():
                if key in type_hints:
                    config_data[key] = value
                    field_sources[key] = "override"
                    logger.debug(f"Applied override value for {key}")
                else:
                    logger.warning(
                        f"Unknown configuration key '{key}' in override values"
                    )

        # Create and validate the configuration instance
        try:
            instance = cls(**config_data)
            instance._field_sources = field_sources

            logger.info(f"Successfully loaded configuration for {cls.__name__}")
            return instance

        except ValidationError as e:
            # Convert Pydantic validation errors to our custom exception
            error_details = []
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                error_details.append(
                    {
                        "field": field_path,
                        "message": error["msg"],
                        "type": error["type"],
                    }
                )

            raise ConfigValidationError(
                f"Configuration validation failed for {cls.__name__}", error_details
            ) from e

    @classmethod
    def load_from_file(cls: type[T], config_file: str) -> T:
        """
        Load configuration from a file only (no environment variables).

        Args:
            config_file: Path to configuration file

        Returns:
            Configured instance of the class

        Raises:
            ConfigValidationError: If configuration validation fails
            ConfigFileError: If configuration file cannot be loaded
        """
        logger.debug(f"Loading configuration for {cls.__name__} from file only")

        try:
            file_data = load_config_file(config_file)
            instance = cls(**file_data)

            # Track that all values came from file
            instance._field_sources = {
                field_name: "file"
                for field_name in file_data.keys()
                if field_name in cls.model_fields
            }

            logger.info(
                f"Successfully loaded configuration for {cls.__name__} "
                f"from {config_file}"
            )
            return instance

        except ValidationError as e:
            # Convert Pydantic validation errors to our custom exception
            error_details = []
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                error_details.append(
                    {
                        "field": field_path,
                        "message": error["msg"],
                        "type": error["type"],
                    }
                )

            raise ConfigValidationError(
                f"Configuration validation failed for {cls.__name__}", error_details
            ) from e

    def get_field_sources(self) -> dict[str, str]:
        """
        Get information about where each field value came from.

        Returns:
            Dictionary mapping field names to source types:
            - 'default': From class default value
            - 'file': From configuration file
            - 'environment': From environment variable
            - 'override': From override values
        """
        return getattr(self, "_field_sources", {}).copy()

    def get_config_summary(self) -> str:
        """
        Get a human-readable summary of the configuration.

        Returns:
            Formatted string showing all configuration values and their sources
        """
        lines = [f"Configuration Summary for {self.__class__.__name__}:"]
        sources = self.get_field_sources()

        for field_name in self.model_fields.keys():
            value = getattr(self, field_name)
            source = sources.get(field_name, "unknown")

            # Don't show sensitive values in summaries
            if "password" in field_name.lower() or "secret" in field_name.lower():
                value_str = "***"
            else:
                value_str = repr(value)

            lines.append(f"  {field_name}: {value_str} (source: {source})")

        return "\n".join(lines)

    def get_env_vars(self) -> dict[str, str]:
        """
        Get environment variable names for all fields that support them.

        Returns:
            Dictionary mapping field names to environment variable names
        """
        env_vars = {}

        for field_name, field_info in self.model_fields.items():
            if (
                hasattr(field_info, "json_schema_extra")
                and field_info.json_schema_extra
            ):
                env_var = field_info.json_schema_extra.get("env_var")
                if env_var:
                    env_vars[field_name] = env_var

        return env_vars
