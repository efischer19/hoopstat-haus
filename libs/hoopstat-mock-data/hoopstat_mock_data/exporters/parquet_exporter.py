"""Parquet exporter for Silver/Gold layer data."""

from pathlib import Path

import pandas as pd
from pydantic import BaseModel


class ParquetExporter:
    """Exporter for Parquet format (Silver/Gold layers)."""

    @staticmethod
    def export_to_file(
        data: list[BaseModel], filepath: str | Path, compression: str = "snappy"
    ) -> None:
        """
        Export data to Parquet file.

        Args:
            data: List of Pydantic models to export
            filepath: Output file path
            compression: Compression method (snappy, gzip, brotli)
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Convert Pydantic models to DataFrame
        df = ParquetExporter._models_to_dataframe(data)

        # Write to Parquet
        df.to_parquet(filepath, compression=compression, index=False)

    @staticmethod
    def export_multiple_tables(
        data_dict: dict[str, list[BaseModel]],
        output_dir: str | Path,
        compression: str = "snappy",
    ) -> None:
        """
        Export multiple tables to separate Parquet files.

        Args:
            data_dict: Dictionary of table name to list of models
            output_dir: Output directory
            compression: Compression method
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for table_name, models in data_dict.items():
            if models:  # Only export non-empty tables
                filepath = output_dir / f"{table_name}.parquet"
                ParquetExporter.export_to_file(models, filepath, compression)

    @staticmethod
    def export_partitioned(
        data: list[BaseModel],
        output_dir: str | Path,
        partition_cols: list[str],
        compression: str = "snappy",
    ) -> None:
        """
        Export data with partitioning (useful for large datasets).

        Args:
            data: List of Pydantic models to export
            output_dir: Output directory
            partition_cols: Columns to partition by
            compression: Compression method
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Convert to DataFrame
        df = ParquetExporter._models_to_dataframe(data)

        # Write partitioned Parquet
        df.to_parquet(
            output_dir,
            partition_cols=partition_cols,
            compression=compression,
            index=False,
        )

    @staticmethod
    def load_from_file(filepath: str | Path) -> pd.DataFrame:
        """
        Load data from Parquet file.

        Args:
            filepath: Path to Parquet file

        Returns:
            DataFrame with loaded data
        """
        return pd.read_parquet(filepath)

    @staticmethod
    def load_partitioned(directory: str | Path) -> pd.DataFrame:
        """
        Load partitioned Parquet data.

        Args:
            directory: Directory containing partitioned Parquet files

        Returns:
            DataFrame with loaded data
        """
        return pd.read_parquet(directory)

    @staticmethod
    def _models_to_dataframe(models: list[BaseModel]) -> pd.DataFrame:
        """
        Convert list of Pydantic models to pandas DataFrame.

        Args:
            models: List of Pydantic models

        Returns:
            DataFrame
        """
        if not models:
            return pd.DataFrame()

        # Convert models to dictionaries
        data = [model.model_dump() for model in models]

        # Create DataFrame
        df = pd.DataFrame(data)

        # Convert datetime columns to proper datetime type
        for col in df.columns:
            if df[col].dtype == "object":
                # Try to convert datetime strings
                try:
                    df[col] = pd.to_datetime(df[col], errors="ignore")
                except (ValueError, TypeError):
                    pass

        return df

    @staticmethod
    def get_schema_info(data: list[BaseModel]) -> dict:
        """
        Get schema information for the data.

        Args:
            data: List of Pydantic models

        Returns:
            Dictionary with schema information
        """
        if not data:
            return {}

        df = ParquetExporter._models_to_dataframe(data)

        schema_info = {
            "columns": list(df.columns),
            "dtypes": df.dtypes.to_dict(),
            "shape": df.shape,
            "memory_usage": df.memory_usage(deep=True).sum(),
        }

        return schema_info
