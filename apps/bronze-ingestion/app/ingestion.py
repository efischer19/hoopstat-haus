"""
Date-scoped ingestion logic for bronze layer.
"""

from datetime import date
from typing import Any

from hoopstat_nba_api import NBAClient
from hoopstat_observability import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .bronze_summary import BronzeSummaryManager
from .config import BronzeIngestionConfig
from .quarantine import DataQuarantine
from .s3_manager import BronzeS3Manager
from .validation import DataValidator

logger = get_logger(__name__)


class DateScopedIngestion:
    """Date-scoped NBA data ingestion for bronze layer."""

    def __init__(self, config: BronzeIngestionConfig | None = None):
        """Initialize the ingestion system."""
        self.config = config or BronzeIngestionConfig.load()
        self.nba_client = NBAClient()
        self.s3_manager = BronzeS3Manager(
            bucket_name=self.config.bronze_bucket, region_name=self.config.aws_region
        )
        self.validator = DataValidator()
        self.quarantine = DataQuarantine(self.s3_manager)
        self.summary_manager = BronzeSummaryManager(self.s3_manager)

    def run(self, target_date: date, dry_run: bool = False) -> bool:
        """
        Run the date-scoped ingestion process.

        Args:
            target_date: Date to fetch data for
            dry_run: If True, don't write data to S3

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Starting ingestion for {target_date}")

            # Step 1: Fetch and validate schedule for the date
            games = self._fetch_and_validate_schedule(target_date)

            # Step 2: Early exit if no games for this date
            if not games:
                logger.info(f"No games found for {target_date}, exiting successfully")

                # Still update bronze summary even with no games (unless dry run)
                if not dry_run:
                    self.summary_manager.update_bronze_summary(target_date, 0, 0)

                return True

            logger.info(f"Found {len(games)} games for {target_date}")

            # Step 3: Validate completeness and data quality
            self._validate_ingestion_completeness(games, target_date)

            # Step 4: Store schedule as JSON (if validation passed)
            if not dry_run:
                self._store_schedule(games, target_date)
            else:
                logger.info("Dry run: would store schedule data")

            # Step 5: Fetch and validate box scores for each game
            successful_box_scores = 0
            for game in games:
                game_id = str(game.get("GAME_ID", ""))
                if game_id:
                    box_score = self._fetch_and_validate_box_score(game_id, target_date)
                    if box_score and not dry_run:
                        self._store_box_score(box_score, game_id, target_date)
                        successful_box_scores += 1
                    elif box_score:
                        logger.info(
                            f"Dry run: would store box score for game {game_id}"
                        )
                        successful_box_scores += 1

            # Step 6: Log final ingestion metrics
            self._log_ingestion_summary(target_date, len(games), successful_box_scores)

            # Step 7: Generate and store bronze layer summary (unless dry run)
            if not dry_run:
                self.summary_manager.update_bronze_summary(
                    target_date, len(games), successful_box_scores
                )

            logger.info(f"Ingestion completed for {target_date}")
            return True

        except Exception as e:
            logger.error(f"Ingestion failed for {target_date}: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _fetch_schedule(self, target_date: date) -> list[dict[str, Any]]:
        """Fetch games schedule for the target date."""
        try:
            logger.info(f"Fetching schedule for {target_date}")
            games = self.nba_client.get_games_for_date(target_date)
            logger.info(f"Successfully fetched {len(games)} games")
            return games
        except Exception as e:
            logger.error(f"Failed to fetch schedule for {target_date}: {e}")
            raise

    def _fetch_and_validate_schedule(self, target_date: date) -> list[dict[str, Any]]:
        """Fetch and validate games schedule for the target date."""
        try:
            # Fetch raw schedule data
            raw_schedule = self._fetch_schedule(target_date)

            # Validate the schedule data
            validation_context = {
                "target_date": target_date,
                "expected_min_games": 0,  # No minimum expectation for schedule
            }

            validation_result = self.validator.validate_api_response(
                raw_schedule, "schedule", validation_context
            )

            # Handle validation failures
            if self.quarantine.should_quarantine(validation_result):
                self.quarantine.quarantine_api_response(
                    raw_schedule, validation_result, "get_games_for_date", target_date
                )

                # If validation completely failed, return empty list
                if not validation_result.get("valid", False):
                    logger.warning(
                        f"Schedule validation failed for {target_date}, "
                        "returning empty list"
                    )
                    return []

            # Log validation success
            logger.info(
                f"Schedule validation completed for {target_date}",
                extra={
                    "games_count": len(raw_schedule),
                    "validation_valid": validation_result.get("valid", False),
                    "issues_count": len(validation_result.get("issues", [])),
                },
            )

            return raw_schedule

        except Exception as e:
            logger.error(
                f"Failed to fetch and validate schedule for {target_date}: {e}"
            )
            raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _fetch_box_score(self, game_id: str) -> dict[str, Any] | None:
        """Fetch box score for a specific game."""
        try:
            logger.debug(f"Fetching box score for game {game_id}")
            box_score = self.nba_client.get_box_score(game_id)
            logger.debug(f"Successfully fetched box score for game {game_id}")
            return box_score
        except Exception as e:
            logger.warning(f"Failed to fetch box score for game {game_id}: {e}")
            return None

    def _fetch_and_validate_box_score(
        self, game_id: str, target_date: date
    ) -> dict[str, Any] | None:
        """Fetch and validate box score for a specific game."""
        try:
            # Fetch raw box score data
            raw_box_score = self._fetch_box_score(game_id)

            if raw_box_score is None:
                return None

            # Validate the box score data
            validation_context = {
                "expected_game_id": game_id,
                "target_date": target_date,
            }

            validation_result = self.validator.validate_api_response(
                raw_box_score, "box_score", validation_context
            )

            # Handle validation failures
            if self.quarantine.should_quarantine(validation_result):
                self.quarantine.quarantine_api_response(
                    raw_box_score,
                    validation_result,
                    "get_box_score",
                    target_date,
                    {"game_id": game_id},
                )

                # If validation completely failed, return None
                if not validation_result.get("valid", False):
                    logger.warning(f"Box score validation failed for game {game_id}")
                    return None

            # Log validation success
            logger.debug(
                f"Box score validation completed for game {game_id}",
                extra={
                    "game_id": game_id,
                    "validation_valid": validation_result.get("valid", False),
                    "issues_count": len(validation_result.get("issues", [])),
                },
            )

            return raw_box_score

        except Exception as e:
            logger.warning(
                f"Failed to fetch and validate box score for game {game_id}: {e}"
            )
            return None

    def _store_schedule(self, games: list[dict[str, Any]], target_date: date) -> None:
        """Store schedule data as JSON in S3 with date-based partitioning."""
        try:
            # Store as JSON (no DataFrame conversion needed)
            self.s3_manager.store_json(
                games, entity="schedule", target_date=target_date
            )
            logger.info(f"Stored schedule data for {target_date}")

        except Exception as e:
            logger.error(f"Failed to store schedule data: {e}")
            raise

    def _store_box_score(
        self, box_score: dict[str, Any], game_id: str, target_date: date
    ) -> None:
        """Store box score data as JSON in S3 with date-based partitioning."""
        try:
            # Store raw nested box score structure as JSON (ADR-031: one file per game)
            self.s3_manager.store_json(
                box_score,
                entity="box_scores",
                target_date=target_date,
                game_id=game_id,
            )
            logger.debug(f"Stored box score for game {game_id}")

        except Exception as e:
            logger.error(f"Failed to store box score for game {game_id}: {e}")
            raise

    def _validate_ingestion_completeness(
        self, games: list[dict[str, Any]], target_date: date
    ) -> None:
        """Validate completeness of ingested data for the target date."""
        try:
            # Validate completeness using the validator
            completeness_result = self.validator.validate_completeness(
                games, expected_count=None, context=f"schedule_for_{target_date}"
            )

            # Log completeness metrics
            logger.info(
                f"Data completeness check for {target_date}",
                extra={
                    "target_date": target_date.isoformat(),
                    "complete": completeness_result["complete"],
                    "actual_count": completeness_result["actual_count"],
                    "expected_count": completeness_result["expected_count"],
                    "context": completeness_result["context"],
                },
            )

            # For schedule data, we don't enforce minimum counts since some
            # days have no games. The check serves mainly for logging and
            # monitoring purposes

        except Exception as e:
            logger.error(f"Error validating completeness for {target_date}: {e}")

    def _log_ingestion_summary(
        self, target_date: date, games_count: int, successful_box_scores: int
    ) -> None:
        """Log summary metrics for the ingestion run."""
        try:
            # Calculate success rates
            box_score_success_rate = (
                successful_box_scores / games_count if games_count > 0 else 0.0
            )

            # Log comprehensive ingestion metrics
            logger.info(
                f"Ingestion summary for {target_date}",
                extra={
                    "target_date": target_date.isoformat(),
                    "total_games": games_count,
                    "successful_box_scores": successful_box_scores,
                    "box_score_success_rate": round(box_score_success_rate, 2),
                    "ingestion_status": "completed",
                    "data_quality_check": "passed" if games_count > 0 else "no_games",
                },
            )

        except Exception as e:
            logger.error(f"Error logging ingestion summary for {target_date}: {e}")
