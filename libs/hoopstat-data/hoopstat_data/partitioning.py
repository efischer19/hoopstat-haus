"""
Gold layer partitioning utilities for optimized data storage and query performance.

Provides classes and utilities for implementing hierarchical partitioning strategy
as defined in ADR-020.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PartitionType(str, Enum):
    """Supported partition types for Gold layer data."""

    PLAYER_DAILY = "player_daily_stats"
    PLAYER_SEASON = "player_season_summaries"
    TEAM_DAILY = "team_daily_stats"
    TEAM_SEASON = "team_season_summaries"
    GAME_SUMMARIES = "game_summaries"


class S3PartitionKey(BaseModel):
    """S3 partition key for Gold layer data with hierarchical structure."""

    bucket: str = Field(..., description="S3 bucket name")
    partition_type: PartitionType = Field(..., description="Type of data partition")
    season: str = Field(..., description="NBA season (e.g., '2023-24')")
    entity_id: str | None = Field(None, description="Player ID, Team ID, or Game ID")
    date: str | None = Field(None, description="Game date (YYYY-MM-DD)")
    filename: str = Field(default="stats.parquet", description="File name")

    @field_validator("season")
    @classmethod
    def validate_season_format(cls, v: str) -> str:
        """Validate NBA season format."""
        import re

        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError("Season must be in format 'YYYY-YY' (e.g., '2023-24')")
        return v

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate date format if provided."""
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in format 'YYYY-MM-DD'") from None
        return v

    @property
    def s3_prefix(self) -> str:
        """Generate S3 prefix from partition key components."""
        parts = [self.partition_type.value, f"season={self.season}"]

        if self.entity_id:
            # Use different prefix based on partition type
            if "player" in self.partition_type.value:
                parts.append(f"player_id={self.entity_id}")
            elif "team" in self.partition_type.value:
                parts.append(f"team_id={self.entity_id}")
            elif "game" in self.partition_type.value:
                parts.append(f"game_id={self.entity_id}")

        if self.date:
            parts.append(f"date={self.date}")

        return "/".join(parts)

    @property
    def s3_path(self) -> str:
        """Generate full S3 path including bucket and filename."""
        return f"s3://{self.bucket}/{self.s3_prefix}/{self.filename}"

    @property
    def local_path(self) -> Path:
        """Generate local file path structure matching S3 hierarchy."""
        return Path(self.s3_prefix) / self.filename


class FileSizeOptimizer:
    """Utilities for optimizing file sizes for Lambda performance."""

    # Target file sizes for optimal Lambda performance
    MIN_FILE_SIZE_MB = 5
    TARGET_FILE_SIZE_MB = 25
    MAX_FILE_SIZE_MB = 50

    @staticmethod
    def estimate_parquet_size(row_count: int, avg_row_size_bytes: int = 500) -> int:
        """
        Estimate Parquet file size based on row count.

        Args:
            row_count: Number of rows in the dataset
            avg_row_size_bytes: Average size per row in bytes

        Returns:
            Estimated file size in bytes
        """
        # Parquet typically achieves 60-80% compression ratio
        compression_ratio = 0.7
        base_size = row_count * avg_row_size_bytes
        return int(base_size * compression_ratio)

    @classmethod
    def should_split_file(cls, row_count: int, avg_row_size_bytes: int = 500) -> bool:
        """
        Determine if file should be split based on estimated size.

        Args:
            row_count: Number of rows in the dataset
            avg_row_size_bytes: Average size per row in bytes

        Returns:
            True if file should be split
        """
        estimated_size_mb = cls.estimate_parquet_size(row_count, avg_row_size_bytes) / (
            1024 * 1024
        )
        return estimated_size_mb > cls.MAX_FILE_SIZE_MB

    @classmethod
    def recommend_split_strategy(
        cls, row_count: int, avg_row_size_bytes: int = 500
    ) -> dict[str, Any]:
        """
        Recommend splitting strategy for large files.

        Args:
            row_count: Number of rows in the dataset
            avg_row_size_bytes: Average size per row in bytes

        Returns:
            Dictionary with splitting recommendations
        """
        estimated_size_mb = cls.estimate_parquet_size(row_count, avg_row_size_bytes) / (
            1024 * 1024
        )

        if estimated_size_mb <= cls.MAX_FILE_SIZE_MB:
            return {"should_split": False, "estimated_size_mb": estimated_size_mb}

        # Calculate number of splits needed
        target_splits = max(2, int(estimated_size_mb / cls.TARGET_FILE_SIZE_MB) + 1)
        rows_per_split = row_count // target_splits

        return {
            "should_split": True,
            "estimated_size_mb": estimated_size_mb,
            "recommended_splits": target_splits,
            "rows_per_split": rows_per_split,
            "estimated_size_per_split_mb": estimated_size_mb / target_splits,
        }


