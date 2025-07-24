"""S3 storage client for NBA data with Parquet format support."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from io import BytesIO
from typing import Any

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from botocore.exceptions import ClientError, NoCredentialsError

from .config import BackfillConfig


class S3StorageClient:
    """S3 client for storing NBA data in Parquet format."""

    def __init__(self, config: BackfillConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize S3 client
        try:
            self.s3_client = boto3.client("s3", region_name=config.aws_region)
            # Test connection
            self.s3_client.head_bucket(Bucket=config.s3_bucket_name)
            self.logger.info(f"Connected to S3 bucket: {config.s3_bucket_name}")
        except NoCredentialsError:
            raise ValueError(
                "AWS credentials not found. Please configure AWS credentials."
            ) from None
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                raise ValueError(f"S3 bucket not found: {config.s3_bucket_name}") from e
            elif error_code == "403":
                raise ValueError(
                    f"Access denied to S3 bucket: {config.s3_bucket_name}"
                ) from e
            else:
                raise ValueError(f"Error accessing S3 bucket: {e}") from e

        # Storage statistics
        self.stats = {
            "files_uploaded": 0,
            "total_bytes_uploaded": 0,
            "upload_failures": 0,
            "total_upload_time": 0.0,
        }

    def _generate_file_path(
        self, data_type: str, game_id: str, season: str, game_date: datetime
    ) -> str:
        """Generate S3 file path following the partitioning strategy."""
        month = f"{game_date.month:02d}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{data_type}_{game_id}_{timestamp}.parquet"

        return f"{self.config.s3_data_prefix}/{data_type}/month={month}/{filename}"

    def _add_metadata_to_dataframe(
        self, df: pd.DataFrame, metadata: dict[str, Any]
    ) -> pd.DataFrame:
        """Add metadata columns to DataFrame."""
        df = df.copy()

        # Add metadata as columns
        for key, value in metadata.items():
            df[f"_meta_{key}"] = value

        return df

    def _upload_file_to_s3(
        self, data: bytes, s3_key: str, metadata: dict[str, str]
    ) -> bool:
        """Upload file to S3 with metadata."""
        try:
            start_time = datetime.now()

            self.s3_client.put_object(
                Bucket=self.config.s3_bucket_name,
                Key=s3_key,
                Body=data,
                Metadata=metadata,
                ContentType="application/octet-stream",
            )

            upload_time = (datetime.now() - start_time).total_seconds()
            self.stats["files_uploaded"] += 1
            self.stats["total_bytes_uploaded"] += len(data)
            self.stats["total_upload_time"] += upload_time

            self.logger.debug(
                "File uploaded successfully",
                extra={
                    "s3_key": s3_key,
                    "file_size_bytes": len(data),
                    "upload_time_seconds": upload_time,
                },
            )

            return True

        except Exception as e:
            self.stats["upload_failures"] += 1
            self.logger.error(
                "Failed to upload file to S3",
                extra={"s3_key": s3_key, "error": str(e)},
            )
            return False

    def store_game_data(
        self,
        data_type: str,
        game_id: str,
        season: str,
        game_date: datetime,
        dataframes: list[pd.DataFrame],
        api_metadata: dict[str, Any],
    ) -> bool:
        """Store game data in S3 as Parquet files."""
        if self.config.dry_run:
            self.logger.info(
                f"DRY RUN: Would store {data_type} for game {game_id}",
                extra={
                    "data_type": data_type,
                    "game_id": game_id,
                    "num_dataframes": len(dataframes),
                },
            )
            return True

        success = True

        for i, df in enumerate(dataframes):
            if df.empty:
                self.logger.warning(
                    f"Empty DataFrame for {data_type} game {game_id}, table {i}"
                )
                continue

            try:
                # Generate file path
                s3_key = self._generate_file_path(data_type, game_id, season, game_date)
                if len(dataframes) > 1:
                    s3_key = s3_key.replace(".parquet", f"_table_{i}.parquet")

                # Add metadata to DataFrame
                extended_metadata = {
                    **api_metadata,
                    "table_index": i,
                    "total_tables": len(dataframes),
                    "row_count": len(df),
                    "column_count": len(df.columns),
                }

                df_with_metadata = self._add_metadata_to_dataframe(
                    df, extended_metadata
                )

                # Convert to Parquet with Snappy compression
                buffer = BytesIO()
                table = pa.Table.from_pandas(df_with_metadata)

                pq.write_table(
                    table,
                    buffer,
                    compression="snappy",
                    use_dictionary=True,
                    row_group_size=10000,
                )

                # Prepare S3 metadata
                s3_metadata = {
                    "source": "nba-api",
                    "endpoint": api_metadata.get("endpoint", "unknown"),
                    "game_id": game_id,
                    "game_date": game_date.isoformat(),
                    "season": season,
                    "data_type": data_type,
                    "ingestion_timestamp": datetime.now().isoformat(),
                    "table_index": str(i),
                    "row_count": str(len(df)),
                    "column_count": str(len(df.columns)),
                }

                # Upload to S3
                if not self._upload_file_to_s3(buffer.getvalue(), s3_key, s3_metadata):
                    success = False

            except Exception as e:
                self.logger.error(
                    f"Error processing DataFrame {i} for {data_type} game {game_id}",
                    extra={"error": str(e)},
                )
                success = False

        return success

    def store_state_file(self, state_data: dict[str, Any]) -> bool:
        """Store checkpoint state file in S3."""
        try:
            state_json = json.dumps(state_data, indent=2, default=str)

            if self.config.dry_run:
                self.logger.info("DRY RUN: Would store state file")
                return True

            # Create backup of current state if it exists
            current_state_key = self.config.state_file_path
            backup_state_key = f"{self.config.state_file_prefix}/checkpoint_backup.json"

            try:
                # Copy current state to backup
                self.s3_client.copy_object(
                    Bucket=self.config.s3_bucket_name,
                    CopySource={
                        "Bucket": self.config.s3_bucket_name,
                        "Key": current_state_key,
                    },
                    Key=backup_state_key,
                )
            except ClientError as e:
                if e.response["Error"]["Code"] != "NoSuchKey":
                    self.logger.warning(f"Could not backup current state: {e}")

            # Upload new state
            self.s3_client.put_object(
                Bucket=self.config.s3_bucket_name,
                Key=current_state_key,
                Body=state_json.encode("utf-8"),
                ContentType="application/json",
                Metadata={
                    "backup_timestamp": datetime.now().isoformat(),
                    "state_version": "1.0",
                },
            )

            self.logger.info("State file stored successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to store state file: {e}")
            return False

    def load_state_file(self) -> dict[str, Any] | None:
        """Load checkpoint state file from S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.config.s3_bucket_name, Key=self.config.state_file_path
            )

            state_data = json.loads(response["Body"].read().decode("utf-8"))
            self.logger.info("State file loaded successfully")
            return state_data

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                self.logger.info("No existing state file found")
                return None
            else:
                self.logger.error(f"Error loading state file: {e}")
                return None
        except Exception as e:
            self.logger.error(f"Error parsing state file: {e}")
            return None

    def upload_files_concurrent(
        self, upload_tasks: list[dict[str, Any]], max_workers: int = 3
    ) -> list[bool]:
        """Upload multiple files concurrently."""
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all upload tasks
            future_to_task = {
                executor.submit(
                    self._upload_file_to_s3,
                    task["data"],
                    task["s3_key"],
                    task["metadata"],
                ): task
                for task in upload_tasks
            }

            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        "Concurrent upload failed",
                        extra={
                            "s3_key": task.get("s3_key", "unknown"),
                            "error": str(e),
                        },
                    )
                    results.append(False)

        return results

    def get_storage_stats(self) -> dict[str, Any]:
        """Get storage operation statistics."""
        avg_upload_time = self.stats["total_upload_time"] / max(
            self.stats["files_uploaded"], 1
        )

        return {
            "files_uploaded": self.stats["files_uploaded"],
            "total_bytes_uploaded": self.stats["total_bytes_uploaded"],
            "upload_failures": self.stats["upload_failures"],
            "success_rate": (
                self.stats["files_uploaded"]
                / max(self.stats["files_uploaded"] + self.stats["upload_failures"], 1)
            ),
            "average_upload_time_seconds": avg_upload_time,
            "total_upload_time_seconds": self.stats["total_upload_time"],
        }
