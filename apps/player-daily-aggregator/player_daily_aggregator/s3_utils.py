"""
S3 utilities for reading Silver layer data and writing Gold layer data.

Handles Parquet file operations with proper partitioning.
"""

import io
from typing import Any
from urllib.parse import urlparse

import boto3
import pandas as pd


class S3DataHandler:
    """Handles S3 operations for Silver and Gold layer data."""

    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize S3 client.

        Args:
            region_name: AWS region for S3 operations
        """
        self.s3_client = boto3.client("s3", region_name=region_name)

    def read_silver_layer_data(self, s3_path: str) -> pd.DataFrame:
        """
        Read player game data from Silver layer S3 path.

        Args:
            s3_path: S3 path to Silver layer data

        Returns:
            DataFrame with player game statistics

        Raises:
            Exception: If unable to read data from S3
        """
        try:
            # Parse S3 path
            parsed = urlparse(s3_path)
            bucket = parsed.netloc
            prefix = parsed.path.lstrip("/")

            # List Parquet files in the path
            parquet_files = self._list_parquet_files(bucket, prefix)

            if not parquet_files:
                return pd.DataFrame()

            # Read all Parquet files and concatenate
            dfs = []
            for file_key in parquet_files:
                df = self._read_parquet_file(bucket, file_key)
                if not df.empty:
                    dfs.append(df)

            if not dfs:
                return pd.DataFrame()

            return pd.concat(dfs, ignore_index=True)

        except Exception as e:
            raise Exception(
                f"Failed to read Silver layer data from {s3_path}: {str(e)}"
            )

    def write_gold_layer_data(
        self,
        stats_df: pd.DataFrame,
        base_s3_path: str,
        partition_columns: list[str] = None,
    ) -> list[str]:
        """
        Write aggregated statistics to Gold layer with partitioning.

        Args:
            stats_df: DataFrame with aggregated statistics
            base_s3_path: Base S3 path for Gold layer
            partition_columns: Columns to partition by (default: ['season', 'player_id'])

        Returns:
            List of S3 paths where data was written

        Raises:
            Exception: If unable to write data to S3
        """
        if stats_df.empty:
            return []

        if partition_columns is None:
            partition_columns = ["season", "player_id"]

        try:
            written_paths = []

            # Group by partition columns
            if all(col in stats_df.columns for col in partition_columns):
                grouped = stats_df.groupby(partition_columns)

                for partition_values, group_df in grouped:
                    if not isinstance(partition_values, tuple):
                        partition_values = (partition_values,)

                    # Build partitioned path
                    partition_path = self._build_partition_path(
                        base_s3_path, partition_columns, partition_values
                    )

                    # Write the group data
                    self._write_parquet_file(group_df, partition_path)
                    written_paths.append(partition_path)
            else:
                # Write without partitioning if columns missing
                file_path = f"{base_s3_path.rstrip('/')}/daily_stats.parquet"
                self._write_parquet_file(stats_df, file_path)
                written_paths.append(file_path)

            return written_paths

        except Exception as e:
            raise Exception(
                f"Failed to write Gold layer data to {base_s3_path}: {str(e)}"
            )

    def read_existing_season_data(
        self, player_id: str, season: str, base_s3_path: str
    ) -> pd.DataFrame:
        """
        Read existing season-to-date data for a specific player.

        Args:
            player_id: Player identifier
            season: Season identifier
            base_s3_path: Base Gold layer S3 path

        Returns:
            DataFrame with existing season data or empty DataFrame
        """
        try:
            season_path = f"{base_s3_path}/season={season}/player_id={player_id}/season_stats.parquet"

            parsed = urlparse(season_path)
            bucket = parsed.netloc
            file_key = parsed.path.lstrip("/")

            return self._read_parquet_file(bucket, file_key)

        except Exception:
            # Return empty DataFrame if file doesn't exist
            return pd.DataFrame()

    def _list_parquet_files(self, bucket: str, prefix: str) -> list[str]:
        """List all Parquet files under the given S3 prefix."""
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)

            parquet_files = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    if obj["Key"].endswith(".parquet"):
                        parquet_files.append(obj["Key"])

            return parquet_files

        except Exception as e:
            raise Exception(f"Failed to list files in s3://{bucket}/{prefix}: {str(e)}")

    def _read_parquet_file(self, bucket: str, file_key: str) -> pd.DataFrame:
        """Read a single Parquet file from S3."""
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=file_key)
            parquet_buffer = io.BytesIO(response["Body"].read())
            return pd.read_parquet(parquet_buffer)

        except Exception as e:
            raise Exception(f"Failed to read s3://{bucket}/{file_key}: {str(e)}")

    def _write_parquet_file(self, df: pd.DataFrame, s3_path: str) -> None:
        """Write DataFrame to S3 as Parquet file."""
        parsed = urlparse(s3_path)
        bucket = parsed.netloc
        file_key = parsed.path.lstrip("/")

        # Convert DataFrame to Parquet in memory
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False, engine="pyarrow")
        parquet_buffer.seek(0)

        # Upload to S3
        self.s3_client.put_object(
            Bucket=bucket,
            Key=file_key,
            Body=parquet_buffer.getvalue(),
            ContentType="application/octet-stream",
        )

    def _build_partition_path(
        self, base_path: str, partition_columns: list[str], partition_values: tuple
    ) -> str:
        """Build partitioned S3 path."""
        path_parts = [base_path.rstrip("/")]

        for col, value in zip(partition_columns, partition_values, strict=False):
            path_parts.append(f"{col}={value}")

        # Add filename
        if len(partition_columns) > 1 and partition_columns[-1] == "player_id":
            path_parts.append("daily_stats.parquet")
        else:
            path_parts.append("daily_stats.parquet")

        return "/".join(path_parts)


def extract_s3_info_from_event(event: dict[str, Any]) -> dict[str, str]:
    """
    Extract S3 bucket and key information from Lambda event.

    Args:
        event: Lambda event from S3 trigger

    Returns:
        Dictionary with bucket, key, season, and date information
    """
    try:
        # Get S3 event record
        s3_record = event["Records"][0]["s3"]
        bucket = s3_record["bucket"]["name"]
        key = s3_record["object"]["key"]

        # Parse key to extract season and date
        # Expected format: player_games/season=2023-24/date=2024-01-15/file.parquet
        key_parts = key.split("/")

        season = None
        date = None

        for part in key_parts:
            if part.startswith("season="):
                season = part.split("=")[1]
            elif part.startswith("date="):
                date = part.split("=")[1]

        return {
            "bucket": bucket,
            "key": key,
            "season": season,
            "date": date,
            "silver_path": f"s3://{bucket}/{'/'.join(key_parts[:-1])}",  # Path without filename
        }

    except (KeyError, IndexError) as e:
        raise Exception(f"Invalid S3 event format: {str(e)}")
