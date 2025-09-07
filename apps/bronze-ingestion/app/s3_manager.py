"""
S3 manager for bronze layer with JSON storage (ADR-025).
"""

import json
from datetime import date

import boto3
from hoopstat_observability import get_logger

logger = get_logger(__name__)


class BronzeS3Manager:
    """S3 manager for bronze layer with JSON storage (ADR-025)."""

    def __init__(self, bucket_name: str, region_name: str = "us-east-1"):
        """Initialize S3 manager."""
        self.bucket_name = bucket_name
        self.region_name = region_name

        try:
            self.s3_client = boto3.client("s3", region_name=region_name)
            logger.info(f"Initialized S3 manager for bucket: {bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise

    def store_json(self, data: dict, entity: str, target_date: date) -> str:
        """
        Store dictionary as JSON in S3 following ADR-025 JSON storage format.

        Args:
            data: Dictionary to store as JSON
            entity: Entity type (schedule, box_scores, etc.)
            target_date: Date for partitioning

        Returns:
            S3 key where data was stored
        """
        # Key structure: s3://<bronze-bucket>/raw/<entity>/date=YYYY-MM-DD/data.json
        date_str = target_date.strftime("%Y-%m-%d")
        key = f"raw/{entity}/date={date_str}/data.json"

        try:
            # Convert dictionary to JSON bytes
            json_str = json.dumps(data, indent=2)
            json_bytes = json_str.encode("utf-8")

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json_bytes,
                ContentType="application/json",
                Metadata={
                    "entity": entity,
                    "date": date_str,
                    "format": "json",
                },
            )

            logger.info(f"Stored JSON data to s3://{self.bucket_name}/{key}")
            return key

        except Exception as e:
            logger.error(f"Failed to store JSON data to S3: {e}")
            raise

    def check_exists(self, entity: str, target_date: date) -> bool:
        """Check if data already exists for entity and date."""
        date_str = target_date.strftime("%Y-%m-%d")
        prefix = f"raw/{entity}/date={date_str}/"

        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix, MaxKeys=1
            )
            return response.get("KeyCount", 0) > 0
        except Exception as e:
            logger.warning(f"Failed to check if data exists: {e}")
            return False

    def list_entities_for_date(self, target_date: date) -> list[str]:
        """List all entities that have data for the given date."""
        date_str = target_date.strftime("%Y-%m-%d")
        prefix = "raw/"

        entities = []
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix, Delimiter="/"
            )

            for common_prefix in response.get("CommonPrefixes", []):
                entity_prefix = common_prefix["Prefix"]
                # Extract entity name from prefix like "raw/schedule/"
                entity = entity_prefix.replace("raw/", "").rstrip("/")

                # Check if this entity has data for target date
                entity_date_prefix = f"raw/{entity}/date={date_str}/"
                entity_response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name, Prefix=entity_date_prefix, MaxKeys=1
                )

                if entity_response.get("KeyCount", 0) > 0:
                    entities.append(entity)

        except Exception as e:
            logger.error(f"Failed to list entities for date {target_date}: {e}")

        return entities
