"""
Tests for Gold layer partitioning utilities.
"""

from pathlib import Path

import pytest

from hoopstat_data.partitioning import (
    FileSizeOptimizer,
    PartitionHealthChecker,
    PartitionType,
    QueryPatternOptimizer,
    S3PartitionKey,
    create_player_daily_partition,
    create_player_season_partition,
    create_team_daily_partition,
)


class TestS3PartitionKey:
    """Test S3 partition key generation and validation."""

    def test_valid_player_daily_partition(self):
        """Test creating valid player daily partition key."""
        partition_key = S3PartitionKey(
            bucket="test-bucket",
            partition_type=PartitionType.PLAYER_DAILY,
            season="2023-24",
            entity_id="2544",
            date="2024-01-15",
        )

        assert partition_key.bucket == "test-bucket"
        assert partition_key.partition_type == PartitionType.PLAYER_DAILY
        assert partition_key.season == "2023-24"
        assert partition_key.entity_id == "2544"
        assert partition_key.date == "2024-01-15"

    def test_s3_prefix_generation(self):
        """Test S3 prefix generation for different partition types."""
        # Player daily partition
        player_partition = S3PartitionKey(
            bucket="test-bucket",
            partition_type=PartitionType.PLAYER_DAILY,
            season="2023-24",
            entity_id="2544",
            date="2024-01-15",
        )
        expected_prefix = (
            "player_daily_stats/season=2023-24/player_id=2544/date=2024-01-15"
        )
        assert player_partition.s3_prefix == expected_prefix

        # Team daily partition
        team_partition = S3PartitionKey(
            bucket="test-bucket",
            partition_type=PartitionType.TEAM_DAILY,
            season="2023-24",
            entity_id="1610612747",
            date="2024-01-15",
        )
        expected_prefix = (
            "team_daily_stats/season=2023-24/team_id=1610612747/date=2024-01-15"
        )
        assert team_partition.s3_prefix == expected_prefix

        # Player season summary (no date)
        season_partition = S3PartitionKey(
            bucket="test-bucket",
            partition_type=PartitionType.PLAYER_SEASON,
            season="2023-24",
            entity_id="2544",
        )
        expected_prefix = "player_season_summaries/season=2023-24/player_id=2544"
        assert season_partition.s3_prefix == expected_prefix

    def test_s3_path_generation(self):
        """Test full S3 path generation."""
        partition_key = S3PartitionKey(
            bucket="test-bucket",
            partition_type=PartitionType.PLAYER_DAILY,
            season="2023-24",
            entity_id="2544",
            date="2024-01-15",
            filename="daily_stats.parquet",
        )

        expected_path = (
            "s3://test-bucket/player_daily_stats/season=2023-24/"
            "player_id=2544/date=2024-01-15/daily_stats.parquet"
        )
        assert partition_key.s3_path == expected_path

    def test_local_path_generation(self):
        """Test local path generation."""
        partition_key = S3PartitionKey(
            bucket="test-bucket",
            partition_type=PartitionType.PLAYER_DAILY,
            season="2023-24",
            entity_id="2544",
            date="2024-01-15",
        )

        expected_path = Path(
            "player_daily_stats/season=2023-24/player_id=2544/date=2024-01-15/stats.parquet"
        )
        assert partition_key.local_path == expected_path

    def test_invalid_season_format(self):
        """Test validation of invalid season format."""
        with pytest.raises(ValueError, match="Season must be in format"):
            S3PartitionKey(
                bucket="test-bucket",
                partition_type=PartitionType.PLAYER_DAILY,
                season="2023",  # Invalid format
                entity_id="2544",
            )

    def test_invalid_date_format(self):
        """Test validation of invalid date format."""
        with pytest.raises(ValueError, match="Date must be in format"):
            S3PartitionKey(
                bucket="test-bucket",
                partition_type=PartitionType.PLAYER_DAILY,
                season="2023-24",
                entity_id="2544",
                date="01-15-2024",  # Invalid format
            )

    def test_game_partition_type(self):
        """Test game partition type key generation."""
        partition_key = S3PartitionKey(
            bucket="test-bucket",
            partition_type=PartitionType.GAME_SUMMARIES,
            season="2023-24",
            entity_id="0022300123",
            date="2024-01-15",
        )

        expected_prefix = (
            "game_summaries/season=2023-24/game_id=0022300123/date=2024-01-15"
        )
        assert partition_key.s3_prefix == expected_prefix


