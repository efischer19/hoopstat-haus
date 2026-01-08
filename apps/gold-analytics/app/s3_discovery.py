"""
S3 data discovery and loading utilities for Gold Analytics.

This module provides utilities for discovering Silver layer data files
and loading them for processing, implementing retry logic per ADR-021.
"""

import re
from datetime import date, datetime
from typing import Any

import boto3
import pandas as pd
from botocore.exceptions import ClientError, NoCredentialsError
from hoopstat_observability import get_logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import GoldAnalyticsConfig

logger = get_logger(__name__)


class S3DataDiscovery:
    """
    Discovers and loads Silver layer data from S3 with retry logic.

    This class implements the data discovery and loading functionality
    with robust error handling and retry mechanisms following ADR-021.
    """

    def __init__(self, config: GoldAnalyticsConfig) -> None:
        """
        Initialize S3 data discovery with configuration.

        Args:
            config: Gold analytics configuration
        """
        self.config = config
        self.s3_client = boto3.client("s3", region_name=config.aws_region)

        logger.info(
            f"Initialized S3DataDiscovery for silver_bucket={config.silver_bucket}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_exception_type((ClientError, NoCredentialsError)),
    )
    def discover_silver_files(
        self, target_date: date, file_type: str = "player_stats"
    ) -> list[dict[str, Any]]:
        """
        Discover Silver layer files for a specific date.

        Args:
            target_date: Date to discover files for
            file_type: Type of file to discover ('player_stats' or 'team_stats')

        Returns:
            List of dictionaries containing file metadata

        Raises:
            ClientError: If S3 operation fails
            ValueError: If invalid file_type provided
        """
        if file_type not in ["player_stats", "team_stats"]:
            raise ValueError(f"Invalid file_type: {file_type}")

        # ADR-032: URL-safe Silver paths only.
        # Example: silver/player-stats/2024-01-15/players.json
        season = self._extract_season_from_date(target_date)
        date_str = target_date.strftime("%Y-%m-%d")

        entity_type = file_type.replace("_", "-")
        prefix = f"silver/{entity_type}/{date_str}/"

        logger.info(
            f"Discovering {file_type} files for {target_date} with prefix: {prefix}"
        )

        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.config.silver_bucket,
                Prefix=prefix,
                MaxKeys=1000,  # Reasonable limit for daily files
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(
                f"Failed to discover files for {target_date}: {error_code} - {e}"
            )
            raise

        files = []
        if response and "Contents" in response:
            for obj in response["Contents"]:
                # Skip directory markers and non-data files
                if obj["Key"].endswith("/") or obj["Size"] == 0:
                    continue

                # Filter for data files (parquet, json, csv)
                if not any(
                    obj["Key"].endswith(ext) for ext in [".parquet", ".json", ".csv"]
                ):
                    continue

                file_info = {
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"],
                    "etag": obj["ETag"].strip('"'),
                    "file_type": file_type,
                    "date": target_date,
                    "season": season,
                }
                files.append(file_info)

        logger.info(f"Discovered {len(files)} {file_type} files for {target_date}")
        return files

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_exception_type(ClientError),
    )
    def load_silver_data(
        self, file_info: dict[str, Any], file_format: str = "auto"
    ) -> pd.DataFrame:
        """
        Load a Silver layer data file from S3.

        Args:
            file_info: File metadata from discover_silver_files
            file_format: Format of the file ('auto', 'parquet', 'json', 'csv')

        Returns:
            DataFrame containing the loaded data

        Raises:
            ClientError: If S3 operation fails
            ValueError: If file format is not supported
        """
        key = file_info["key"]
        logger.info(f"Loading Silver data from s3://{self.config.silver_bucket}/{key}")

        # Auto-detect format if not specified
        if file_format == "auto":
            if key.endswith(".parquet"):
                file_format = "parquet"
            elif key.endswith(".json"):
                file_format = "json"
            elif key.endswith(".csv"):
                file_format = "csv"
            else:
                raise ValueError(f"Cannot auto-detect format for file: {key}")

        try:
            # Download file content
            response = self.s3_client.get_object(
                Bucket=self.config.silver_bucket, Key=key
            )

            file_content = response["Body"].read()

            # Load based on format
            if file_format == "parquet":
                df = pd.read_parquet(file_content)
            elif file_format == "json":
                df = pd.read_json(file_content, lines=True)  # Assume JSON Lines format
            elif file_format == "csv":
                df = pd.read_csv(file_content)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")

            logger.info(f"Loaded {len(df)} records from {key}")
            return df

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"Failed to load file {key}: {error_code} - {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse file {key} as {file_format}: {e}")
            raise

    def load_all_silver_data(self, target_date: date, file_type: str) -> pd.DataFrame:
        """
        Load all Silver layer files for a specific date and type.

        Args:
            target_date: Date to load data for
            file_type: Type of files to load ('player_stats' or 'team_stats')

        Returns:
            Combined DataFrame with all data for the date
        """
        files = self.discover_silver_files(target_date, file_type)

        if not files:
            logger.warning(f"No {file_type} files found for {target_date}")
            return pd.DataFrame()

        # Load and combine all files
        dataframes = []
        for file_info in files:
            try:
                df = self.load_silver_data(file_info)
                if not df.empty:
                    # Add metadata columns
                    df["_source_file"] = file_info["key"]
                    df["_load_timestamp"] = datetime.utcnow()
                    dataframes.append(df)
            except Exception as e:
                logger.error(f"Failed to load file {file_info['key']}: {e}")
                # Continue processing other files
                continue

        if dataframes:
            combined_df = pd.concat(dataframes, ignore_index=True)
            logger.info(
                f"Combined {len(dataframes)} files into {len(combined_df)} records "
                f"for {file_type} on {target_date}"
            )
            return combined_df
        else:
            logger.warning(f"No data loaded for {file_type} on {target_date}")
            return pd.DataFrame()

    def check_data_freshness(
        self, target_date: date, file_type: str, max_age_hours: int = 24
    ) -> bool:
        """
        Check if Silver layer data is fresh enough for processing.

        Args:
            target_date: Date to check data for
            file_type: Type of files to check
            max_age_hours: Maximum age in hours for data to be considered fresh

        Returns:
            True if data is fresh enough, False otherwise
        """
        files = self.discover_silver_files(target_date, file_type)

        if not files:
            logger.warning(
                f"No {file_type} files found for freshness check on {target_date}"
            )
            return False

        now = datetime.utcnow()
        fresh_files = []

        for file_info in files:
            age_hours = (
                now - file_info["last_modified"].replace(tzinfo=None)
            ).total_seconds() / 3600
            if age_hours <= max_age_hours:
                fresh_files.append(file_info)

        is_fresh = len(fresh_files) > 0
        logger.info(
            f"Data freshness check for {file_type} on {target_date}: "
            f"{len(fresh_files)}/{len(files)} files are fresh "
            f"(max_age: {max_age_hours}h)"
        )

        return is_fresh

    def discover_dates_to_process(
        self, start_date: date, end_date: date, file_type: str = "player_stats"
    ) -> list[date]:
        """
        Discover dates that have Silver layer data available for processing.

        Args:
            start_date: Start date for discovery
            end_date: End date for discovery
            file_type: Type of files to check for

        Returns:
            List of dates that have data available
        """
        available_dates = []
        current_date = start_date

        while current_date <= end_date:
            try:
                files = self.discover_silver_files(current_date, file_type)
                if files:
                    available_dates.append(current_date)
            except Exception as e:
                logger.warning(f"Failed to check data for {current_date}: {e}")

            # Move to next day
            current_date = date.fromordinal(current_date.toordinal() + 1)

        logger.info(
            f"Discovered {len(available_dates)} dates with {file_type} data "
            f"between {start_date} and {end_date}"
        )

        return available_dates

    def _extract_season_from_date(self, target_date: date) -> str:
        """
        Extract NBA season string from a date.

        Args:
            target_date: Date to extract season from

        Returns:
            Season string in format "YYYY-YY"
        """
        # NBA season logic: Oct-June
        if target_date.month >= 10:  # Oct, Nov, Dec
            season_start_year = target_date.year
        else:  # Jan-June
            season_start_year = target_date.year - 1

        season_end_year_short = str(season_start_year + 1)[2:]
        return f"{season_start_year}-{season_end_year_short}"


