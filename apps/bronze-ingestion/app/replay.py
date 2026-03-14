"""
Quarantine replay orchestration module.

Provides the core replay logic for re-processing quarantined data through
the Bronze-to-Silver pipeline. Handles transform selection, Bronze path
writing, Silver processing invocation, and quarantine status updates.
"""

import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from hoopstat_observability import get_logger

from .quarantine import DataQuarantine, ErrorClassification
from .s3_manager import BronzeS3Manager
from .transforms import (
    IdentityTransform,
    ReplayTransform,
    RoundingToleranceTransform,
    TransformError,
    get_transform_for_classification,
)

logger = get_logger(__name__)

# Map from CLI-friendly transform names to transform classes
_TRANSFORM_NAMES: dict[str, type[ReplayTransform]] = {
    "identity": IdentityTransform,
    "rounding_tolerance": RoundingToleranceTransform,
}

# Map from quarantine data_type to Bronze entity name
_DATA_TYPE_TO_ENTITY: dict[str, str] = {
    "box_score": "box",
    "schedule": "schedule",
    "api_response": "box",
}


@dataclass
class ReplayResult:
    """Result of a single replay operation."""

    s3_key: str
    success: bool
    error: str | None = None
    transform_applied: str | None = None
    dry_run: bool = False


@dataclass
class BatchReplayResult:
    """Result of a batch replay operation."""

    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list[ReplayResult] = field(default_factory=list)


def get_transform_by_name(name: str) -> ReplayTransform:
    """
    Get a transform instance by its CLI-friendly name.

    Args:
        name: Transform name (e.g., 'identity', 'rounding_tolerance').

    Returns:
        A ReplayTransform instance.

    Raises:
        ValueError: If the name is not recognized.
    """
    transform_cls = _TRANSFORM_NAMES.get(name)
    if transform_cls is None:
        valid_names = ", ".join(sorted(_TRANSFORM_NAMES.keys()))
        raise ValueError(
            f"Unknown transform name: '{name}'. Valid names: {valid_names}"
        )
    return transform_cls()


