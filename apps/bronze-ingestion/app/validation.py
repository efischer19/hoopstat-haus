"""
Data validation module for bronze layer ingestion.

Provides validation functions that integrate JSON schema validation
with existing data quality checks from hoopstat-data library.
"""

from datetime import date, datetime
from typing import Any

import jsonschema
from hoopstat_data.quality import calculate_data_quality_score
from hoopstat_data.validation import validate_game_stats
from hoopstat_observability import get_logger

from .schemas import get_schema

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom exception for validation failures."""

    pass


class DataValidator:
    """
    Data validator for NBA API responses and ingested data.

    Combines JSON schema validation with domain-specific data quality checks.
    """

    def __init__(self):
        """Initialize the data validator."""
        self.validation_results = []

    def validate_api_response(
        self,
        response_data: Any,
        response_type: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Validate NBA API response against expected schema and quality rules.

        Args:
            response_data: Raw API response data
            response_type: Type of response ('schedule', 'box_score')
            context: Optional context for validation (e.g., expected date)

        Returns:
            Validation result dictionary with metrics and issues
        """
        result = {
            "valid": True,
            "issues": [],
            "metrics": {},
            "response_type": response_type,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            # Schema validation
            schema = get_schema(response_type)
            jsonschema.validate(response_data, schema)
            result["metrics"]["schema_valid"] = True
            logger.debug(f"Schema validation passed for {response_type}")

        except jsonschema.ValidationError as e:
            result["valid"] = False
            result["issues"].append(f"Schema validation failed: {e.message}")
            result["metrics"]["schema_valid"] = False
            logger.warning(f"Schema validation failed for {response_type}: {e.message}")

        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Schema validation error: {str(e)}")
            result["metrics"]["schema_valid"] = False
            logger.error(f"Schema validation error for {response_type}: {e}")

        # Type-specific validation
        if response_type == "schedule":
            self._validate_schedule_data(response_data, result, context)
        elif response_type == "box_score":
            self._validate_box_score_data(response_data, result, context)

        # Log validation results
        self._log_validation_metrics(result)

        return result

    def _validate_schedule_data(
        self, schedule_data: list[dict], result: dict, context: dict[str, Any] | None
    ) -> None:
        """Validate schedule-specific data quality."""
        if not isinstance(schedule_data, list):
            result["valid"] = False
            result["issues"].append("Schedule data is not a list")
            return

        result["metrics"]["game_count"] = len(schedule_data)

        # Check expected game count if context provided
        if context and "expected_min_games" in context:
            min_games = context["expected_min_games"]
            if len(schedule_data) < min_games:
                result["issues"].append(
                    f"Fewer games than expected: {len(schedule_data)} < {min_games}"
                )

        # Validate date consistency
        target_date = context.get("target_date") if context else None
        if target_date:
            self._validate_date_consistency(schedule_data, target_date, result)

        # Validate individual game records
        valid_games = 0
        for i, game in enumerate(schedule_data):
            if self._validate_individual_game(game, result, f"game_{i}"):
                valid_games += 1

        result["metrics"]["valid_games"] = valid_games
        result["metrics"]["game_validity_ratio"] = (
            valid_games / len(schedule_data) if schedule_data else 0.0
        )

    def _validate_box_score_data(
        self, box_score_data: dict, result: dict, context: dict[str, Any] | None
    ) -> None:
        """Validate box score-specific data quality."""
        if not isinstance(box_score_data, dict):
            result["valid"] = False
            result["issues"].append("Box score data is not a dictionary")
            return

        # Check which format we have: V3 (boxScoreTraditional) or legacy (resultSets)
        if "boxScoreTraditional" in box_score_data:
            # V3 format validation
            self._validate_box_score_v3_format(box_score_data, result, context)
        elif "resultSets" in box_score_data:
            # Legacy format validation
            self._validate_box_score_legacy_format(box_score_data, result, context)
        else:
            result["valid"] = False
            result["issues"].append(
                "Box score data missing both 'boxScoreTraditional' and 'resultSets'"
            )

    def _validate_box_score_v3_format(
        self, box_score_data: dict, result: dict, context: dict[str, Any] | None
    ) -> None:
        """Validate V3 format box score with boxScoreTraditional structure."""
        box_score = box_score_data.get("boxScoreTraditional", {})

        # Get team data - schema validation ensures these exist and have required fields
        home_team = box_score.get("homeTeam", {})
        away_team = box_score.get("awayTeam", {})

        # Count teams and players for metrics
        result["metrics"]["team_count"] = 2
        result["metrics"]["home_player_count"] = len(home_team.get("players", []))
        result["metrics"]["away_player_count"] = len(away_team.get("players", []))
        result["metrics"]["total_player_count"] = (
            result["metrics"]["home_player_count"]
            + result["metrics"]["away_player_count"]
        )

        # Extract and validate game metadata
        game_id = box_score.get("gameId")
        if game_id:
            game_metadata = {"game_id": game_id}
            self._validate_game_metadata(game_metadata, result, context)
        else:
            result["issues"].append("Missing gameId in V3 box score")

    def _validate_box_score_legacy_format(
        self, box_score_data: dict, result: dict, context: dict[str, Any] | None
    ) -> None:
        """Validate legacy format box score with resultSets structure."""
        result_sets = box_score_data.get("resultSets", [])
        result["metrics"]["result_set_count"] = len(result_sets)

        if not result_sets:
            result["valid"] = False
            result["issues"].append("No result sets found in box score")
            return

        # Validate each result set
        for i, result_set in enumerate(result_sets):
            self._validate_result_set(result_set, result, f"result_set_{i}")

        # Extract game metadata for validation
        game_metadata = self._extract_game_metadata(box_score_data)
        if game_metadata:
            self._validate_game_metadata(game_metadata, result, context)

    def _validate_date_consistency(
        self, schedule_data: list[dict], target_date: date, result: dict
    ) -> None:
        """Validate that schedule data is for the expected date."""
        inconsistent_dates = []

        for game in schedule_data:
            game_date_str = game.get("GAME_DATE")
            if game_date_str:
                try:
                    game_date = datetime.strptime(game_date_str, "%Y-%m-%d").date()
                    if game_date != target_date:
                        inconsistent_dates.append(game_date_str)
                except ValueError:
                    inconsistent_dates.append(f"invalid_format:{game_date_str}")

        if inconsistent_dates:
            result["issues"].append(
                f"Date inconsistencies found: {inconsistent_dates[:5]}..."
            )
            result["metrics"]["date_consistency"] = False
        else:
            result["metrics"]["date_consistency"] = True

    def _validate_individual_game(self, game: dict, result: dict, game_id: str) -> bool:
        """Validate an individual game record."""
        try:
            # Use existing validation from hoopstat-data
            game_stats = {
                "game_id": game.get("GAME_ID"),
                "home_score": game.get("PTS", 0),
                "away_score": game.get(
                    "PTS", 0
                ),  # Note: schedule doesn't have both scores
            }

            # Basic validation using existing tools
            if not validate_game_stats(game_stats):
                result["issues"].append(f"Game validation failed for {game_id}")
                return False

            # Check for reasonable values
            points = game.get("PTS")
            if points is not None and (points < 0 or points > 200):
                result["issues"].append(
                    f"Unrealistic points value for {game_id}: {points}"
                )
                return False

            return True

        except Exception as e:
            result["issues"].append(f"Error validating {game_id}: {str(e)}")
            return False

    def _validate_result_set(self, result_set: dict, result: dict, set_id: str) -> None:
        """Validate a result set from box score data."""
        headers = result_set.get("headers", [])
        rows = result_set.get("rowSet", [])

        result["metrics"][f"{set_id}_header_count"] = len(headers)
        result["metrics"][f"{set_id}_row_count"] = len(rows)

        # Validate row consistency
        if rows and headers:
            inconsistent_rows = 0
            for i, row in enumerate(rows):
                if len(row) != len(headers):
                    inconsistent_rows += 1
                    if inconsistent_rows <= 3:  # Limit issue reporting
                        result["issues"].append(
                            f"{set_id} row {i} has {len(row)} values but "
                            f"{len(headers)} headers"
                        )

            result["metrics"][f"{set_id}_inconsistent_rows"] = inconsistent_rows

    def _extract_game_metadata(self, box_score_data: dict) -> dict[str, Any] | None:
        """Extract game metadata from box score for validation."""
        try:
            parameters = box_score_data.get("parameters", {})
            game_id = parameters.get("GameID")

            if game_id:
                return {"game_id": game_id}

        except Exception as e:
            logger.warning(f"Failed to extract game metadata: {e}")

        return None

    def _validate_game_metadata(
        self, metadata: dict, result: dict, context: dict[str, Any] | None
    ) -> None:
        """Validate game metadata consistency."""
        game_id = metadata.get("game_id")

        # Validate game ID format
        if game_id and not game_id.isdigit():
            result["issues"].append(f"Invalid game ID format: {game_id}")

        # Check context consistency
        if context and "expected_game_id" in context:
            expected_id = context["expected_game_id"]
            if game_id != expected_id:
                result["issues"].append(
                    f"Game ID mismatch: expected {expected_id}, got {game_id}"
                )

    def _log_validation_metrics(self, result: dict) -> None:
        """Log validation metrics for monitoring."""
        metrics = result["metrics"]
        response_type = result["response_type"]

        logger.info(
            f"Validation completed for {response_type}",
            extra={
                "validation_result": result["valid"],
                "issue_count": len(result["issues"]),
                "metrics": metrics,
                "response_type": response_type,
            },
        )

    def validate_completeness(
        self, data: list[dict], expected_count: int | None = None, context: str = ""
    ) -> dict[str, Any]:
        """
        Validate data completeness against expectations.

        Args:
            data: List of data records to validate
            expected_count: Expected number of records
            context: Context description for logging

        Returns:
            Completeness validation result
        """
        result = {
            "complete": True,
            "actual_count": len(data),
            "expected_count": expected_count,
            "issues": [],
            "context": context,
        }

        if expected_count is not None:
            if len(data) == 0:
                result["complete"] = False
                result["issues"].append("No data found")
            elif len(data) < expected_count:
                result["complete"] = False
                result["issues"].append(
                    f"Incomplete data: {len(data)} < {expected_count} expected"
                )

        # Log completeness metrics
        logger.info(
            f"Completeness check for {context}",
            extra={
                "complete": result["complete"],
                "actual_count": result["actual_count"],
                "expected_count": expected_count,
                "issue_count": len(result["issues"]),
            },
        )

        return result

    def calculate_quality_score(self, data: dict[str, Any]) -> float:
        """
        Calculate overall data quality score using hoopstat-data quality tools.

        Args:
            data: Data record to assess

        Returns:
            Quality score from 0.0 to 1.0
        """
        try:
            return calculate_data_quality_score(data)
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.0