def parse_s3_event_key(s3_key: str) -> dict[str, Any] | None:
    """
    Parse S3 object key to extract metadata for processing.

    Supports multiple patterns:
    1. Silver-ready marker: metadata/{date}/silver-ready.json
    2. Silver data: silver/{file_type}/{date}/filename (ADR-032)

    Args:
        s3_key: S3 object key from event

    Returns:
        Dictionary with parsed metadata or None if parsing fails
    """
    # First, check if this is a silver-ready marker (ADR-028 daily trigger)
    marker_pattern = r"metadata/(?P<date>[\d-]+)/silver-ready\.json"
    match = re.match(marker_pattern, s3_key)
    if match:
        try:
            parsed_date = datetime.strptime(match.group("date"), "%Y-%m-%d").date()
            season = _extract_season_from_date_helper(parsed_date)
            return {
                "file_type": "silver-ready-marker",
                "season": season,
                "date": parsed_date,
                "original_key": s3_key,
                "is_marker": True,
            }
        except ValueError as e:
            logger.error(f"Failed to parse date from marker key {s3_key}: {e}")
            return None

    # ADR-032 format: silver/{file_type}/{date}/filename
    # Handles hyphens in file_type (e.g., player-stats, team-stats)
    pattern_current = r"silver/(?P<file_type>[a-z-]+)/(?P<date>[\d-]+)/.*"

    match = re.match(pattern_current, s3_key)
    if match:
        try:
            parsed_date = datetime.strptime(match.group("date"), "%Y-%m-%d").date()
            season = _extract_season_from_date_helper(parsed_date)
            return {
                "file_type": match.group("file_type"),
                "season": season,
                "date": parsed_date,
                "original_key": s3_key,
                "is_marker": False,
            }
        except ValueError as e:
            logger.error(f"Failed to parse date from S3 key {s3_key}: {e}")
            return None

    logger.warning(f"S3 key does not match any expected pattern: {s3_key}")
    return None


def _extract_season_from_date_helper(target_date: date) -> str:
    """
    Helper function to extract NBA season string from a date.

    Args:
        target_date: Date to extract season from

    Returns:
        Season string in format "YYYY-YY"
    """
    # NBA season logic: Oct-June
    if target_date.month >= 10:  # Oct, Nov, Dec
        season_start_year = target_date.year
    else:  # Jan-June
        season_start_year = target_date.year - 1

    season_end_year_short = str(season_start_year + 1)[2:]
    return f"{season_start_year}-{season_end_year_short}"