class TestFileSizeOptimizer:
    """Test file size optimization utilities."""

    def test_estimate_parquet_size(self):
        """Test Parquet file size estimation."""
        # Small file
        size_bytes = FileSizeOptimizer.estimate_parquet_size(100, 500)
        assert size_bytes == int(100 * 500 * 0.7)  # 35,000 bytes

        # Large file
        size_bytes = FileSizeOptimizer.estimate_parquet_size(10000, 1000)
        assert size_bytes == int(10000 * 1000 * 0.7)  # 7,000,000 bytes

    def test_should_split_file(self):
        """Test file splitting decision logic."""
        # Small file - should not split
        assert not FileSizeOptimizer.should_split_file(1000, 500)  # ~350KB

        # Large file - should split
        assert FileSizeOptimizer.should_split_file(200000, 500)  # ~70MB

    def test_recommend_split_strategy(self):
        """Test split strategy recommendations."""
        # Small file - no split needed
        result = FileSizeOptimizer.recommend_split_strategy(1000, 500)
        assert not result["should_split"]
        assert "estimated_size_mb" in result

        # Large file - split recommended
        result = FileSizeOptimizer.recommend_split_strategy(200000, 500)
        assert result["should_split"]
        assert result["recommended_splits"] >= 2
        assert "rows_per_split" in result
        assert "estimated_size_per_split_mb" in result


class TestQueryPatternOptimizer:
    """Test query pattern optimization utilities."""

    def test_list_query_patterns(self):
        """Test listing available query patterns."""
        patterns = QueryPatternOptimizer.list_query_patterns()

        assert "player_recent_stats" in patterns
        assert "player_season_summary" in patterns
        assert "team_performance" in patterns
        assert "league_comparison" in patterns
        assert "game_analysis" in patterns

        # Check descriptions are provided
        for _pattern, description in patterns.items():
            assert isinstance(description, str)
            assert len(description) > 0

    def test_player_recent_stats_pattern(self):
        """Test player recent stats query pattern optimization."""
        partition_key = QueryPatternOptimizer.get_optimal_partition_key(
            "player_recent_stats",
            bucket="test-bucket",
            season="2023-24",
            entity_id="2544",
            date="2024-01-15",
        )

        assert partition_key.partition_type == PartitionType.PLAYER_DAILY
        assert partition_key.season == "2023-24"
        assert partition_key.entity_id == "2544"
        assert partition_key.date == "2024-01-15"

    def test_player_season_summary_pattern(self):
        """Test player season summary query pattern optimization."""
        partition_key = QueryPatternOptimizer.get_optimal_partition_key(
            "player_season_summary",
            bucket="test-bucket",
            season="2023-24",
            entity_id="2544",
        )

        assert partition_key.partition_type == PartitionType.PLAYER_SEASON
        assert partition_key.season == "2023-24"
        assert partition_key.entity_id == "2544"
        assert partition_key.date is None

    def test_team_performance_pattern(self):
        """Test team performance query pattern optimization."""
        partition_key = QueryPatternOptimizer.get_optimal_partition_key(
            "team_performance",
            bucket="test-bucket",
            season="2023-24",
            entity_id="1610612747",
            date="2024-01-15",
        )

        assert partition_key.partition_type == PartitionType.TEAM_DAILY
        assert partition_key.season == "2023-24"
        assert partition_key.entity_id == "1610612747"
        assert partition_key.date == "2024-01-15"

    def test_league_comparison_pattern(self):
        """Test league comparison query pattern optimization."""
        partition_key = QueryPatternOptimizer.get_optimal_partition_key(
            "league_comparison",
            bucket="test-bucket",
            season="2023-24",
        )

        assert partition_key.partition_type == PartitionType.PLAYER_SEASON
        assert partition_key.season == "2023-24"
        assert partition_key.entity_id is None

    def test_game_analysis_pattern(self):
        """Test game analysis query pattern optimization."""
        partition_key = QueryPatternOptimizer.get_optimal_partition_key(
            "game_analysis",
            bucket="test-bucket",
            season="2023-24",
            date="2024-01-15",
        )

        assert partition_key.partition_type == PartitionType.GAME_SUMMARIES
        assert partition_key.season == "2023-24"
        assert partition_key.date == "2024-01-15"

    def test_unknown_query_pattern(self):
        """Test handling of unknown query patterns."""
        with pytest.raises(ValueError, match="Unknown query pattern"):
            QueryPatternOptimizer.get_optimal_partition_key(
                "unknown_pattern",
                bucket="test-bucket",
                season="2023-24",
            )

    def test_missing_required_parameters(self):
        """Test handling of missing required parameters."""
        with pytest.raises(ValueError, match="Required parameter.*missing"):
            QueryPatternOptimizer.get_optimal_partition_key(
                "player_recent_stats",
                bucket="test-bucket",
                # Missing season and entity_id
            )


