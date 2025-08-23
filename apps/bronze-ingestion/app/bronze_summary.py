"""
Bronze layer summary manager for generating metadata and insights.
"""

import json
from datetime import date, datetime
from typing import Any

from hoopstat_observability import get_logger

from .s3_manager import BronzeS3Manager

logger = get_logger(__name__)


class BronzeSummaryManager:
    """Manager for generating and storing bronze layer summary data."""

    def __init__(self, s3_manager: BronzeS3Manager):
        """Initialize the summary manager."""
        self.s3_manager = s3_manager

    def generate_summary(
        self, target_date: date, games_count: int, successful_box_scores: int
    ) -> dict[str, Any]:
        """
        Generate comprehensive bronze layer summary data.

        Args:
            target_date: The date that was processed
            games_count: Number of games found for the date
            successful_box_scores: Number of box scores successfully ingested

        Returns:
            Dictionary containing bronze layer summary
        """
        try:
            logger.info(f"Generating bronze layer summary for {target_date}")

            # Get current bronze layer statistics
            bronze_stats = self._collect_bronze_statistics(target_date)

            # Calculate success rates
            box_score_success_rate = (
                successful_box_scores / games_count if games_count > 0 else 0.0
            )

            # Build comprehensive summary
            summary = {
                "summary_version": "1.0",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "bronze_layer_stats": {
                    "last_ingestion_date": target_date.isoformat(),
                    "last_successful_run": datetime.utcnow().isoformat() + "Z",
                    "total_entities": len(bronze_stats["entities"]),
                    "entities": bronze_stats["entities"],
                    "data_quality": {
                        "last_run_games_count": games_count,
                        "last_run_successful_box_scores": successful_box_scores,
                        "last_run_success_rate": round(box_score_success_rate, 2),
                        "last_quality_check": datetime.utcnow().isoformat() + "Z",
                    },
                    "storage_info": bronze_stats["storage_info"],
                },
            }

            logger.info(
                "Bronze summary generated successfully",
                extra={
                    "target_date": target_date.isoformat(),
                    "total_entities": summary["bronze_layer_stats"]["total_entities"],
                    "total_files": summary["bronze_layer_stats"]["storage_info"][
                        "total_files"
                    ],
                    "games_processed": games_count,
                    "box_scores_success_rate": box_score_success_rate,
                },
            )

            return summary

        except Exception as e:
            logger.error(f"Failed to generate bronze summary for {target_date}: {e}")
            raise

    def store_summary(self, summary: dict[str, Any]) -> str:
        """
        Store bronze layer summary to S3.

        Args:
            summary: Summary data dictionary to store

        Returns:
            S3 key where summary was stored
        """
        try:
            # Store summary at well-known location for easy access
            key = "_metadata/summary.json"

            # Convert summary to JSON bytes
            summary_json = json.dumps(summary, indent=2, default=str)
            summary_bytes = summary_json.encode("utf-8")

            # Upload to S3
            self.s3_manager.s3_client.put_object(
                Bucket=self.s3_manager.bucket_name,
                Key=key,
                Body=summary_bytes,
                ContentType="application/json",
                Metadata={
                    "summary_version": summary.get("summary_version", "1.0"),
                    "generated_at": summary.get("generated_at", ""),
                    "type": "bronze_layer_summary",
                },
            )

            logger.info(
                f"Bronze summary stored to s3://{self.s3_manager.bucket_name}/{key}"
            )
            return key

        except Exception as e:
            logger.error(f"Failed to store bronze summary: {e}")
            raise

    def update_bronze_summary(
        self, target_date: date, games_count: int, successful_box_scores: int
    ) -> str:
        """
        Generate and store bronze layer summary in one operation.

        Args:
            target_date: The date that was processed
            games_count: Number of games found for the date
            successful_box_scores: Number of box scores successfully ingested

        Returns:
            S3 key where summary was stored
        """
        try:
            summary = self.generate_summary(
                target_date, games_count, successful_box_scores
            )
            key = self.store_summary(summary)

            logger.info(
                f"Bronze layer summary updated successfully for {target_date}",
                extra={
                    "s3_key": key,
                    "target_date": target_date.isoformat(),
                    "summary_size_bytes": len(json.dumps(summary, default=str)),
                },
            )

            return key

        except Exception as e:
            logger.error(f"Failed to update bronze summary for {target_date}: {e}")
            raise

    def _collect_bronze_statistics(self, target_date: date) -> dict[str, Any]:
        """
        Collect current bronze layer statistics.

        Args:
            target_date: Reference date for statistics collection

        Returns:
            Dictionary with entities and storage information
        """
        try:
            # Get entities that have data for the target date
            entities_for_date = self.s3_manager.list_entities_for_date(target_date)

            # Collect statistics for each entity
            entities_stats = {}
            total_files = 0
            estimated_size_mb = 0.0

            for entity in entities_for_date:
                entity_stats = self._get_entity_statistics(entity, target_date)
                entities_stats[entity] = entity_stats
                total_files += entity_stats["file_count"]
                estimated_size_mb += entity_stats["estimated_size_mb"]

            # Also check for any additional entities by scanning the raw/ prefix
            all_entities = self._scan_all_entities()
            for entity in all_entities:
                if entity not in entities_stats:
                    # This entity doesn't have data for target_date, but exists
                    entity_stats = self._get_entity_latest_statistics(entity)
                    if entity_stats:  # Only include if it has some data
                        entities_stats[entity] = entity_stats
                        total_files += entity_stats["file_count"]
                        estimated_size_mb += entity_stats["estimated_size_mb"]

            return {
                "entities": entities_stats,
                "storage_info": {
                    "total_files": total_files,
                    "estimated_size_mb": round(estimated_size_mb, 2),
                },
            }

        except Exception as e:
            logger.error(f"Failed to collect bronze statistics: {e}")
            # Return empty stats rather than failing completely
            return {
                "entities": {},
                "storage_info": {"total_files": 0, "estimated_size_mb": 0.0},
            }

    def _get_entity_statistics(self, entity: str, target_date: date) -> dict[str, Any]:
        """Get statistics for a specific entity on a specific date."""
        try:
            date_str = target_date.strftime("%Y-%m-%d")
            prefix = f"raw/{entity}/date={date_str}/"

            # List objects for this entity/date combination
            response = self.s3_manager.s3_client.list_objects_v2(
                Bucket=self.s3_manager.bucket_name, Prefix=prefix
            )

            file_count = response.get("KeyCount", 0)
            total_size = sum(obj.get("Size", 0) for obj in response.get("Contents", []))
            size_mb = total_size / (1024 * 1024) if total_size > 0 else 0.0

            # Get the latest modified time
            last_modified = None
            if response.get("Contents"):
                last_modified = max(
                    obj["LastModified"] for obj in response["Contents"]
                ).isoformat()

            return {
                "last_updated": last_modified,
                "file_count": file_count,
                "estimated_size_mb": round(size_mb, 2),
                "last_processed_date": target_date.isoformat(),
            }

        except Exception as e:
            logger.warning(f"Failed to get statistics for entity {entity}: {e}")
            return {
                "last_updated": None,
                "file_count": 0,
                "estimated_size_mb": 0.0,
                "last_processed_date": target_date.isoformat(),
            }

    def _get_entity_latest_statistics(self, entity: str) -> dict[str, Any] | None:
        """Get latest statistics for an entity (no target_date data)."""
        try:
            prefix = f"raw/{entity}/"

            # List objects for this entity
            response = self.s3_manager.s3_client.list_objects_v2(
                Bucket=self.s3_manager.bucket_name,
                Prefix=prefix,
                MaxKeys=100,  # Limit to avoid expensive calls
            )

            if not response.get("Contents"):
                return None

            file_count = response.get("KeyCount", 0)
            total_size = sum(obj.get("Size", 0) for obj in response.get("Contents", []))
            size_mb = total_size / (1024 * 1024) if total_size > 0 else 0.0

            # Get the latest modified time
            last_modified = max(
                obj["LastModified"] for obj in response["Contents"]
            ).isoformat()

            return {
                "last_updated": last_modified,
                "file_count": file_count,
                "estimated_size_mb": round(size_mb, 2),
                "last_processed_date": None,  # No data for current target date
            }

        except Exception as e:
            logger.warning(f"Failed to get latest statistics for entity {entity}: {e}")
            return None

    def _scan_all_entities(self) -> list[str]:
        """Scan for all entities in the bronze layer."""
        try:
            prefix = "raw/"

            response = self.s3_manager.s3_client.list_objects_v2(
                Bucket=self.s3_manager.bucket_name, Prefix=prefix, Delimiter="/"
            )

            entities = []
            for common_prefix in response.get("CommonPrefixes", []):
                entity_prefix = common_prefix["Prefix"]
                # Extract entity name from prefix like "raw/schedule/"
                entity = entity_prefix.replace("raw/", "").rstrip("/")
                entities.append(entity)

            return entities

        except Exception as e:
            logger.warning(f"Failed to scan all entities: {e}")
            return []
