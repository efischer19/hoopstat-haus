"""
Tests for the Parquet converter functionality.
"""

from io import BytesIO
from unittest.mock import patch

import pyarrow.parquet as pq
import pytest

from hoopstat_nba_ingestion.parquet_converter import (
    ParquetConversionError,
    ParquetConverter,
)


class TestParquetConverter:
    """Test cases for ParquetConverter class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        converter = ParquetConverter()
        assert converter.compression == "snappy"

    def test_init_with_custom_compression(self):
        """Test initialization with custom compression."""
        converter = ParquetConverter(compression="gzip")
        assert converter.compression == "gzip"

    def test_normalize_data_dict(self):
        """Test data normalization for dictionaries."""
        converter = ParquetConverter()

        data = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
            "complex": {"nested": "value"},
        }

        normalized = converter._normalize_data(data)

        assert normalized["string"] == "test"
        assert normalized["number"] == 42
        assert normalized["float"] == 3.14
        assert normalized["bool"] is True
        assert normalized["none"] is None
        assert isinstance(normalized["complex"], dict)

    def test_normalize_data_list(self):
        """Test data normalization for lists."""
        converter = ParquetConverter()

        data = [1, "test", None, {"key": "value"}]
        normalized = converter._normalize_data(data)

        assert len(normalized) == 4
        assert normalized[0] == 1
        assert normalized[1] == "test"
        assert normalized[2] is None
        assert isinstance(normalized[3], dict)

    def test_extract_tabular_data_result_set(self):
        """Test extraction of tabular data from resultSet format."""
        converter = ParquetConverter()

        json_data = {
            "resultSet": {
                "headers": ["id", "name", "value"],
                "rowSet": [[1, "test1", 10.5], [2, "test2", 20.5]],
            },
            "fetch_date": "2024-01-15T10:00:00",
        }

        records = converter._extract_tabular_data(json_data)

        assert len(records) == 2
        assert records[0]["id"] == 1
        assert records[0]["name"] == "test1"
        assert records[0]["value"] == 10.5
        assert records[0]["fetch_date"] == "2024-01-15T10:00:00"
        assert records[1]["id"] == 2

    def test_extract_tabular_data_result_sets(self):
        """Test extraction of tabular data from resultSets format."""
        converter = ParquetConverter()

        json_data = {
            "resultSets": [
                {
                    "name": "PlayerStats",
                    "headers": ["player_id", "points"],
                    "rowSet": [[1, 25], [2, 30]],
                },
                {
                    "name": "TeamStats",
                    "headers": ["team_id", "wins"],
                    "rowSet": [[101, 15]],
                },
            ]
        }

        records = converter._extract_tabular_data(json_data)

        assert len(records) == 3
        assert records[0]["player_id"] == 1
        assert records[0]["result_set_name"] == "PlayerStats"
        assert records[1]["player_id"] == 2
        assert records[2]["team_id"] == 101
        assert records[2]["result_set_name"] == "TeamStats"

    def test_extract_tabular_data_single_record(self):
        """Test extraction when treating entire response as single record."""
        converter = ParquetConverter()

        json_data = {
            "player_id": 12345,
            "name": "Test Player",
            "position": "PG",
            "fetch_date": "2024-01-15T10:00:00",
        }

        records = converter._extract_tabular_data(json_data)

        assert len(records) == 1
        assert records[0]["player_id"] == 12345
        assert records[0]["name"] == "Test Player"
        assert records[0]["fetch_date"] == "2024-01-15T10:00:00"

    def test_convert_to_parquet_bytes(self):
        """Test conversion of JSON to Parquet bytes."""
        converter = ParquetConverter()

        json_data = {
            "resultSet": {
                "headers": ["id", "name"],
                "rowSet": [[1, "test1"], [2, "test2"]],
            }
        }

        parquet_bytes = converter.convert_to_parquet_bytes(json_data)

        assert isinstance(parquet_bytes, bytes)
        assert len(parquet_bytes) > 0

        # Verify we can read it back
        buffer = BytesIO(parquet_bytes)
        table = pq.read_table(buffer)
        df = table.to_pandas()

        assert len(df) == 2
        assert "id" in df.columns
        assert "name" in df.columns

    def test_convert_to_parquet_bytes_empty(self):
        """Test conversion of empty data."""
        converter = ParquetConverter()

        json_data = {"resultSet": {"headers": [], "rowSet": []}}

        parquet_bytes = converter.convert_to_parquet_bytes(json_data)
        assert parquet_bytes == b""

    def test_convert_games(self):
        """Test conversion of games data."""
        converter = ParquetConverter()

        games_data = [
            {"game_id": "001", "home_team": "Lakers", "away_team": "Warriors"},
            {"game_id": "002", "home_team": "Bulls", "away_team": "Heat"},
        ]

        parquet_bytes = converter.convert_games(games_data)

        assert isinstance(parquet_bytes, bytes)
        assert len(parquet_bytes) > 0

        # Verify content
        buffer = BytesIO(parquet_bytes)
        table = pq.read_table(buffer)
        df = table.to_pandas()

        assert len(df) == 2
        assert "game_id" in df.columns

    def test_convert_games_empty(self):
        """Test conversion of empty games data."""
        converter = ParquetConverter()

        parquet_bytes = converter.convert_games([])
        assert parquet_bytes == b""

    def test_convert_box_score(self):
        """Test conversion of box score data."""
        converter = ParquetConverter()

        box_score_data = {
            "game_id": "001",
            "resultSet": {
                "headers": ["player_id", "points"],
                "rowSet": [[1, 25], [2, 30]],
            },
        }

        parquet_bytes = converter.convert_box_score(box_score_data)

        assert isinstance(parquet_bytes, bytes)
        assert len(parquet_bytes) > 0

    def test_conversion_error_handling(self):
        """Test error handling during conversion."""
        converter = ParquetConverter()

        # Test with data that will cause PyArrow table creation to fail
        with pytest.raises(ParquetConversionError):
            # Create data with mixed types that can't be converted to a table
            invalid_data = {
                "resultSet": {
                    "headers": ["col1", "col2"],
                    "rowSet": [
                        ["string", 123],
                        [123, "string"],
                    ],  # Mixed types should work fine
                }
            }
            # Instead, let's mock the table creation to fail
            with patch(
                "pyarrow.Table.from_pylist", side_effect=Exception("Mock error")
            ):
                converter.convert_to_parquet_bytes(invalid_data)
