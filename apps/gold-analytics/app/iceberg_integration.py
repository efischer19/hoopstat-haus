"""
Apache Iceberg integration for S3 Tables Gold layer storage.

This module provides utilities for writing NBA analytics data to S3 Tables
using the Apache Iceberg format with optimized partitioning and file sizes.
"""

from datetime import date
from typing import Any

import pandas as pd
import pyarrow as pa
from hoopstat_observability import get_logger
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NoSuchTableError

logger = get_logger(__name__)


class IcebergS3TablesWriter:
    """
    Writer for Apache Iceberg tables in S3 Tables.

    Handles optimized writes with proper partitioning strategy per ADR-026:
    - Partitioning: season (year), month (1-12), team_id
    - File sizes: Target 64-128MB for query performance
    - Schema evolution: Support for future analytics additions
    - Transaction support: Data consistency through Iceberg
    """

    # Target file sizes for optimal Lambda and query performance
    TARGET_FILE_SIZE_MB = 96  # Middle of 64-128MB range
    MAX_ROWS_PER_FILE = 50000  # Estimated based on analytics row size

    def __init__(self, gold_bucket: str, aws_region: str = "us-east-1") -> None:
        """
        Initialize the Iceberg writer for S3 Tables.

        Args:
            gold_bucket: S3 Tables bucket name for Gold layer
            aws_region: AWS region for S3 Tables
        """
        self.gold_bucket = gold_bucket
        self.aws_region = aws_region

        # Configure catalog for S3 Tables
        self.catalog = self._configure_catalog()
        logger.info(f"Initialized Iceberg writer for bucket: {gold_bucket}")

    def _configure_catalog(self) -> Any:
        """
        Configure PyIceberg catalog for S3 Tables access.

        Returns:
            Configured PyIceberg catalog
        """
        try:
            # S3 Tables catalog configuration
            catalog_config = {
                "type": "glue",  # S3 Tables uses Glue for metadata
                "warehouse": f"s3://{self.gold_bucket}/",
                "region": self.aws_region,
            }

            return load_catalog("s3tables", **catalog_config)
        except Exception as e:
            logger.error(f"Failed to configure Iceberg catalog: {e}")
            raise

    def write_player_analytics(
        self, analytics_df: pd.DataFrame, target_date: date, season: str
    ) -> bool:
        """
        Write player analytics to the player_analytics Iceberg table.

        Args:
            analytics_df: Player analytics DataFrame
            target_date: Date being processed
            season: NBA season (e.g., "2023-24")

        Returns:
            True if write succeeded, False otherwise
        """
        if analytics_df.empty:
            logger.info("No player analytics data to write")
            return True

        try:
            # Add partitioning columns
            analytics_df = self._add_partition_columns(
                analytics_df, target_date, season
            )

            # Convert to PyArrow table with proper schema
            arrow_table = self._convert_to_arrow_player_table(analytics_df)

            # Get or create table
            iceberg_table = self._get_or_create_table(
                "basketball_analytics.player_analytics",
                arrow_table.schema,
                ["season", "month", "team_id"],  # Partition spec per ADR-026
            )

            # Write with optimized file sizes
            self._write_with_file_optimization(iceberg_table, arrow_table)

            logger.info(
                f"Successfully wrote {len(analytics_df)} player analytics records "
                f"for date {target_date}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to write player analytics: {e}")
            return False

    def write_team_analytics(
        self, analytics_df: pd.DataFrame, target_date: date, season: str
    ) -> bool:
        """
        Write team analytics to the team_analytics Iceberg table.

        Args:
            analytics_df: Team analytics DataFrame
            target_date: Date being processed
            season: NBA season (e.g., "2023-24")

        Returns:
            True if write succeeded, False otherwise
        """
        if analytics_df.empty:
            logger.info("No team analytics data to write")
            return True

        try:
            # Add partitioning columns
            analytics_df = self._add_partition_columns(
                analytics_df, target_date, season
            )

            # Convert to PyArrow table with proper schema
            arrow_table = self._convert_to_arrow_team_table(analytics_df)

            # Get or create table
            iceberg_table = self._get_or_create_table(
                "basketball_analytics.team_analytics",
                arrow_table.schema,
                ["season", "month", "team_id"],  # Partition spec per ADR-026
            )

            # Write with optimized file sizes
            self._write_with_file_optimization(iceberg_table, arrow_table)

            logger.info(
                f"Successfully wrote {len(analytics_df)} team analytics records "
                f"for date {target_date}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to write team analytics: {e}")
            return False

    def _add_partition_columns(
        self, df: pd.DataFrame, target_date: date, season: str
    ) -> pd.DataFrame:
        """
        Add partitioning columns to DataFrame per ADR-026 strategy.

        Args:
            df: Analytics DataFrame
            target_date: Date being processed
            season: NBA season

        Returns:
            DataFrame with partition columns added
        """
        df = df.copy()
        df["season"] = season
        df["month"] = target_date.month
        df["game_date"] = target_date

        return df

    def _convert_to_arrow_player_table(self, df: pd.DataFrame) -> pa.Table:
        """
        Convert player analytics DataFrame to PyArrow table with proper schema.

        Args:
            df: Player analytics DataFrame

        Returns:
            PyArrow table with optimized schema
        """
        # Define schema for player analytics matching Terraform definition
        schema = pa.schema(
            [
                ("player_id", pa.int64()),
                ("game_date", pa.date32()),
                ("season", pa.string()),
                ("team_id", pa.int64()),
                ("month", pa.int32()),  # Partition column
                ("points", pa.int32()),
                ("rebounds", pa.int32()),
                ("assists", pa.int32()),
                ("true_shooting_pct", pa.float64()),
                ("player_efficiency_rating", pa.float64()),
                ("usage_rate", pa.float64()),
                ("effective_field_goal_pct", pa.float64()),
                ("defensive_rating", pa.float64()),
                ("offensive_rating", pa.float64()),
            ]
        )

        return pa.Table.from_pandas(df, schema=schema)

    def _convert_to_arrow_team_table(self, df: pd.DataFrame) -> pa.Table:
        """
        Convert team analytics DataFrame to PyArrow table with proper schema.

        Args:
            df: Team analytics DataFrame

        Returns:
            PyArrow table with optimized schema
        """
        # Define schema for team analytics matching Terraform definition
        schema = pa.schema(
            [
                ("team_id", pa.int64()),
                ("game_date", pa.date32()),
                ("season", pa.string()),
                ("opponent_team_id", pa.int64()),
                ("month", pa.int32()),  # Partition column
                ("offensive_rating", pa.float64()),
                ("defensive_rating", pa.float64()),
                ("net_rating", pa.float64()),
                ("pace", pa.float64()),
                ("effective_field_goal_pct", pa.float64()),
                ("true_shooting_pct", pa.float64()),
                ("turnover_rate", pa.float64()),
                ("rebound_rate", pa.float64()),
            ]
        )

        return pa.Table.from_pandas(df, schema=schema)

    def _get_or_create_table(
        self, table_name: str, schema: pa.Schema, partition_spec: list[str]
    ) -> Any:
        """
        Get existing Iceberg table or create if it doesn't exist.

        Args:
            table_name: Full table name (namespace.table)
            schema: PyArrow schema for the table
            partition_spec: List of partition column names

        Returns:
            PyIceberg table object
        """
        try:
            # Try to load existing table
            return self.catalog.load_table(table_name)
        except NoSuchTableError:
            logger.info(f"Table {table_name} does not exist, creating...")

            # Create new table with partition spec
            from pyiceberg.partitioning import PartitionField, PartitionSpec
            from pyiceberg.transforms import identity

            # Build partition spec
            partition_fields = []
            for i, col in enumerate(partition_spec):
                field = PartitionField(
                    source_id=schema.get_field_index(col),
                    field_id=1000 + i,  # Use high field IDs for partitions
                    transform=identity,
                    name=col,
                )
                partition_fields.append(field)

            spec = PartitionSpec(*partition_fields)

            return self.catalog.create_table(
                table_name, schema=schema, partition_spec=spec
            )

    def _write_with_file_optimization(
        self, iceberg_table: Any, arrow_table: pa.Table
    ) -> None:
        """
        Write data with file size optimization for query performance.

        Args:
            iceberg_table: PyIceberg table object
            arrow_table: Data to write
        """
        # Check if we need to split the data for optimal file sizes
        if len(arrow_table) > self.MAX_ROWS_PER_FILE:
            logger.info(
                f"Splitting {len(arrow_table)} rows into multiple files "
                f"for optimal performance"
            )

            # Split into chunks
            for i in range(0, len(arrow_table), self.MAX_ROWS_PER_FILE):
                chunk = arrow_table.slice(i, self.MAX_ROWS_PER_FILE)
                iceberg_table.append(chunk)
                logger.info(
                    f"Wrote chunk {i // self.MAX_ROWS_PER_FILE + 1} "
                    f"with {len(chunk)} rows"
                )
        else:
            # Write all data at once
            iceberg_table.append(arrow_table)

    def check_table_health(self, table_name: str) -> dict[str, Any]:
        """
        Check health and status of an Iceberg table.

        Args:
            table_name: Full table name to check

        Returns:
            Dictionary with table health information
        """
        try:
            iceberg_table = self.catalog.load_table(table_name)

            # Get basic table info
            metadata = iceberg_table.metadata

            return {
                "exists": True,
                "schema_version": metadata.current_schema_id,
                "spec_version": metadata.default_spec_id,
                "snapshot_id": metadata.current_snapshot_id,
                "location": metadata.location,
            }
        except NoSuchTableError:
            return {"exists": False}
        except Exception as e:
            logger.error(f"Health check failed for table {table_name}: {e}")
            return {"exists": False, "error": str(e)}