class ReplayOrchestrator:
    """
    Orchestrates the replay of quarantined data through the pipeline.

    Handles the full replay lifecycle: fetch record, apply transform,
    write to Bronze, invoke Silver processing, and update status.
    """

    def __init__(
        self,
        s3_manager: BronzeS3Manager,
        quarantine: DataQuarantine,
        silver_processing_dir: str | None = None,
    ):
        """
        Initialize the replay orchestrator.

        Args:
            s3_manager: S3 manager for Bronze layer operations.
            quarantine: DataQuarantine instance for record management.
            silver_processing_dir: Path to the silver-processing app directory.
                If None, silver processing invocation is skipped.
        """
        self.s3_manager = s3_manager
        self.quarantine = quarantine
        self.silver_processing_dir = silver_processing_dir

    def replay_single(
        self,
        s3_key: str,
        transform_override: ReplayTransform | None = None,
        dry_run: bool = False,
    ) -> ReplayResult:
        """
        Replay a single quarantined file.

        Steps:
        1. Fetch the quarantine record from S3
        2. Determine error classification
        3. Select transform (default or override)
        4. Apply transform to original payload
        5. Write transformed payload to Bronze path
        6. Invoke Silver processing for the date
        7. Update quarantine record status
        8. Return result

        Args:
            s3_key: S3 key of the quarantine record.
            transform_override: Optional transform to use instead of default.
            dry_run: If True, validate without writing.

        Returns:
            ReplayResult with success/failure details.
        """
        logger.info(
            "Starting replay",
            extra={"s3_key": s3_key, "dry_run": dry_run},
        )

        # Step 1: Fetch quarantine record
        record = self._fetch_record(s3_key)
        if record is None:
            error_msg = f"Could not fetch quarantine record: {s3_key}"
            logger.error(error_msg, extra={"s3_key": s3_key})
            return ReplayResult(s3_key=s3_key, success=False, error=error_msg)

        metadata = record.get("metadata", {})
        classification_value = metadata.get("error_classification", "unknown")

        # Step 2: Determine classification
        try:
            classification = ErrorClassification(classification_value)
        except ValueError:
            classification = ErrorClassification.UNKNOWN

        # Step 3: Select transform
        if transform_override is not None:
            transform = transform_override
        else:
            transform = get_transform_for_classification(classification)

        transform_name = type(transform).__name__

        logger.info(
            "Applying transform",
            extra={
                "s3_key": s3_key,
                "classification": classification.value,
                "transform": transform_name,
            },
        )

        # Step 4: Apply transform
        try:
            transform_result = transform.transform(record)
        except TransformError as e:
            error_msg = f"Transform failed: {e}"
            logger.error(error_msg, extra={"s3_key": s3_key})
            self._update_quarantine_failed(s3_key, record, error_msg, transform_name)
            return ReplayResult(
                s3_key=s3_key,
                success=False,
                error=error_msg,
                transform_applied=transform_name,
            )

        transformed_data = transform_result["data"]
        transform_metadata = transform_result["transform_metadata"]
        applied_transform_type = transform_metadata.get(
            "transform_type", transform_name
        )

        # Step 5: Write to Bronze path (unless dry run)
        if dry_run:
            logger.info(
                "Dry run -- skipping Bronze write and Silver processing",
                extra={
                    "s3_key": s3_key,
                    "transform_applied": applied_transform_type,
                    "transform_metadata": transform_metadata,
                },
            )
            return ReplayResult(
                s3_key=s3_key,
                success=True,
                transform_applied=applied_transform_type,
                dry_run=True,
            )

        try:
            bronze_key = self._write_to_bronze(transformed_data, metadata)
            logger.info(
                "Wrote transformed data to Bronze",
                extra={"s3_key": s3_key, "bronze_key": bronze_key},
            )
        except Exception as e:
            error_msg = f"Failed to write to Bronze: {e}"
            logger.error(error_msg, extra={"s3_key": s3_key})
            self._update_quarantine_failed(
                s3_key, record, error_msg, applied_transform_type
            )
            return ReplayResult(
                s3_key=s3_key,
                success=False,
                error=error_msg,
                transform_applied=applied_transform_type,
            )

        # Step 6: Invoke Silver processing
        target_date_str = metadata.get("target_date", "")
        silver_success = self._invoke_silver_processing(target_date_str)

        # Step 7: Update quarantine record status
        if silver_success:
            self._update_quarantine_resolved(
                s3_key, record, applied_transform_type, transform_metadata
            )
            logger.info(
                "Replay succeeded",
                extra={
                    "s3_key": s3_key,
                    "transform_applied": applied_transform_type,
                    "status": "resolved",
                },
            )
            return ReplayResult(
                s3_key=s3_key,
                success=True,
                transform_applied=applied_transform_type,
            )
        else:
            error_msg = "Silver processing failed for the replayed data"
            self._update_quarantine_failed(
                s3_key, record, error_msg, applied_transform_type
            )
            logger.warning(
                "Replay failed at Silver processing",
                extra={
                    "s3_key": s3_key,
                    "transform_applied": applied_transform_type,
                    "status": "failed",
                },
            )
            return ReplayResult(
                s3_key=s3_key,
                success=False,
                error=error_msg,
                transform_applied=applied_transform_type,
            )

    def replay_batch(
        self,
        items: list[dict[str, Any]],
        transform_override: ReplayTransform | None = None,
        dry_run: bool = False,
    ) -> BatchReplayResult:
        """
        Replay multiple quarantined files sequentially.

        Args:
            items: List of quarantine item dicts (must have 'key' field).
            transform_override: Optional transform override for all items.
            dry_run: If True, validate without writing.

        Returns:
            BatchReplayResult with summary counts and individual results.
        """
        batch_result = BatchReplayResult(total=len(items))

        logger.info(
            "Starting batch replay",
            extra={"total_items": len(items), "dry_run": dry_run},
        )

        for item in items:
            s3_key = item["key"]
            result = self.replay_single(
                s3_key,
                transform_override=transform_override,
                dry_run=dry_run,
            )
            batch_result.results.append(result)
            if result.success:
                batch_result.succeeded += 1
            else:
                batch_result.failed += 1

        logger.info(
            "Batch replay completed",
            extra={
                "total": batch_result.total,
                "succeeded": batch_result.succeeded,
                "failed": batch_result.failed,
            },
        )

        return batch_result

    def _fetch_record(self, s3_key: str) -> dict[str, Any] | None:
        """Fetch and parse a quarantine record from S3."""
        try:
            response = self.s3_manager.s3_client.get_object(
                Bucket=self.s3_manager.bucket_name,
                Key=s3_key,
            )
            body = response["Body"].read().decode("utf-8")
            return json.loads(body)
        except Exception as e:
            logger.error(f"Failed to fetch quarantine record {s3_key}: {e}")
            return None

    def _write_to_bronze(self, data: dict[str, Any], metadata: dict[str, Any]) -> str:
        """
        Write transformed data to the correct Bronze location.

        Determines the entity type and date from the quarantine metadata,
        then writes the data to the appropriate S3 path.

        Args:
            data: Transformed payload data.
            metadata: Quarantine record metadata.

        Returns:
            The S3 key where data was written.
        """
        data_type = metadata.get("data_type", "box_score")
        entity = _DATA_TYPE_TO_ENTITY.get(data_type, "box")
        target_date_str = metadata.get("target_date", "")

        try:
            target_date = date.fromisoformat(target_date_str)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid target_date in quarantine metadata: {target_date_str}"
            ) from e

        # Extract game_id from context or data
        game_id = self._extract_game_id(data, metadata)

        return self.s3_manager.store_json(
            data,
            entity=entity,
            target_date=target_date,
            game_id=game_id,
        )

    def _extract_game_id(self, data: Any, metadata: dict[str, Any]) -> str | None:
        """
        Extract game_id from data or metadata context.

        Checks the quarantine context for game_id (from request_params),
        then falls back to extracting from the data payload itself.
        """
        # Try context first (set by quarantine_api_response)
        context = metadata.get("context", {})
        game_id = context.get("game_id")
        if game_id:
            return str(game_id)

        # Try request_params within context
        request_params = context.get("request_params", {})
        game_id = request_params.get("game_id")
        if game_id:
            return str(game_id)

        # Try extracting from box score data (only if data is a dict)
        if isinstance(data, dict):
            box_score = data.get("boxScoreTraditional", {})
            game_id = box_score.get("gameId")
            if game_id:
                return str(game_id)

        return None

    def _invoke_silver_processing(self, target_date_str: str) -> bool:
        """
        Invoke Silver processing for the affected date via subprocess.

        Uses subprocess invocation to maintain app boundary separation
        per ADR-008 monorepo structure.

        Args:
            target_date_str: Date string in YYYY-MM-DD format.

        Returns:
            True if Silver processing succeeded, False otherwise.
        """
        if not self.silver_processing_dir:
            logger.info(
                "Silver processing directory not configured -- skipping",
                extra={"target_date": target_date_str},
            )
            return True

        silver_dir = Path(self.silver_processing_dir)
        if not silver_dir.exists():
            logger.warning(
                "Silver processing directory not found -- skipping",
                extra={
                    "silver_processing_dir": self.silver_processing_dir,
                    "target_date": target_date_str,
                },
            )
            return True

        try:
            cmd = [
                "poetry",
                "run",
                "python",
                "-m",
                "app.main",
                "process",
                "--date",
                target_date_str,
            ]

            # Pass bucket config via environment
            env_vars = {
                "BRONZE_BUCKET": self.s3_manager.bucket_name,
            }

            logger.info(
                "Invoking Silver processing",
                extra={
                    "command": " ".join(cmd),
                    "target_date": target_date_str,
                    "cwd": str(silver_dir),
                },
            )

            run_env = {**os.environ, **env_vars}
            result = subprocess.run(
                cmd,
                cwd=str(silver_dir),
                capture_output=True,
                text=True,
                timeout=300,
                env=run_env,
            )

            if result.returncode == 0:
                logger.info(
                    "Silver processing completed successfully",
                    extra={"target_date": target_date_str},
                )
                return True
            else:
                logger.error(
                    "Silver processing failed",
                    extra={
                        "target_date": target_date_str,
                        "returncode": result.returncode,
                        "stderr": result.stderr[:500] if result.stderr else "",
                    },
                )
                return False

        except subprocess.TimeoutExpired:
            logger.error(
                "Silver processing timed out",
                extra={"target_date": target_date_str},
            )
            return False
        except Exception as e:
            logger.error(
                f"Failed to invoke Silver processing: {e}",
                extra={"target_date": target_date_str},
            )
            return False

    def _update_quarantine_resolved(
        self,
        s3_key: str,
        record: dict[str, Any],
        transform_type: str,
        transform_metadata: dict[str, Any],
    ) -> None:
        """
        Update quarantine record status to 'resolved'.

        Adds replay_timestamp and transform_applied metadata.
        """
        record["metadata"]["status"] = "resolved"
        record["metadata"]["replay_timestamp"] = datetime.now(UTC).isoformat()
        record["metadata"]["transform_applied"] = transform_type
        record["metadata"]["transform_metadata"] = transform_metadata

        self._store_updated_record(s3_key, record)

    def _update_quarantine_failed(
        self,
        s3_key: str,
        record: dict[str, Any],
        error_msg: str,
        transform_type: str,
    ) -> None:
        """
        Update quarantine record status to 'failed'.

        Adds replay_timestamp, replay_error, and increments retry_count.
        """
        record["metadata"]["status"] = "failed"
        record["metadata"]["replay_timestamp"] = datetime.now(UTC).isoformat()
        record["metadata"]["replay_error"] = error_msg
        record["metadata"]["transform_applied"] = transform_type
        record["metadata"]["retry_count"] = record["metadata"].get("retry_count", 0) + 1

        self._store_updated_record(s3_key, record)

    def _store_updated_record(self, s3_key: str, record: dict[str, Any]) -> None:
        """Write the updated quarantine record back to S3."""
        try:
            json_data = json.dumps(record, default=str, indent=2)
            self.s3_manager.s3_client.put_object(
                Bucket=self.s3_manager.bucket_name,
                Key=s3_key,
                Body=json_data.encode("utf-8"),
                ContentType="application/json",
            )
            logger.debug(f"Updated quarantine record at {s3_key}")
        except Exception as e:
            logger.error(f"Failed to update quarantine record at {s3_key}: {e}")
