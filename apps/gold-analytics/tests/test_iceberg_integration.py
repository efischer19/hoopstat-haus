"""
Tests for Apache Iceberg S3 Tables integration.

These tests validate the Iceberg writer functionality including:
- PyIceberg dependency integration
- Table creation with proper partitioning
- Data writing with file size optimization
- Schema validation and error handling
"""

from datetime import date
from unittest.mock import Mock, patch, MagicMock

import pandas as pd
import pytest
import pyarrow as pa
from app.iceberg_integration import IcebergS3TablesWriter


class TestIcebergS3TablesWriter:
    """Test cases for Iceberg S3 Tables writer."""

    @pytest.fixture
    def mock_catalog(self):
        """Mock PyIceberg catalog for testing."""
        with patch("app.iceberg_integration.load_catalog") as mock_load:
            catalog = Mock()
            mock_load.return_value = catalog
            yield catalog

    @pytest.fixture
    def writer(self, mock_catalog):
        """Create IcebergS3TablesWriter instance for testing."""
        return IcebergS3TablesWriter("test-gold-bucket", "us-east-1")

    @pytest.fixture
    def sample_player_data(self):
        """Sample player analytics data for testing."""
        return pd.DataFrame({
            "player_id": [2544, 201939],  # LeBron, Curry
            "team_id": [1610612747, 1610612744],  # Lakers, Warriors
            "points": [25, 30],
            "rebounds": [8, 5],
            "assists": [7, 6],
            "true_shooting_pct": [0.58, 0.65],
            "player_efficiency_rating": [22.5, 25.8],
            "usage_rate": [0.28, 0.32],
            "effective_field_goal_pct": [0.52, 0.62],
            "defensive_rating": [110.5, 108.2],
            "offensive_rating": [115.3, 118.7],
        })

    @pytest.fixture
    def sample_team_data(self):
        """Sample team analytics data for testing."""
        return pd.DataFrame({
            "team_id": [1610612747, 1610612744],  # Lakers, Warriors
            "opponent_team_id": [1610612744, 1610612747],  # Warriors, Lakers
            "offensive_rating": [115.3, 118.7],
            "defensive_rating": [110.5, 108.2],
            "net_rating": [4.8, 10.5],
            "pace": [102.3, 104.1],
            "effective_field_goal_pct": [0.52, 0.62],
            "true_shooting_pct": [0.58, 0.65],
            "turnover_rate": [0.12, 0.11],
            "rebound_rate": [0.48, 0.52],
        })

    def test_writer_initialization(self, mock_catalog):
        """Test IcebergS3TablesWriter initialization."""
        writer = IcebergS3TablesWriter("test-bucket", "us-west-2")
        
        assert writer.gold_bucket == "test-bucket"
        assert writer.aws_region == "us-west-2"
        assert writer.catalog is not None

    def test_add_partition_columns(self, writer, sample_player_data):
        """Test adding partition columns to DataFrame."""
        target_date = date(2024, 1, 15)
        season = "2023-24"
        
        result = writer._add_partition_columns(sample_player_data, target_date, season)
        
        assert "season" in result.columns
        assert "month" in result.columns
        assert "game_date" in result.columns
        assert all(result["season"] == season)
        assert all(result["month"] == 1)
        assert all(result["game_date"] == target_date)

    def test_convert_to_arrow_player_table(self, writer, sample_player_data):
        """Test converting player DataFrame to PyArrow table."""
        # Add required columns
        df = writer._add_partition_columns(sample_player_data, date(2024, 1, 15), "2023-24")
        
        arrow_table = writer._convert_to_arrow_player_table(df)
        
        assert isinstance(arrow_table, pa.Table)
        assert len(arrow_table) == len(df)
        
        # Check required schema fields
        schema_names = [field.name for field in arrow_table.schema]
        assert "player_id" in schema_names
        assert "team_id" in schema_names
        assert "season" in schema_names
        assert "month" in schema_names
        assert "true_shooting_pct" in schema_names

    def test_convert_to_arrow_team_table(self, writer, sample_team_data):
        """Test converting team DataFrame to PyArrow table."""
        # Add required columns
        df = writer._add_partition_columns(sample_team_data, date(2024, 1, 15), "2023-24")
        
        arrow_table = writer._convert_to_arrow_team_table(df)
        
        assert isinstance(arrow_table, pa.Table)
        assert len(arrow_table) == len(df)
        
        # Check required schema fields
        schema_names = [field.name for field in arrow_table.schema]
        assert "team_id" in schema_names
        assert "opponent_team_id" in schema_names
        assert "season" in schema_names
        assert "month" in schema_names
        assert "offensive_rating" in schema_names

    def test_write_player_analytics_success(self, writer, sample_player_data, mock_catalog):
        """Test successful player analytics write."""
        # Mock table operations
        mock_table = Mock()
        mock_catalog.load_table.return_value = mock_table
        
        target_date = date(2024, 1, 15)
        season = "2023-24"
        
        result = writer.write_player_analytics(sample_player_data, target_date, season)
        
        assert result is True
        mock_table.append.assert_called_once()

    def test_write_team_analytics_success(self, writer, sample_team_data, mock_catalog):
        """Test successful team analytics write."""
        # Mock table operations
        mock_table = Mock()
        mock_catalog.load_table.return_value = mock_table
        
        target_date = date(2024, 1, 15)
        season = "2023-24"
        
        result = writer.write_team_analytics(sample_team_data, target_date, season)
        
        assert result is True
        mock_table.append.assert_called_once()

    def test_write_empty_dataframe(self, writer):
        """Test writing empty DataFrame returns True without error."""
        empty_df = pd.DataFrame()
        target_date = date(2024, 1, 15)
        season = "2023-24"
        
        result = writer.write_player_analytics(empty_df, target_date, season)
        assert result is True

    def test_write_large_dataset_chunking(self, writer, mock_catalog):
        """Test file size optimization with large datasets."""
        # Create large dataset to trigger chunking
        large_data = pd.DataFrame({
            "player_id": range(60000),  # More than MAX_ROWS_PER_FILE
            "team_id": [1610612747] * 60000,
            "points": [25] * 60000,
            "rebounds": [8] * 60000,
            "assists": [7] * 60000,
            "true_shooting_pct": [0.58] * 60000,
            "player_efficiency_rating": [22.5] * 60000,
            "usage_rate": [0.28] * 60000,
            "effective_field_goal_pct": [0.52] * 60000,
            "defensive_rating": [110.5] * 60000,
            "offensive_rating": [115.3] * 60000,
        })
        
        # Mock table operations
        mock_table = Mock()
        mock_catalog.load_table.return_value = mock_table
        
        target_date = date(2024, 1, 15)
        season = "2023-24"
        
        result = writer.write_player_analytics(large_data, target_date, season)
        
        assert result is True
        # Should call append multiple times for chunks
        assert mock_table.append.call_count > 1

    def test_table_health_check_existing(self, writer, mock_catalog):
        """Test health check for existing table."""
        # Mock existing table with metadata
        mock_table = Mock()
        mock_metadata = Mock()
        mock_metadata.current_schema_id = 1
        mock_metadata.default_spec_id = 0
        mock_metadata.current_snapshot_id = 12345
        mock_metadata.location = "s3://test-bucket/table/"
        mock_table.metadata = mock_metadata
        mock_catalog.load_table.return_value = mock_table
        
        health = writer.check_table_health("basketball_analytics.player_analytics")
        
        assert health["exists"] is True
        assert health["schema_version"] == 1
        assert health["snapshot_id"] == 12345

    def test_table_health_check_nonexistent(self, writer, mock_catalog):
        """Test health check for non-existent table."""
        from pyiceberg.exceptions import NoSuchTableError
        
        mock_catalog.load_table.side_effect = NoSuchTableError("Table not found")
        
        health = writer.check_table_health("basketball_analytics.nonexistent")
        
        assert health["exists"] is False

    def test_error_handling_catalog_failure(self):
        """Test error handling when catalog configuration fails."""
        with patch("app.iceberg_integration.load_catalog") as mock_load:
            mock_load.side_effect = Exception("Catalog connection failed")
            
            with pytest.raises(Exception):
                IcebergS3TablesWriter("test-bucket")

    def test_error_handling_write_failure(self, writer, sample_player_data, mock_catalog):
        """Test error handling during write operations."""
        # Mock table operation failure
        mock_table = Mock()
        mock_table.append.side_effect = Exception("Write failed")
        mock_catalog.load_table.return_value = mock_table
        
        target_date = date(2024, 1, 15)
        season = "2023-24"
        
        result = writer.write_player_analytics(sample_player_data, target_date, season)
        
        assert result is False


class TestPerformanceOptimization:
    """Test cases for file size and performance optimization."""

    def test_file_size_target_constants(self):
        """Test that file size constants are within expected ranges."""
        assert IcebergS3TablesWriter.TARGET_FILE_SIZE_MB >= 64
        assert IcebergS3TablesWriter.TARGET_FILE_SIZE_MB <= 128
        assert IcebergS3TablesWriter.MAX_ROWS_PER_FILE > 0

    def test_chunking_calculation(self):
        """Test chunking logic for large datasets."""
        max_rows = IcebergS3TablesWriter.MAX_ROWS_PER_FILE
        
        # Test exact boundary
        assert max_rows == 50000  # Expected value
        
        # Test chunking behavior would be correct
        large_dataset_size = 150000
        expected_chunks = (large_dataset_size + max_rows - 1) // max_rows
        assert expected_chunks == 3  # 150k rows = 3 chunks of 50k each