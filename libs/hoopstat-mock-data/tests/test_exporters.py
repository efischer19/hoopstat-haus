"""Tests for data exporters."""

import json
import tempfile
from pathlib import Path

import pandas as pd

from hoopstat_mock_data.exporters.json_exporter import JSONExporter
from hoopstat_mock_data.exporters.parquet_exporter import ParquetExporter
from hoopstat_mock_data.generators.mock_data_generator import MockDataGenerator


class TestJSONExporter:
    """Test cases for JSONExporter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = MockDataGenerator(seed=42)
        self.small_dataset = self.generator.generate_small_test_dataset()

    def test_export_to_string(self):
        """Test exporting data to JSON string."""
        json_string = JSONExporter.export_to_string(self.small_dataset["teams"])

        assert isinstance(json_string, str)

        # Parse to verify it's valid JSON
        data = json.loads(json_string)
        assert isinstance(data, list)
        assert len(data) == len(self.small_dataset["teams"])

    def test_export_complete_dataset_to_string(self):
        """Test exporting complete dataset to JSON string."""
        json_string = JSONExporter.export_to_string(self.small_dataset)

        assert isinstance(json_string, str)

        # Parse to verify structure
        data = json.loads(json_string)
        assert isinstance(data, dict)
        assert "teams" in data
        assert "players" in data
        assert "games" in data

    def test_export_to_file(self):
        """Test exporting data to JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_teams.json"

            JSONExporter.export_to_file(self.small_dataset["teams"], file_path)

            assert file_path.exists()

            # Load and verify
            with open(file_path) as f:
                data = json.load(f)

            assert isinstance(data, list)
            assert len(data) == len(self.small_dataset["teams"])

    def test_load_from_file(self):
        """Test loading data from JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_data.json"

            # Export then load
            JSONExporter.export_to_file(self.small_dataset, file_path)
            loaded_data = JSONExporter.load_from_file(file_path)

            assert isinstance(loaded_data, dict)
            assert "teams" in loaded_data
            assert len(loaded_data["teams"]) == len(self.small_dataset["teams"])

    def test_load_from_string(self):
        """Test loading data from JSON string."""
        json_string = JSONExporter.export_to_string(self.small_dataset["teams"])
        loaded_data = JSONExporter.load_from_string(json_string)

        assert isinstance(loaded_data, list)
        assert len(loaded_data) == len(self.small_dataset["teams"])


class TestParquetExporter:
    """Test cases for ParquetExporter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = MockDataGenerator(seed=42)
        self.small_dataset = self.generator.generate_small_test_dataset()

    def test_export_to_file(self):
        """Test exporting data to Parquet file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_teams.parquet"

            ParquetExporter.export_to_file(self.small_dataset["teams"], file_path)

            assert file_path.exists()

            # Load and verify
            df = pd.read_parquet(file_path)
            assert len(df) == len(self.small_dataset["teams"])
            assert "id" in df.columns
            assert "name" in df.columns

    def test_export_multiple_tables(self):
        """Test exporting multiple tables to separate files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "tables"

            data_dict = {
                "teams": self.small_dataset["teams"],
                "players": self.small_dataset["players"],
            }

            ParquetExporter.export_multiple_tables(data_dict, output_dir)

            teams_file = output_dir / "teams.parquet"
            players_file = output_dir / "players.parquet"

            assert teams_file.exists()
            assert players_file.exists()

            # Verify data
            teams_df = pd.read_parquet(teams_file)
            players_df = pd.read_parquet(players_file)

            assert len(teams_df) == len(self.small_dataset["teams"])
            assert len(players_df) == len(self.small_dataset["players"])

    def test_load_from_file(self):
        """Test loading data from Parquet file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_data.parquet"

            # Export then load
            ParquetExporter.export_to_file(self.small_dataset["teams"], file_path)
            df = ParquetExporter.load_from_file(file_path)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == len(self.small_dataset["teams"])

    def test_get_schema_info(self):
        """Test getting schema information."""
        schema_info = ParquetExporter.get_schema_info(self.small_dataset["teams"])

        assert "columns" in schema_info
        assert "dtypes" in schema_info
        assert "shape" in schema_info
        assert "memory_usage" in schema_info

        assert isinstance(schema_info["columns"], list)
        assert "id" in schema_info["columns"]
        assert "name" in schema_info["columns"]

    def test_models_to_dataframe(self):
        """Test converting models to DataFrame."""
        df = ParquetExporter._models_to_dataframe(self.small_dataset["teams"])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(self.small_dataset["teams"])
        assert "id" in df.columns
        assert "name" in df.columns

        # Check data types
        assert df["id"].dtype in ["int64", "Int64"]
        assert df["name"].dtype == "object"

    def test_empty_models_list(self):
        """Test handling empty models list."""
        df = ParquetExporter._models_to_dataframe([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
