"""
S3 storage client for NBA data backfill to Bronze layer.

Implements S3 integration following ADR-014 Parquet storage format
with proper partitioning, metadata, and error handling.
"""

import json
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import boto3
import pyarrow as pa
import pyarrow.parquet as pq
from botocore.exceptions import ClientError, NoCredentialsError
from hoopstat_observability import get_logger

logger = get_logger(__name__)


class S3Client:
    """
    S3 client for Bronze layer data storage.

    Handles upload of Parquet files with proper partitioning,
    metadata embedding, and state management.
    """

    def __init__(self, bucket: str, region: str = "us-east-1"):
        """
        Initialize S3 client.

        Args:
            bucket: S3 bucket name
            region: AWS region
        """
        self.bucket = bucket
        self.region = region

        try:
            self.s3_client = boto3.client("s3", region_name=region)
            # Test connectivity
            self.s3_client.head_bucket(Bucket=bucket)
            logger.info(
                "S3 client initialized successfully",
                bucket=bucket,
                region=region,
            )
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except ClientError as e:
            logger.error(
                "Failed to initialize S3 client",
                bucket=bucket,
                error=str(e),
            )
            raise

    def _generate_s3_key(
        self,
        data_type: str,
        season: str,
        game_date: str,
        game_id: str,
        prefix: str = "historical-backfill",
    ) -> str:
        """
        Generate S3 key following partitioning scheme.

        Args:
            data_type: Type of data (box-scores, play-by-play, etc.)
            season: Season in format YYYY-YY
            game_date: Game date in YYYY-MM-DD format
            game_id: NBA game ID
            prefix: S3 prefix for backfill data

        Returns:
            S3 key path
        """
        # Extract month from game date
        try:
            date_obj = datetime.fromisoformat(game_date)
            month = f"{date_obj.month:02d}"
        except ValueError:
            # Fallback to current month if date parsing fails
            month = f"{datetime.now().month:02d}"

        # Generate timestamp for file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return (
            f"{prefix}/{data_type}/"
            f"season={season}/month={month}/"
            f"{data_type}_{game_id}_{timestamp}.parquet"
        )

    def _create_parquet_table(
        self,
        data: list[dict[str, Any]],
        metadata: dict[str, Any],
    ) -> pa.Table:
        """
        Create PyArrow table from NBA API data with metadata.

        Args:
            data: NBA API response data
            metadata: Metadata to embed in Parquet file

        Returns:
            PyArrow table with embedded metadata
        """
        if not data:
            # Create empty table with basic schema
            schema = pa.schema(
                [
                    pa.field("game_id", pa.string()),
                    pa.field("season", pa.string()),
                    pa.field("ingestion_timestamp", pa.timestamp("us")),
                ]
            )
            table = pa.Table.from_arrays([[], [], []], schema=schema)
        else:
            # Convert data to PyArrow table
            table = pa.Table.from_pylist(data)

        # Add metadata
        metadata_json = json.dumps(metadata)
        schema_with_metadata = table.schema.with_metadata(
            {"nba_backfill_metadata": metadata_json}
        )
        table = table.cast(schema_with_metadata)

        return table

    def upload_game_data(
        self,
        data: list[dict[str, Any]],
        data_type: str,
        game_id: str,
        season: str,
        game_date: str,
        api_response_time: float,
        prefix: str = "historical-backfill",
        dry_run: bool = False,
    ) -> str:
        """
        Upload game data as Parquet file to S3.

        Args:
            data: Game data from NBA API
            data_type: Type of data (box-scores, play-by-play, etc.)
            game_id: NBA game ID
            season: Season in format YYYY-YY
            game_date: Game date in YYYY-MM-DD format
            api_response_time: API response time in seconds
            prefix: S3 prefix for backfill data
            dry_run: If True, skip actual upload

        Returns:
            S3 key of uploaded file
        """
        s3_key = self._generate_s3_key(data_type, season, game_date, game_id, prefix)

        # Prepare metadata
        metadata = {
            "source": "nba-api",
            "data_type": data_type,
            "game_id": game_id,
            "game_date": game_date,
            "season": season,
            "ingestion_timestamp": datetime.now().isoformat() + "Z",
            "api_response_time_ms": round(api_response_time * 1000, 2),
            "row_count": len(data),
            "validation_status": "passed",  # TODO: Add actual validation
            "data_quality_score": 1.0,  # TODO: Add actual scoring
        }

        if dry_run:
            logger.info(
                "Dry run: would upload game data",
                s3_key=s3_key,
                row_count=len(data),
                data_type=data_type,
                game_id=game_id,
            )
            return s3_key

        try:
            # Create PyArrow table
            table = self._create_parquet_table(data, metadata)

            # Convert to bytes
            buffer = pa.BufferOutputStream()
            pq.write_table(
                table,
                buffer,
                compression="snappy",  # Per ADR-014
                use_dictionary=True,
                row_group_size=10000,
            )
            parquet_bytes = buffer.getvalue().to_pybytes()

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=parquet_bytes,
                ContentType="application/octet-stream",
                Metadata={
                    "data-type": data_type,
                    "game-id": game_id,
                    "season": season,
                    "row-count": str(len(data)),
                },
            )

            logger.info(
                "Game data uploaded successfully",
                s3_key=s3_key,
                row_count=len(data),
                data_type=data_type,
                game_id=game_id,
                file_size_bytes=len(parquet_bytes),
            )

            return s3_key

        except Exception as e:
            logger.error(
                "Failed to upload game data",
                s3_key=s3_key,
                data_type=data_type,
                game_id=game_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def upload_state_file(
        self,
        state_data: dict[str, Any],
        state_file_path: str,
        dry_run: bool = False,
    ) -> None:
        """
        Upload checkpoint state file to S3.

        Args:
            state_data: State data dictionary
            state_file_path: S3 path for state file (s3://bucket/key format)
            dry_run: If True, skip actual upload
        """
        # Parse S3 path
        parsed = urlparse(state_file_path)
        if parsed.scheme != "s3":
            raise ValueError(f"Invalid S3 path: {state_file_path}")

        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        if dry_run:
            logger.info(
                "Dry run: would upload state file",
                state_file_path=state_file_path,
                state_size=len(json.dumps(state_data)),
            )
            return

        try:
            # Convert state to JSON
            state_json = json.dumps(state_data, indent=2, default=str)

            # Upload to S3
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=state_json.encode("utf-8"),
                ContentType="application/json",
                Metadata={
                    "content-type": "checkpoint-state",
                    "backfill-id": state_data.get("backfill_id", "unknown"),
                },
            )

            logger.info(
                "State file uploaded successfully",
                state_file_path=state_file_path,
                state_size=len(state_json),
                games_processed=state_data.get("statistics", {}).get(
                    "total_games_processed", 0
                ),
            )

        except Exception as e:
            logger.error(
                "Failed to upload state file",
                state_file_path=state_file_path,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def download_state_file(self, state_file_path: str) -> dict[str, Any] | None:
        """
        Download checkpoint state file from S3.

        Args:
            state_file_path: S3 path for state file (s3://bucket/key format)

        Returns:
            State data dictionary or None if not found
        """
        # Parse S3 path
        parsed = urlparse(state_file_path)
        if parsed.scheme != "s3":
            raise ValueError(f"Invalid S3 path: {state_file_path}")

        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            state_json = response["Body"].read().decode("utf-8")
            state_data = json.loads(state_json)

            logger.info(
                "State file downloaded successfully",
                state_file_path=state_file_path,
                games_processed=state_data.get("statistics", {}).get(
                    "total_games_processed", 0
                ),
            )

            return state_data

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.info(
                    "State file not found",
                    state_file_path=state_file_path,
                )
                return None
            else:
                logger.error(
                    "Failed to download state file",
                    state_file_path=state_file_path,
                    error=str(e),
                )
                raise
        except Exception as e:
            logger.error(
                "Failed to parse state file",
                state_file_path=state_file_path,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