class TestPartitionHealthChecker:
    """Test partition health checking utilities."""

    def test_calculate_partition_hash(self):
        """Test partition hash calculation."""
        partition_key = S3PartitionKey(
            bucket="test-bucket",
            partition_type=PartitionType.PLAYER_DAILY,
            season="2023-24",
            entity_id="2544",
            date="2024-01-15",
        )

        hash1 = PartitionHealthChecker.calculate_partition_hash(partition_key)
        hash2 = PartitionHealthChecker.calculate_partition_hash(partition_key)

        # Same partition should generate same hash
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length

        # Different partition should generate different hash
        partition_key2 = S3PartitionKey(
            bucket="test-bucket",
            partition_type=PartitionType.PLAYER_DAILY,
            season="2023-24",
            entity_id="2544",
            date="2024-01-16",  # Different date
        )
        hash3 = PartitionHealthChecker.calculate_partition_hash(partition_key2)
        assert hash1 != hash3

    def test_validate_partition_structure_valid(self):
        """Test validation of valid partition structure."""
        partition_key = S3PartitionKey(
            bucket="test-bucket",
            partition_type=PartitionType.PLAYER_DAILY,
            season="2023-24",
            entity_id="2544",
            date="2024-01-15",
        )

        result = PartitionHealthChecker.validate_partition_structure(partition_key)

        assert result["is_valid"]
        assert len(result["warnings"]) == 0
        assert "partition_hash" in result

    def test_validate_partition_structure_missing_entity_id(self):
        """Test validation with missing entity_id for player partition."""
        partition_key = S3PartitionKey(
            bucket="test-bucket",
            partition_type=PartitionType.PLAYER_DAILY,
            season="2023-24",
            # Missing entity_id
        )

        result = PartitionHealthChecker.validate_partition_structure(partition_key)

        assert not result["is_valid"]
        assert any("Missing entity_id" in warning for warning in result["warnings"])

    def test_validate_partition_structure_missing_date_recommendation(self):
        """Test validation with missing date for daily partition."""
        partition_key = S3PartitionKey(
            bucket="test-bucket",
            partition_type=PartitionType.PLAYER_DAILY,
            season="2023-24",
            entity_id="2544",
            # Missing date - should be recommendation, not warning
        )

        result = PartitionHealthChecker.validate_partition_structure(partition_key)

        # Should be valid but with recommendation
        assert result["is_valid"]
        assert any("date" in rec for rec in result["recommendations"])

    def test_validate_partition_structure_non_parquet_filename(self):
        """Test validation with non-Parquet filename."""
        partition_key = S3PartitionKey(
            bucket="test-bucket",
            partition_type=PartitionType.PLAYER_DAILY,
            season="2023-24",
            entity_id="2544",
            date="2024-01-15",
            filename="data.csv",  # Non-Parquet file
        )

        result = PartitionHealthChecker.validate_partition_structure(partition_key)

        assert not result["is_valid"]
        assert any("Non-Parquet" in warning for warning in result["warnings"])


class TestConvenienceFunctions:
    """Test convenience functions for common partition operations."""

    def test_create_player_daily_partition(self):
        """Test creating player daily partition with convenience function."""
        partition_key = create_player_daily_partition(
            season="2023-24",
            player_id="2544",
            date="2024-01-15",
            bucket="test-bucket",
        )

        assert partition_key.partition_type == PartitionType.PLAYER_DAILY
        assert partition_key.season == "2023-24"
        assert partition_key.entity_id == "2544"
        assert partition_key.date == "2024-01-15"
        assert partition_key.bucket == "test-bucket"

    def test_create_player_season_partition(self):
        """Test creating player season partition with convenience function."""
        partition_key = create_player_season_partition(
            season="2023-24",
            player_id="2544",
            bucket="test-bucket",
        )

        assert partition_key.partition_type == PartitionType.PLAYER_SEASON
        assert partition_key.season == "2023-24"
        assert partition_key.entity_id == "2544"
        assert partition_key.filename == "season_summary.parquet"
        assert partition_key.bucket == "test-bucket"

    def test_create_team_daily_partition(self):
        """Test creating team daily partition with convenience function."""
        partition_key = create_team_daily_partition(
            season="2023-24",
            team_id="1610612747",
            date="2024-01-15",
            bucket="test-bucket",
        )

        assert partition_key.partition_type == PartitionType.TEAM_DAILY
        assert partition_key.season == "2023-24"
        assert partition_key.entity_id == "1610612747"
        assert partition_key.date == "2024-01-15"
        assert partition_key.bucket == "test-bucket"

    def test_default_bucket_values(self):
        """Test default bucket values in convenience functions."""
        partition_key = create_player_daily_partition(
            season="2023-24",
            player_id="2544",
            date="2024-01-15",
            # Using default bucket
        )

        assert partition_key.bucket == "hoopstat-haus-gold"