class QueryPatternOptimizer:
    """Utilities for optimizing data layout for common query patterns."""

    # Common MCP server query patterns mapped to partition strategies
    QUERY_PATTERNS = {
        "player_recent_stats": {
            "partition_type": PartitionType.PLAYER_DAILY,
            "required_keys": ["season", "entity_id"],
            "optional_keys": ["date"],
            "description": "Recent performance for specific player",
        },
        "player_season_summary": {
            "partition_type": PartitionType.PLAYER_SEASON,
            "required_keys": ["season", "entity_id"],
            "optional_keys": [],
            "description": "Full season statistics for specific player",
        },
        "team_performance": {
            "partition_type": PartitionType.TEAM_DAILY,
            "required_keys": ["season", "entity_id"],
            "optional_keys": ["date"],
            "description": "Team performance statistics",
        },
        "league_comparison": {
            "partition_type": PartitionType.PLAYER_SEASON,
            "required_keys": ["season"],
            "optional_keys": [],
            "description": "Cross-player comparisons within season",
        },
        "game_analysis": {
            "partition_type": PartitionType.GAME_SUMMARIES,
            "required_keys": ["season", "date"],
            "optional_keys": [],
            "description": "Specific game analysis",
        },
    }

    @classmethod
    def get_optimal_partition_key(
        cls, query_pattern: str, **kwargs: Any
    ) -> S3PartitionKey:
        """
        Generate optimal partition key for a given query pattern.

        Args:
            query_pattern: Name of the query pattern
            **kwargs: Parameters for partition key generation

        Returns:
            Optimized S3PartitionKey

        Raises:
            ValueError: If query pattern is unknown or required parameters missing
        """
        if query_pattern not in cls.QUERY_PATTERNS:
            available_patterns = ", ".join(cls.QUERY_PATTERNS.keys())
            raise ValueError(
                f"Unknown query pattern '{query_pattern}'. "
                f"Available patterns: {available_patterns}"
            )

        pattern_config = cls.QUERY_PATTERNS[query_pattern]

        # Validate required parameters
        for required_key in pattern_config["required_keys"]:
            if required_key not in kwargs:
                raise ValueError(
                    f"Required parameter '{required_key}' missing for pattern "
                    f"'{query_pattern}'"
                )

        # Build partition key
        partition_key_data = {
            "bucket": kwargs.get("bucket", "hoopstat-haus-gold"),
            "partition_type": pattern_config["partition_type"],
        }

        # Map generic parameters to specific partition key fields
        if "season" in kwargs:
            partition_key_data["season"] = kwargs["season"]
        if "entity_id" in kwargs:
            partition_key_data["entity_id"] = kwargs["entity_id"]
        if "date" in kwargs:
            partition_key_data["date"] = kwargs["date"]
        if "filename" in kwargs:
            partition_key_data["filename"] = kwargs["filename"]

        return S3PartitionKey(**partition_key_data)

    @classmethod
    def list_query_patterns(cls) -> dict[str, str]:
        """
        List available query patterns with descriptions.

        Returns:
            Dictionary mapping pattern names to descriptions
        """
        return {
            pattern: config["description"]
            for pattern, config in cls.QUERY_PATTERNS.items()
        }


class PartitionHealthChecker:
    """Utilities for monitoring partition health and performance."""

    @staticmethod
    def calculate_partition_hash(partition_key: S3PartitionKey) -> str:
        """
        Calculate a hash for partition identification and change detection.

        Args:
            partition_key: S3 partition key

        Returns:
            MD5 hash of the partition key
        """
        key_string = f"{partition_key.s3_prefix}/{partition_key.filename}"
        return hashlib.md5(key_string.encode()).hexdigest()

    @staticmethod
    def validate_partition_structure(partition_key: S3PartitionKey) -> dict[str, Any]:
        """
        Validate partition structure against ADR-020 standards.

        Args:
            partition_key: S3 partition key to validate

        Returns:
            Validation result with warnings and recommendations
        """
        warnings = []
        recommendations = []

        # Check season format
        if not partition_key.season:
            warnings.append("Missing season in partition key")

        # Check entity_id for player/team partitions
        if partition_key.partition_type in [
            PartitionType.PLAYER_DAILY,
            PartitionType.PLAYER_SEASON,
            PartitionType.TEAM_DAILY,
            PartitionType.TEAM_SEASON,
        ]:
            if not partition_key.entity_id:
                warnings.append(
                    f"Missing entity_id for {partition_key.partition_type} partition"
                )

        # Check date for daily partitions
        if partition_key.partition_type in [
            PartitionType.PLAYER_DAILY,
            PartitionType.TEAM_DAILY,
        ]:
            if not partition_key.date:
                recommendations.append("Consider adding date for daily partition types")

        # Check filename format
        if not partition_key.filename.endswith(".parquet"):
            warnings.append("Non-Parquet filename detected, may impact performance")

        return {
            "is_valid": len(warnings) == 0,
            "warnings": warnings,
            "recommendations": recommendations,
            "partition_hash": PartitionHealthChecker.calculate_partition_hash(
                partition_key
            ),
        }


# Convenience functions for common operations
def create_player_daily_partition(
    season: str,
    player_id: str,
    date: str,
    bucket: str = "hoopstat-haus-gold",
    filename: str = "stats.parquet",
) -> S3PartitionKey:
    """Create partition key for player daily stats."""
    return S3PartitionKey(
        bucket=bucket,
        partition_type=PartitionType.PLAYER_DAILY,
        season=season,
        entity_id=player_id,
        date=date,
        filename=filename,
    )


def create_player_season_partition(
    season: str,
    player_id: str,
    bucket: str = "hoopstat-haus-gold",
    filename: str = "season_summary.parquet",
) -> S3PartitionKey:
    """Create partition key for player season summary."""
    return S3PartitionKey(
        bucket=bucket,
        partition_type=PartitionType.PLAYER_SEASON,
        season=season,
        entity_id=player_id,
        filename=filename,
    )


def create_team_daily_partition(
    season: str,
    team_id: str,
    date: str,
    bucket: str = "hoopstat-haus-gold",
    filename: str = "stats.parquet",
) -> S3PartitionKey:
    """Create partition key for team daily stats."""
    return S3PartitionKey(
        bucket=bucket,
        partition_type=PartitionType.TEAM_DAILY,
        season=season,
        entity_id=team_id,
        date=date,
        filename=filename,
    )
