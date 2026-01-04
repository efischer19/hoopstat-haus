"""
Silver S3 Manager for reading Bronze and writing Silver JSON data.

This module implements S3 integration that reads Bronze layer JSON data and
writes transformed Silver layer JSON data following the established partitioning
strategy from ADR-020 and JSON storage format from ADR-025.
"""

import json
import logging
from datetime import date, datetime
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from .s3_uploader import S3Uploader, S3UploadError

logger = logging.getLogger(__name__)


class SilverS3ManagerError(Exception):
    """Custom exception for Silver S3 Manager errors."""

    pass


class SilverS3Manager(S3Uploader):
    """
    Silver S3 Manager for Bronze-to-Silver data processing.

    Extends the base S3Uploader to support:
    - Reading Bronze layer JSON data from paths: raw/{entity}/YYYY-MM-DD/data.json
    - Writing Silver layer JSON data to paths: silver/{entity_type}/YYYY-MM-DD/
    - Partitioned Silver storage for player_stats, team_stats, game_stats
    - S3 event handling for Lambda triggers
    - Idempotency checks
    - Proper metadata tagging
    """

    def __init__(
        self,
        bucket_name: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region_name: str = "us-east-1",
        bronze_bucket: str | None = None,
        silver_bucket: str | None = None,
    ):
        """
        Initialize the Silver S3 Manager.

        Args:
            bucket_name: S3 bucket name for uploads/downloads (deprecated, use
                bronze_bucket and silver_bucket instead for clarity)
            aws_access_key_id: AWS access key (optional, can use IAM roles)
            aws_secret_access_key: AWS secret key (optional, can use IAM roles)
            region_name: AWS region name
            bronze_bucket: S3 bucket name for reading Bronze data
            silver_bucket: S3 bucket name for writing Silver data
        """
        # Store region_name for our own use
        self.region_name = region_name

        # Determine which buckets to use
        # Priority: explicit bronze_bucket/silver_bucket > bucket_name
        # (for backward compatibility)
        if bronze_bucket or silver_bucket:
            self.bronze_bucket = bronze_bucket
            self.silver_bucket = silver_bucket
            # Use silver_bucket for the parent S3Uploader (for writing)
            write_bucket = silver_bucket or bucket_name
        else:
            # Backward compatibility: use bucket_name for both read and write
            self.bronze_bucket = bucket_name
            self.silver_bucket = bucket_name
            write_bucket = bucket_name

        if not write_bucket:
            raise ValueError("Must provide bucket_name or silver_bucket")

        # Initialize the parent S3Uploader with the write bucket
        super().__init__(
            write_bucket, aws_access_key_id, aws_secret_access_key, region_name
        )

        if self.bronze_bucket == self.silver_bucket:
            logger.info(f"Initialized Silver S3 Manager for bucket: {write_bucket}")
        else:
            logger.info(
                f"Initialized Silver S3 Manager - Bronze: {self.bronze_bucket}, "
                f"Silver: {self.silver_bucket}"
            )

    def read_bronze_json(self, entity: str, target_date: date) -> dict[str, Any] | None:
        """
        Read Bronze JSON data from S3.

        Args:
            entity: Entity type (e.g., 'box')
            target_date: Date of the data

        Returns:
            Parsed JSON data or None if not found

        Raises:
            SilverS3ManagerError: If read operation fails
        """
        date_str = target_date.strftime("%Y-%m-%d")
        key = f"raw/{entity}/{date_str}/data.json"

        try:
            response = self.s3_client.get_object(Bucket=self.bronze_bucket, Key=key)
            json_content = response["Body"].read().decode("utf-8")
            data = json.loads(json_content)

            logger.info(
                f"Successfully read Bronze data from s3://{self.bronze_bucket}/{key}"
            )
            return data

        except self.s3_client.exceptions.NoSuchKey:
            logger.warning(f"Bronze data not found: s3://{self.bronze_bucket}/{key}")
            return None

        except (BotoCoreError, ClientError, json.JSONDecodeError) as e:
            logger.error(
                f"Failed to read Bronze data from s3://{self.bronze_bucket}/{key}: {e}"
            )
            raise SilverS3ManagerError(f"Bronze data read failed: {e}") from e

    def write_silver_json(
        self,
        entity_type: str,
        data: dict[str, Any],
        target_date: date,
        check_exists: bool = True,
    ) -> str:
        """
        Write Silver JSON data to S3 with proper partitioning.

        Args:
            entity_type: Type of entity (player-stats, team-stats, game-stats)
            data: Silver layer data to write
            target_date: Date for partitioning
            check_exists: Whether to check for existing data (idempotency)

        Returns:
            S3 key where data was written

        Raises:
            SilverS3ManagerError: If write operation fails
        """
        date_str = target_date.strftime("%Y-%m-%d")

        # Generate Silver partition path (ADR-032: URL-safe characters only)
        partition_path = f"silver/{entity_type}/{date_str}/"

        # Determine filename based on entity type
        if entity_type == "player-stats":
            filename = "players.json"
        elif entity_type == "team-stats":
            filename = "teams.json"
        elif entity_type == "game-stats":
            filename = "games.json"
        else:
            filename = f"{entity_type}.json"

        s3_key = partition_path + filename

        # Idempotency check
        if check_exists and self._silver_data_exists(s3_key):
            logger.info(
                f"Silver data already exists at "
                f"s3://{self.bucket_name}/{s3_key}, skipping"
            )
            return s3_key

        try:
            # Convert data to JSON bytes
            json_data = json.dumps(data, indent=2, default=str).encode("utf-8")

            # Add metadata for Silver layer
            metadata = {
                "data_layer": "silver",
                "entity_type": entity_type,
                "target_date": target_date.isoformat(),
                "upload_timestamp": datetime.now().isoformat(),
                "format": "json",
                "transformation_stage": "silver",
                "record_count": str(len(data) if isinstance(data, list) else 1),
            }

            # Upload to S3
            self._upload_to_s3(json_data, s3_key, metadata)

            logger.info(
                f"Successfully wrote Silver data to s3://{self.bucket_name}/{s3_key} "
                f"({len(json_data)} bytes)"
            )

            return s3_key

        except Exception as e:
            logger.error(
                f"Failed to write Silver data to s3://{self.bucket_name}/{s3_key}: {e}"
            )
            raise SilverS3ManagerError(f"Silver data write failed: {e}") from e

    def write_partitioned_silver_data(
        self,
        silver_data: dict[str, list[dict[str, Any]]],
        target_date: date,
        check_exists: bool = True,
    ) -> dict[str, str]:
        """
        Write partitioned Silver data for all entity types.

        Args:
            silver_data: Dictionary containing lists of Silver model data
                organized by type
            target_date: Date for partitioning
            check_exists: Whether to check for existing data (idempotency)

        Returns:
            Dictionary mapping entity_type to S3 key where data was written

        Raises:
            SilverS3ManagerError: If any write operation fails
        """
        results = {}

        for entity_type, data_list in silver_data.items():
            if data_list:  # Only write non-empty data
                try:
                    s3_key = self.write_silver_json(
                        entity_type, data_list, target_date, check_exists
                    )
                    results[entity_type] = s3_key

                except Exception as e:
                    logger.error(f"Failed to write {entity_type} data: {e}")
                    raise SilverS3ManagerError(
                        f"Failed to write {entity_type}: {e}"
                    ) from e
            else:
                logger.info(f"No data to write for {entity_type}")

        return results

    def _silver_data_exists(self, s3_key: str) -> bool:
        """
        Check if Silver data already exists at the given S3 key.

        Args:
            s3_key: S3 key to check

        Returns:
            True if object exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except self.s3_client.exceptions.NoSuchKey:
            return False
        except Exception as e:
            logger.warning(f"Error checking if S3 object exists {s3_key}: {e}")
            return False

    def _upload_to_s3(
        self, data: bytes, s3_key: str, metadata: dict[str, str] | None = None
    ) -> None:
        """
        Upload JSON data to S3 with error handling.

        Overrides parent method to set proper content type for JSON.

        Args:
            data: JSON data as bytes
            s3_key: S3 key for the object
            metadata: Optional metadata for the object

        Raises:
            S3UploadError: If upload fails
        """
        try:
            extra_args = {}
            if metadata:
                extra_args["Metadata"] = metadata

            # Set content type for JSON files
            extra_args["ContentType"] = "application/json"

            self.s3_client.put_object(
                Bucket=self.bucket_name, Key=s3_key, Body=data, **extra_args
            )

            logger.info(
                f"Successfully uploaded {len(data)} bytes to "
                f"s3://{self.bucket_name}/{s3_key}"
            )

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise S3UploadError(f"S3 upload failed: {e}") from e
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise S3UploadError(f"S3 upload failed: {e}") from e

    def read_summary_json(self) -> dict[str, Any] | None:
        """
        Read the Bronze layer summary.json file from S3.

        This method reads the summary metadata file that contains information
        about the last bronze ingestion, including the date that was processed.

        Returns:
            Parsed summary JSON data, or None if the file doesn't exist

        Raises:
            SilverS3ManagerError: If read operation fails for reasons other
                than file not found
        """
        key = "_metadata/summary.json"

        try:
            response = self.s3_client.get_object(Bucket=self.bronze_bucket, Key=key)
            json_content = response["Body"].read().decode("utf-8")
            data = json.loads(json_content)

            logger.info(
                f"Successfully read summary from s3://{self.bronze_bucket}/{key}"
            )
            return data

        except self.s3_client.exceptions.NoSuchKey:
            logger.warning(f"Summary file not found: s3://{self.bronze_bucket}/{key}")
            return None

        except (BotoCoreError, ClientError, json.JSONDecodeError) as e:
            logger.error(
                f"Failed to read summary from s3://{self.bronze_bucket}/{key}: {e}"
            )
            raise SilverS3ManagerError(f"Summary read failed: {e}") from e

    def parse_s3_event(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """
        DEPRECATED: Parse S3 event records from Lambda event for Bronze data triggers.

        This method is deprecated and will be removed in a future version.
        Use read_summary_json() instead to get the last ingestion date from
        the Bronze layer summary file.

        Args:
            event: Lambda event containing S3 records

        Returns:
            List of parsed Bronze data events that should trigger Silver processing
        """
        logger.warning("parse_s3_event is deprecated. Use read_summary_json() instead.")
        try:
            records = event.get("Records", [])
            bronze_events = []

            for record in records:
                if record.get("eventSource") == "aws:s3":
                    s3_info = record.get("s3", {})
                    bucket = s3_info.get("bucket", {}).get("name")
                    key = s3_info.get("object", {}).get("key", "")

                    # Check if this is a Bronze layer event we should process
                    if self._is_bronze_trigger_event(key):
                        # Extract entity and date from key
                        entity_info = self._extract_entity_info_from_key(key)
                        if entity_info:
                            bronze_events.append(
                                {
                                    "bucket": bucket,
                                    "key": key,
                                    "entity": entity_info["entity"],
                                    "date": entity_info["date"],
                                    "original_record": record,
                                }
                            )

            logger.info(f"Found {len(bronze_events)} Bronze trigger events")
            return bronze_events

        except Exception as e:
            logger.error(f"Failed to parse S3 events: {e}")
            return []

    def _is_bronze_trigger_event(self, s3_key: str) -> bool:
        """
        Check if S3 key represents a Bronze layer event that should
        trigger Silver processing.

        Args:
            s3_key: S3 object key

        Returns:
            True if this is a Bronze trigger event
        """
        # Check for Bronze layer pattern: raw/{entity}/YYYY-MM-DD/*.json
        # ADR-032: No longer using 'date=' prefix
        import re

        # Pattern: raw/{entity}/{YYYY-MM-DD}/*.json
        pattern = r"^raw/[^/]+/\d{4}-\d{2}-\d{2}/.*\.json$"
        return bool(re.match(pattern, s3_key))

    def _extract_entity_info_from_key(self, s3_key: str) -> dict[str, Any] | None:
        """
        Extract entity and date information from Bronze S3 key.

        Args:
            s3_key: S3 key like 'raw/box/2024-01-15/data.json'

        Returns:
            Dictionary with entity and date info, or None if parsing fails
        """
        try:
            # Parse: raw/{entity}/{YYYY-MM-DD}/*.json (ADR-032: no 'date=' prefix)
            parts = s3_key.split("/")
            if len(parts) >= 4 and parts[0] == "raw" and parts[-1].endswith(".json"):
                entity = parts[1]
                date_str = parts[2]

                # Validate date format YYYY-MM-DD
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                return {"entity": entity, "date": target_date, "date_str": date_str}

        except Exception as e:
            logger.warning(f"Failed to extract entity info from key {s3_key}: {e}")

        return None

    def list_bronze_data(
        self,
        entity: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """
        List available Bronze data for an entity within a date range.

        Args:
            entity: Entity type (e.g., 'box_scores')
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)

        Returns:
            List of dictionaries with Bronze data information
        """
        try:
            prefix = f"raw/{entity}/"
            # List objects from Bronze bucket
            response = self.s3_client.list_objects_v2(
                Bucket=self.bronze_bucket, Prefix=prefix, MaxKeys=1000
            )
            objects = response.get("Contents", [])

            bronze_data = []
            for obj in objects:
                key = obj.get("Key", "")
                entity_info = self._extract_entity_info_from_key(key)

                if entity_info:
                    target_date = entity_info["date"]

                    # Apply date filtering if specified
                    if start_date and target_date < start_date:
                        continue
                    if end_date and target_date > end_date:
                        continue

                    bronze_data.append(
                        {
                            "key": key,
                            "entity": entity_info["entity"],
                            "date": target_date,
                            "size": obj.get("Size", 0),
                            "last_modified": obj.get("LastModified"),
                        }
                    )

            # Sort by date
            bronze_data.sort(key=lambda x: x["date"])

            logger.info(f"Found {len(bronze_data)} Bronze data objects for {entity}")
            return bronze_data

        except Exception as e:
            logger.error(f"Failed to list Bronze data for {entity}: {e}")
            raise SilverS3ManagerError(f"Bronze data listing failed: {e}") from e

    def list_silver_data(
        self,
        entity_type: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """
        List available Silver data for an entity type within a date range.

        Args:
            entity_type: Entity type (player_stats, team_stats, game_stats)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)

        Returns:
            List of dictionaries with Silver data information
        """
        try:
            prefix = f"silver/{entity_type}/"
            objects = self.list_objects(prefix)

            silver_data = []
            for obj in objects:
                key = obj.get("Key", "")

                # Extract date from silver path:
                # silver/{entity_type}/{YYYY-MM-DD}/{filename}
                # ADR-032: No longer using 'date=' prefix
                if len(key.split("/")) >= 4:
                    try:
                        # Get third segment which should be the date
                        date_str = key.split("/")[2]
                        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                        # Apply date filtering if specified
                        if start_date and target_date < start_date:
                            continue
                        if end_date and target_date > end_date:
                            continue

                        silver_data.append(
                            {
                                "key": key,
                                "entity_type": entity_type,
                                "date": target_date,
                                "size": obj.get("Size", 0),
                                "last_modified": obj.get("LastModified"),
                            }
                        )

                    except ValueError:
                        # Skip objects with invalid date format
                        continue

            # Sort by date
            silver_data.sort(key=lambda x: x["date"])

            logger.info(
                f"Found {len(silver_data)} Silver data objects for {entity_type}"
            )
            return silver_data

        except Exception as e:
            logger.error(f"Failed to list Silver data for {entity_type}: {e}")
            raise SilverS3ManagerError(f"Silver data listing failed: {e}") from e
