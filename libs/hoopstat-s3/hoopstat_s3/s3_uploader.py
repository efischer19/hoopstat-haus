"""
S3 upload functionality with proper partitioning for NBA data.
"""

import logging
from datetime import date, datetime
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


class S3UploadError(Exception):
    """Custom exception for S3 upload errors."""

    pass


class S3Uploader:
    """
    S3 uploader with proper date-based partitioning for Bronze layer storage.

    Implements partitioning scheme from bronze-layer-ingestion.md:
    s3://bucket/nba-api/{data_type}/year={year}/month={month}/day={day}/hour={hour}/
    """

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region_name: str = "us-east-1",
    ):
        """
        Initialize the S3 uploader.

        Args:
            bucket_name: S3 bucket name for uploads
            aws_access_key_id: AWS access key (optional, can use IAM roles)
            aws_secret_access_key: AWS secret key (optional, can use IAM roles)
            region_name: AWS region name
        """
        self.bucket_name = bucket_name

        # Initialize S3 client
        session_kwargs = {"region_name": region_name}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs.update(
                {
                    "aws_access_key_id": aws_access_key_id,
                    "aws_secret_access_key": aws_secret_access_key,
                }
            )

        try:
            self.s3_client = boto3.client("s3", **session_kwargs)
            # Test connection
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"Initialized S3 uploader for bucket: {bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise S3UploadError(f"S3 initialization failed: {e}") from e

    def _generate_partition_path(
        self, data_type: str, target_date: date, hour: int | None = None
    ) -> str:
        """
        Generate S3 partition path following Bronze layer structure.

        Args:
            data_type: Type of data (games, players, teams, statistics)
            target_date: Date for partitioning
            hour: Optional hour for partitioning (defaults to current hour)

        Returns:
            S3 key path with partitioning
        """
        if hour is None:
            hour = datetime.now().hour

        path = (
            f"nba-api/{data_type}/"
            f"year={target_date.year}/"
            f"month={target_date.month:02d}/"
            f"day={target_date.day:02d}/"
            f"hour={hour:02d}/"
        )

        return path

    def _upload_to_s3(
        self, data: bytes, s3_key: str, metadata: dict[str, str] | None = None
    ) -> None:
        """
        Upload data to S3 with error handling.

        Args:
            data: Parquet data as bytes
            s3_key: S3 key for the object
            metadata: Optional metadata for the object

        Raises:
            S3UploadError: If upload fails
        """
        try:
            extra_args = {}
            if metadata:
                extra_args["Metadata"] = metadata

            # Set content type for Parquet files
            extra_args["ContentType"] = "application/octet-stream"

            self.s3_client.put_object(
                Bucket=self.bucket_name, Key=s3_key, Body=data, **extra_args
            )

            logger.info(
                f"Successfully uploaded {len(data)} bytes to s3://{self.bucket_name}/{s3_key}"
            )

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise S3UploadError(f"S3 upload failed: {e}") from e
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise S3UploadError(f"S3 upload failed: {e}") from e

    def upload_games(self, parquet_data: bytes, target_date: date) -> str:
        """
        Upload games data to S3 with proper partitioning.

        Args:
            parquet_data: Games data in Parquet format
            target_date: Date the games occurred

        Returns:
            S3 key where data was uploaded

        Raises:
            S3UploadError: If upload fails
        """
        if not parquet_data:
            logger.warning("No games data to upload")
            return ""

        # Generate partition path
        partition_path = self._generate_partition_path("games", target_date)
        timestamp = datetime.now().isoformat().replace(":", "-")
        filename = f"games_{target_date.strftime('%Y%m%d')}_{timestamp}.parquet"
        s3_key = partition_path + filename

        # Add metadata
        metadata = {
            "data_type": "games",
            "target_date": target_date.isoformat(),
            "upload_timestamp": datetime.now().isoformat(),
            "format": "parquet",
        }

        self._upload_to_s3(parquet_data, s3_key, metadata)
        return s3_key

    def upload_box_score(
        self, parquet_data: bytes, game_id: str, target_date: date
    ) -> str:
        """
        Upload box score data to S3 with proper partitioning.

        Args:
            parquet_data: Box score data in Parquet format
            game_id: NBA game ID
            target_date: Date the game occurred

        Returns:
            S3 key where data was uploaded
        """
        if not parquet_data:
            logger.warning("No box score data to upload")
            return ""

        # Generate partition path
        partition_path = self._generate_partition_path("box", target_date)
        timestamp = datetime.now().isoformat().replace(":", "-")
        filename = f"box_score_{game_id}_{timestamp}.parquet"
        s3_key = partition_path + filename

        # Add metadata
        metadata = {
            "data_type": "box",
            "game_id": game_id,
            "target_date": target_date.isoformat(),
            "upload_timestamp": datetime.now().isoformat(),
            "format": "parquet",
        }

        self._upload_to_s3(parquet_data, s3_key, metadata)
        return s3_key

    def upload_player_info(self, parquet_data: bytes, player_id: int) -> str:
        """
        Upload player info to S3 with proper partitioning.

        Args:
            parquet_data: Player info in Parquet format
            player_id: NBA player ID

        Returns:
            S3 key where data was uploaded
        """
        if not parquet_data:
            logger.warning("No player info data to upload")
            return ""

        # Use today's date for partitioning player info
        today = date.today()
        partition_path = self._generate_partition_path("players", today)
        timestamp = datetime.now().isoformat().replace(":", "-")
        filename = f"player_{player_id}_{timestamp}.parquet"
        s3_key = partition_path + filename

        # Add metadata
        metadata = {
            "data_type": "players",
            "player_id": str(player_id),
            "upload_timestamp": datetime.now().isoformat(),
            "format": "parquet",
        }

        self._upload_to_s3(parquet_data, s3_key, metadata)
        return s3_key

    def upload_standings(self, parquet_data: bytes) -> str:
        """
        Upload league standings to S3 with proper partitioning.

        Args:
            parquet_data: Standings data in Parquet format

        Returns:
            S3 key where data was uploaded
        """
        if not parquet_data:
            logger.warning("No standings data to upload")
            return ""

        # Use today's date for partitioning standings
        today = date.today()
        partition_path = self._generate_partition_path("standings", today)
        timestamp = datetime.now().isoformat().replace(":", "-")
        filename = f"standings_{today.strftime('%Y%m%d')}_{timestamp}.parquet"
        s3_key = partition_path + filename

        # Add metadata
        metadata = {
            "data_type": "standings",
            "upload_timestamp": datetime.now().isoformat(),
            "format": "parquet",
        }

        self._upload_to_s3(parquet_data, s3_key, metadata)
        return s3_key

    def list_objects(self, prefix: str, max_keys: int = 1000) -> list[dict[str, Any]]:
        """
        List objects in S3 bucket with given prefix.

        Args:
            prefix: S3 prefix to filter objects
            max_keys: Maximum number of keys to return

        Returns:
            List of object metadata dictionaries
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix, MaxKeys=max_keys
            )

            objects = response.get("Contents", [])
            logger.debug(f"Listed {len(objects)} objects with prefix '{prefix}'")
            return objects

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to list S3 objects: {e}")
            raise S3UploadError(f"S3 list operation failed: {e}") from e
