"""
Data cleaning and standardization rules engine.

Provides a configurable rules engine for applying data cleaning, standardization,
and conforming transformations to NBA data.
"""

import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from dateutil import parser as date_parser
from fuzzywuzzy import process

logger = logging.getLogger(__name__)


class TransformationResult:
    """Result of a data transformation operation."""

    def __init__(
        self,
        original_value: Any,
        transformed_value: Any,
        transformation_type: str,
        success: bool = True,
        error_message: str | None = None,
        applied_rules: list[str] | None = None,
    ):
        self.original_value = original_value
        self.transformed_value = transformed_value
        self.transformation_type = transformation_type
        self.success = success
        self.error_message = error_message
        self.applied_rules = applied_rules or []
        self.timestamp = datetime.utcnow().isoformat()


class DataCleaningRulesEngine:
    """
    Configurable rules engine for data cleaning and standardization.

    Applies data cleaning, standardization, and conforming transformations
    to NBA data based on configurable YAML rules.
    """

    def __init__(self, config_path: str | None = None):
        """
        Initialize the rules engine.

        Args:
            config_path: Path to YAML configuration file. If None, uses default.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_configuration()
        self._setup_logging()
        self.transformation_log: list[TransformationResult] = []

    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "config" / "cleaning_rules.yaml")

    def _load_configuration(self) -> dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path) as file:
                config = yaml.safe_load(file)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration from {self.config_path}: {e}")
            raise

    def _setup_logging(self) -> None:
        """Setup logging based on configuration."""
        log_config = self.config.get("logging", {})
        level = getattr(logging, log_config.get("level", "INFO"))
        logger.setLevel(level)

    def standardize_team_name(
        self, team_name: str, use_fuzzy_matching: bool = True
    ) -> TransformationResult:
        """
        Standardize team name using mapping table and fuzzy matching.

        Args:
            team_name: Raw team name
            use_fuzzy_matching: Whether to use fuzzy matching as fallback

        Returns:
            TransformationResult with standardized team name
        """
        if not team_name or not isinstance(team_name, str):
            return TransformationResult(
                team_name, "", "team_name_standardization", False, "Invalid input"
            )

        original_name = team_name
        applied_rules = []

        # Clean and normalize input
        cleaned_name = re.sub(r"\s+", " ", team_name.strip().lower())
        applied_rules.append("whitespace_normalization")

        # Check direct mappings
        team_mappings = self.config.get("team_name_mappings", {})
        if cleaned_name in team_mappings:
            standardized_name = team_mappings[cleaned_name]
            applied_rules.append("direct_mapping")

            if self.config.get("logging", {}).get("log_transformations", False):
                logger.info(
                    f"Team name standardized: '{original_name}' -> "
                    f"'{standardized_name}'"
                )

            return TransformationResult(
                original_name,
                standardized_name,
                "team_name_standardization",
                True,
                applied_rules=applied_rules,
            )

        # Try fuzzy matching if enabled
        if use_fuzzy_matching and self.config.get("fuzzy_matching", {}).get(
            "enabled_fields", []
        ):
            if "team_name" in self.config["fuzzy_matching"]["enabled_fields"]:
                threshold = self.config["fuzzy_matching"]["team_name_threshold"]
                official_names = self.config.get("official_team_names", [])

                if official_names:
                    best_match = process.extractOne(cleaned_name, official_names)
                    if best_match and best_match[1] >= threshold:
                        standardized_name = best_match[0]
                        applied_rules.append(f"fuzzy_matching_{best_match[1]}")

                        if self.config.get("logging", {}).get(
                            "log_transformations", False
                        ):
                            logger.info(
                                f"Team name fuzzy matched: '{original_name}' -> "
                                f"'{standardized_name}' (score: {best_match[1]})"
                            )

                        return TransformationResult(
                            original_name,
                            standardized_name,
                            "team_name_standardization",
                            True,
                            applied_rules=applied_rules,
                        )

        # Return cleaned version if no mapping found
        cleaned_title_case = " ".join(
            word.capitalize() for word in cleaned_name.split()
        )
        applied_rules.append("title_case_fallback")

        return TransformationResult(
            original_name,
            cleaned_title_case,
            "team_name_standardization",
            True,
            applied_rules=applied_rules,
        )

    def standardize_position(self, position: str) -> TransformationResult:
        """
        Standardize player position using mapping table.

        Args:
            position: Raw position string

        Returns:
            TransformationResult with standardized position
        """
        if not position or not isinstance(position, str):
            return TransformationResult(
                position,
                "UNKNOWN",
                "position_standardization",
                True,
                applied_rules=["default_unknown"],
            )

        original_position = position
        cleaned_position = position.strip().lower()
        applied_rules = ["normalization"]

        # Check mappings
        position_mappings = self.config.get("position_mappings", {})

        # Direct match
        if cleaned_position in position_mappings:
            standardized = position_mappings[cleaned_position]
            applied_rules.append("direct_mapping")

            if self.config.get("logging", {}).get("log_transformations", False):
                logger.info(
                    f"Position standardized: '{original_position}' -> '{standardized}'"
                )

            return TransformationResult(
                original_position,
                standardized,
                "position_standardization",
                True,
                applied_rules=applied_rules,
            )

        # Partial match
        for key, value in position_mappings.items():
            if key in cleaned_position:
                applied_rules.append("partial_mapping")

                if self.config.get("logging", {}).get("log_transformations", False):
                    logger.info(
                        f"Position partially matched: '{original_position}' -> "
                        f"'{value}'"
                    )

                return TransformationResult(
                    original_position,
                    value,
                    "position_standardization",
                    True,
                    applied_rules=applied_rules,
                )

        # Return unknown if no match found
        applied_rules.append("unknown_fallback")
        return TransformationResult(
            original_position,
            "UNKNOWN",
            "position_standardization",
            True,
            applied_rules=applied_rules,
        )

    def handle_null_values(
        self, data: dict[str, Any], entity_type: str = "player_stats"
    ) -> dict[str, Any]:
        """
        Handle null values according to configured rules.

        Args:
            data: Dictionary containing data to clean
            entity_type: Type of entity (player_stats, team_stats, game_stats)

        Returns:
            Cleaned data dictionary
        """
        null_config = self.config.get("null_handling", {})
        required_fields = null_config.get("required_fields", {}).get(entity_type, [])
        default_values = null_config.get("default_values", {})

        cleaned_data = data.copy()
        applied_transformations = []

        # Check required fields
        for field in required_fields:
            if field not in cleaned_data or cleaned_data[field] is None:
                error_msg = f"Missing required field: {field}"
                logger.warning(error_msg)
                applied_transformations.append(
                    TransformationResult(
                        None,
                        None,
                        "null_validation",
                        False,
                        error_msg,
                        ["required_field_check"],
                    )
                )

        # Apply default values
        for field, default in default_values.items():
            if field not in cleaned_data or cleaned_data[field] is None:
                cleaned_data[field] = default
                applied_transformations.append(
                    TransformationResult(
                        None,
                        default,
                        "null_handling",
                        True,
                        applied_rules=["default_value"],
                    )
                )

        # Log transformations if enabled
        if self.config.get("logging", {}).get("log_transformations", False):
            for transformation in applied_transformations:
                if transformation.success:
                    logger.info("Applied default value for null field")

        self.transformation_log.extend(applied_transformations)
        return cleaned_data

    def clean_numeric_field(self, value: Any, field_name: str) -> TransformationResult:
        """
        Clean and validate numeric field with business rules.

        Args:
            value: Raw numeric value
            field_name: Name of the field for validation rules

        Returns:
            TransformationResult with cleaned numeric value
        """
        if value is None or value == "":
            return TransformationResult(
                value,
                None,
                "numeric_cleaning",
                True,
                applied_rules=["null_passthrough"],
            )

        original_value = value
        applied_rules = []

        # Handle string representations
        if isinstance(value, str):
            # Remove common formatting characters
            cleaned_str = re.sub(r"[,$%]", "", value.strip())
            applied_rules.append("format_cleaning")

            if not cleaned_str:
                return TransformationResult(
                    original_value,
                    None,
                    "numeric_cleaning",
                    True,
                    applied_rules=["empty_to_null"],
                )

            try:
                numeric_value = float(cleaned_str)
                applied_rules.append("string_to_numeric")
            except ValueError as e:
                return TransformationResult(
                    original_value,
                    None,
                    "numeric_cleaning",
                    False,
                    f"Invalid numeric value: {e}",
                    applied_rules,
                )
        else:
            numeric_value = float(value)

        # Apply validation rules
        validation_config = self.config.get("numeric_validation", {}).get(
            field_name, {}
        )

        if "min" in validation_config and numeric_value < validation_config["min"]:
            return TransformationResult(
                original_value,
                None,
                "numeric_cleaning",
                False,
                f"Value {numeric_value} below minimum {validation_config['min']}",
                applied_rules + ["range_validation"],
            )

        if "max" in validation_config and numeric_value > validation_config["max"]:
            return TransformationResult(
                original_value,
                None,
                "numeric_cleaning",
                False,
                f"Value {numeric_value} above maximum {validation_config['max']}",
                applied_rules + ["range_validation"],
            )

        applied_rules.append("validation_passed")

        if self.config.get("logging", {}).get("log_transformations", False):
            logger.debug(f"Numeric field cleaned: {field_name} = {numeric_value}")

        return TransformationResult(
            original_value,
            numeric_value,
            "numeric_cleaning",
            True,
            applied_rules=applied_rules,
        )

    def standardize_datetime(
        self, value: Any, field_name: str = "datetime"
    ) -> TransformationResult:
        """
        Standardize date/time values to consistent format.

        Args:
            value: Raw datetime value
            field_name: Name of the field (for specific handling)

        Returns:
            TransformationResult with standardized datetime
        """
        if value is None:
            return TransformationResult(
                value,
                None,
                "datetime_standardization",
                True,
                applied_rules=["null_passthrough"],
            )

        original_value = value
        applied_rules = ["datetime_parsing"]

        # Handle different input types
        if isinstance(value, datetime):
            dt = value
            applied_rules.append("datetime_object")
        elif isinstance(value, str):
            if not value.strip():
                return TransformationResult(
                    original_value,
                    None,
                    "datetime_standardization",
                    True,
                    applied_rules=["empty_to_null"],
                )

            # Try configured date formats
            input_formats = self.config.get("datetime_formats", {}).get(
                "input_formats", []
            )
            dt = None

            for fmt in input_formats:
                try:
                    dt = datetime.strptime(value.strip(), fmt)
                    applied_rules.append(f"format_{fmt}")
                    break
                except ValueError:
                    continue

            # Fallback to dateutil parser
            if dt is None:
                try:
                    dt = date_parser.parse(value.strip())
                    applied_rules.append("dateutil_parser")
                except Exception as e:
                    return TransformationResult(
                        original_value,
                        None,
                        "datetime_standardization",
                        False,
                        f"Unable to parse datetime: {e}",
                        applied_rules,
                    )
        else:
            return TransformationResult(
                original_value,
                None,
                "datetime_standardization",
                False,
                f"Invalid datetime type: {type(value)}",
                applied_rules,
            )

        # Format to standard output
        output_format = self.config.get("datetime_formats", {}).get(
            "output_format", "%Y-%m-%dT%H:%M:%SZ"
        )

        try:
            standardized = dt.strftime(output_format)
            applied_rules.append("standardized_format")

            if self.config.get("logging", {}).get("log_transformations", False):
                logger.debug(
                    f"Datetime standardized: '{original_value}' -> '{standardized}'"
                )

            return TransformationResult(
                original_value,
                standardized,
                "datetime_standardization",
                True,
                applied_rules=applied_rules,
            )
        except Exception as e:
            return TransformationResult(
                original_value,
                None,
                "datetime_standardization",
                False,
                f"Failed to format datetime: {e}",
                applied_rules,
            )

    def apply_fuzzy_matching(
        self, value: str, candidates: list[str], field_name: str
    ) -> TransformationResult:
        """
        Apply fuzzy string matching to find best candidate.

        Args:
            value: String value to match
            candidates: List of candidate values to match against
            field_name: Field name for configuration lookup

        Returns:
            TransformationResult with best match or original value
        """
        if not value or not isinstance(value, str) or not candidates:
            return TransformationResult(
                value,
                value,
                "fuzzy_matching",
                True,
                applied_rules=["no_matching_needed"],
            )

        fuzzy_config = self.config.get("fuzzy_matching", {})
        threshold = fuzzy_config.get("similarity_threshold", 85)

        # Use field-specific threshold if available
        field_threshold_key = f"{field_name}_threshold"
        if field_threshold_key in fuzzy_config:
            threshold = fuzzy_config[field_threshold_key]

        # Find best match
        best_match = process.extractOne(value, candidates)

        if best_match and best_match[1] >= threshold:
            if self.config.get("logging", {}).get("log_transformations", False):
                logger.info(
                    f"Fuzzy match found for {field_name}: '{value}' -> "
                    f"'{best_match[0]}' (score: {best_match[1]})"
                )

            return TransformationResult(
                value,
                best_match[0],
                "fuzzy_matching",
                True,
                applied_rules=[f"fuzzy_match_score_{best_match[1]}"],
            )
        else:
            return TransformationResult(
                value,
                value,
                "fuzzy_matching",
                True,
                applied_rules=["no_match_above_threshold"],
            )

    def process_batch(
        self, records: list[dict[str, Any]], entity_type: str = "player_stats"
    ) -> tuple[list[dict[str, Any]], list[TransformationResult]]:
        """
        Process a batch of records with all cleaning rules.

        Args:
            records: List of record dictionaries to process
            entity_type: Type of entity (player_stats, team_stats, game_stats)

        Returns:
            Tuple of (cleaned_records, transformation_results)
        """
        start_time = time.time()
        cleaned_records = []
        all_transformations = []

        performance_config = self.config.get("performance", {})
        batch_size = performance_config.get("batch_size", 1000)

        logger.info(f"Processing batch of {len(records)} {entity_type} records")

        for i, record in enumerate(records):
            try:
                cleaned_record = record.copy()
                record_transformations = []

                # Apply null value handling
                cleaned_record = self.handle_null_values(cleaned_record, entity_type)

                # Apply field-specific transformations
                for field_name, value in list(cleaned_record.items()):
                    # Team name standardization
                    if field_name in ["team_name", "team"]:
                        result = self.standardize_team_name(value)
                        if result.success:
                            cleaned_record[field_name] = result.transformed_value
                        record_transformations.append(result)

                    # Position standardization
                    elif field_name == "position":
                        result = self.standardize_position(value)
                        if result.success:
                            cleaned_record[field_name] = result.transformed_value
                        record_transformations.append(result)

                    # Numeric field cleaning
                    elif field_name in self.config.get("data_types", {}).get(
                        "numeric_fields", []
                    ):
                        result = self.clean_numeric_field(value, field_name)
                        if result.success and result.transformed_value is not None:
                            cleaned_record[field_name] = result.transformed_value
                        record_transformations.append(result)

                    # Date/time standardization
                    elif field_name in self.config.get("data_types", {}).get(
                        "date_fields", []
                    ):
                        result = self.standardize_datetime(value, field_name)
                        if result.success and result.transformed_value is not None:
                            cleaned_record[field_name] = result.transformed_value
                        record_transformations.append(result)

                cleaned_records.append(cleaned_record)
                all_transformations.extend(record_transformations)

                # Log progress for large batches
                if (i + 1) % batch_size == 0:
                    logger.info(f"Processed {i + 1}/{len(records)} records")

            except Exception as e:
                logger.error(f"Error processing record {i}: {e}")
                # Keep original record on error
                cleaned_records.append(record)

        end_time = time.time()
        processing_time = end_time - start_time
        records_per_minute = (
            (len(records) / processing_time) * 60 if processing_time > 0 else 0
        )

        logger.info(
            f"Batch processing completed: {len(records)} records in "
            f"{processing_time:.2f}s ({records_per_minute:.0f} records/minute)"
        )

        # Check performance target
        target_rpm = performance_config.get("target_records_per_minute", 10000)
        if records_per_minute < target_rpm:
            logger.warning(
                f"Performance below target: {records_per_minute:.0f} < "
                f"{target_rpm} records/minute"
            )

        return cleaned_records, all_transformations

    def get_transformation_summary(self) -> dict[str, Any]:
        """
        Get summary of all transformations applied.

        Returns:
            Dictionary with transformation statistics
        """
        total_transformations = len(self.transformation_log)
        successful_transformations = sum(
            1 for t in self.transformation_log if t.success
        )
        failed_transformations = total_transformations - successful_transformations

        # Group by transformation type
        by_type = {}
        for transformation in self.transformation_log:
            t_type = transformation.transformation_type
            if t_type not in by_type:
                by_type[t_type] = {"total": 0, "successful": 0, "failed": 0}

            by_type[t_type]["total"] += 1
            if transformation.success:
                by_type[t_type]["successful"] += 1
            else:
                by_type[t_type]["failed"] += 1

        return {
            "total_transformations": total_transformations,
            "successful_transformations": successful_transformations,
            "failed_transformations": failed_transformations,
            "success_rate": successful_transformations / total_transformations
            if total_transformations > 0
            else 0,
            "transformations_by_type": by_type,
            "config_version": self.config.get("version", "unknown"),
        }

    def clear_transformation_log(self) -> None:
        """Clear the transformation log."""
        self.transformation_log.clear()
