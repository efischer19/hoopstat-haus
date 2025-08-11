"""S3 storage client for bronze layer Parquet data."""

from io import BytesIO

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from botocore.exceptions import ClientError, NoCredentialsError
from hoopstat_observability import get_logger

from .config import BronzeIngestionConfig

logger = get_logger(__name__)


class S3ParquetClient:
    """S3 client for storing bronze layer data in Parquet format."""

    def __init__(self, config: BronzeIngestionConfig):
        """Initialize the S3 client.

        Args:
            config: Configuration object with S3 settings
        """
        self.config = config

        # Initialize S3 client
        try:
            self.s3_client = boto3.client("s3", region_name=config.aws_region)
            # Test connection
            self.s3_client.head_bucket(Bucket=config.bronze_bucket_name)
            logger.info(f"Connected to S3 bucket: {config.bronze_bucket_name}")
        except NoCredentialsError:
            raise ValueError(
                "AWS credentials not found. Please configure AWS credentials."
            ) from None
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                raise ValueError(
                    f"S3 bucket not found: {config.bronze_bucket_name}"
                ) from e
            elif error_code == "403":
                raise ValueError(
                    f"Access denied to S3 bucket: {config.bronze_bucket_name}"
                ) from e
            else:
                raise ValueError(f"Error accessing S3 bucket: {e}") from e

    def _build_s3_key(self, entity: str, date: str) -> str:
        """Build S3 key following the bronze layer structure.

        Args:
            entity: Data entity name (e.g., 'schedule', 'box_score', 'play_by_play')
            date: Date in YYYY-MM-DD format

        Returns:
            S3 key following pattern: raw/<entity>/date=YYYY-MM-DD/data.parquet
        """
        return f"raw/{entity}/date={date}/data.parquet"

    def write_parquet(
        self, dataframe: pd.DataFrame, entity: str, date: str, overwrite: bool = True
    ) -> str:
        """Write DataFrame to S3 as Parquet file.

        Args:
            dataframe: Data to write
            entity: Data entity name
            date: Date in YYYY-MM-DD format
            overwrite: Whether to overwrite existing files

        Returns:
            S3 URI of the written file

        Raises:
            ValueError: If write fails
        """
        if dataframe.empty:
            logger.warning(f"Empty dataframe for {entity} on {date}, skipping write")
            return ""

        s3_key = self._build_s3_key(entity, date)
        s3_uri = f"s3://{self.config.bronze_bucket_name}/{s3_key}"

        # Check if file exists when overwrite is False
        if not overwrite:
            try:
                self.s3_client.head_object(
                    Bucket=self.config.bronze_bucket_name, Key=s3_key
                )
                logger.info(f"File already exists and overwrite=False: {s3_uri}")
                return s3_uri
            except ClientError as e:
                if e.response["Error"]["Code"] != "404":
                    logger.error(f"Error checking file existence: {e}")
                    raise ValueError(f"Failed to check if file exists: {e}") from e
                # File doesn't exist, continue with write

        try:
            # Convert DataFrame to Parquet in memory
            buffer = BytesIO()
            table = pa.Table.from_pandas(dataframe)
            pq.write_table(table, buffer)
            buffer.seek(0)

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.config.bronze_bucket_name,
                Key=s3_key,
                Body=buffer.getvalue(),
                ContentType="application/octet-stream",
            )

            logger.info(
                f"Successfully wrote {entity} data to S3",
                extra={
                    "s3_uri": s3_uri,
                    "entity": entity,
                    "date": date,
                    "records_count": len(dataframe),
                    "file_size_bytes": len(buffer.getvalue()),
                },
            )

            return s3_uri

        except Exception as e:
            logger.error(f"Failed to write {entity} data to S3: {e}")
            raise ValueError(f"S3 write failed: {e}") from e

    def file_exists(self, entity: str, date: str) -> bool:
        """Check if a Parquet file exists for the given entity and date.

        Args:
            entity: Data entity name
            date: Date in YYYY-MM-DD format

        Returns:
            True if file exists, False otherwise
        """
        s3_key = self._build_s3_key(entity, date)

        try:
            self.s3_client.head_object(
                Bucket=self.config.bronze_bucket_name, Key=s3_key
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                logger.error(f"Error checking file existence: {e}")
                raise ValueError(f"Failed to check if file exists: {e}") from e

    def read_parquet(self, entity: str, date: str) -> pd.DataFrame | None:
        """Read Parquet file from S3.

        Args:
            entity: Data entity name
            date: Date in YYYY-MM-DD format

        Returns:
            DataFrame with the data, or None if file doesn't exist
        """
        s3_key = self._build_s3_key(entity, date)

        try:
            response = self.s3_client.get_object(
                Bucket=self.config.bronze_bucket_name, Key=s3_key
            )

            # Read Parquet from S3 response
            buffer = BytesIO(response["Body"].read())
            table = pq.read_table(buffer)
            dataframe = table.to_pandas()

            logger.debug(f"Read {len(dataframe)} records from {entity} for {date}")

            return dataframe

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.debug(f"File not found: {s3_key}")
                return None
            else:
                logger.error(f"Error reading file from S3: {e}")
                raise ValueError(f"S3 read failed: {e}") from e
