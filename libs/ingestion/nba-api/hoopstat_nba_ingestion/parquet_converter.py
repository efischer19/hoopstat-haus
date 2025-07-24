"""
JSON to Parquet conversion functionality for NBA data.
"""

import logging
from io import BytesIO
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


class ParquetConversionError(Exception):
    """Custom exception for Parquet conversion errors."""

    pass


class ParquetConverter:
    """
    Convert NBA API JSON responses to Parquet format.

    Follows ADR-014 decision to use Apache Parquet for structured data storage.
    """

    def __init__(self, compression: str = "snappy"):
        """
        Initialize the Parquet converter.

        Args:
            compression: Compression algorithm to use (snappy, gzip, brotli, lz4)
        """
        self.compression = compression

    def _normalize_data(self, data: Any) -> Any:
        """
        Normalize data for Parquet conversion.

        Args:
            data: Raw data to normalize

        Returns:
            Normalized data suitable for Parquet
        """
        if isinstance(data, dict):
            return {k: self._normalize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._normalize_data(item) for item in data]
        elif data is None:
            return None
        else:
            # Convert to string if not a basic type
            if not isinstance(data, int | float | str | bool):
                return str(data)
            return data

    def _extract_tabular_data(self, json_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract tabular data from NBA API JSON response.

        Args:
            json_data: Raw JSON response from NBA API

        Returns:
            List of records suitable for conversion to Parquet
        """
        records = []

        # Handle different NBA API response structures
        if "resultSet" in json_data:
            # Standard result set format
            result_set = json_data["resultSet"]
            if isinstance(result_set, dict):
                headers = result_set.get("headers", [])
                rows = result_set.get("rowSet", [])

                for row in rows:
                    record = dict(zip(headers, row, strict=False))
                    record = self._normalize_data(record)
                    records.append(record)

        elif "resultSets" in json_data:
            # Multiple result sets format
            for i, result_set in enumerate(json_data["resultSets"]):
                headers = result_set.get("headers", [])
                rows = result_set.get("rowSet", [])
                name = result_set.get("name", f"resultSet_{i}")

                for row in rows:
                    record = dict(zip(headers, row, strict=False))
                    record = self._normalize_data(record)
                    record["result_set_name"] = name
                    records.append(record)

        else:
            # Treat entire response as a single record
            record = self._normalize_data(json_data)
            records.append(record)

        # Add metadata if present
        metadata_fields = ["fetch_date", "game_id", "player_id"]
        for field in metadata_fields:
            if field in json_data:
                for record in records:
                    record[field] = json_data[field]

        return records

    def convert_to_parquet_bytes(self, json_data: dict[str, Any]) -> bytes:
        """
        Convert JSON data to Parquet format as bytes.

        Args:
            json_data: JSON data from NBA API

        Returns:
            Parquet data as bytes

        Raises:
            ParquetConversionError: If conversion fails
        """
        try:
            # Extract tabular data
            records = self._extract_tabular_data(json_data)

            if not records:
                logger.warning("No records found in JSON data")
                return b""

            # Convert to PyArrow table
            table = pa.Table.from_pylist(records)

            # Write to bytes buffer
            buffer = BytesIO()
            pq.write_table(
                table,
                buffer,
                compression=self.compression,
                write_statistics=True,
                use_dictionary=True,
            )

            parquet_bytes = buffer.getvalue()
            buffer.close()

            logger.debug(
                f"Converted {len(records)} records to Parquet "
                f"({len(parquet_bytes)} bytes)"
            )
            return parquet_bytes

        except Exception as e:
            logger.error(f"Failed to convert JSON to Parquet: {e}")
            raise ParquetConversionError(f"Parquet conversion failed: {e}") from e

    def convert_games(self, games_data: list[dict[str, Any]]) -> bytes:
        """
        Convert games data to Parquet format.

        Args:
            games_data: List of game dictionaries

        Returns:
            Parquet data as bytes
        """
        try:
            if not games_data:
                logger.warning("No games data to convert")
                return b""

            # Normalize all game records
            normalized_games = [self._normalize_data(game) for game in games_data]

            # Convert to PyArrow table
            table = pa.Table.from_pylist(normalized_games)

            # Write to bytes buffer
            buffer = BytesIO()
            pq.write_table(
                table,
                buffer,
                compression=self.compression,
                write_statistics=True,
                use_dictionary=True,
            )

            parquet_bytes = buffer.getvalue()
            buffer.close()

            logger.info(
                f"Converted {len(games_data)} games to Parquet "
                f"({len(parquet_bytes)} bytes)"
            )
            return parquet_bytes

        except Exception as e:
            logger.error(f"Failed to convert games to Parquet: {e}")
            raise ParquetConversionError(f"Games conversion failed: {e}") from e

    def convert_box_score(self, box_score_data: dict[str, Any]) -> bytes:
        """
        Convert box score data to Parquet format.

        Args:
            box_score_data: Box score dictionary

        Returns:
            Parquet data as bytes
        """
        try:
            return self.convert_to_parquet_bytes(box_score_data)
        except Exception as e:
            logger.error(f"Failed to convert box score to Parquet: {e}")
            raise ParquetConversionError(f"Box score conversion failed: {e}") from e

    def convert_player_info(self, player_data: dict[str, Any]) -> bytes:
        """
        Convert player info to Parquet format.

        Args:
            player_data: Player info dictionary

        Returns:
            Parquet data as bytes
        """
        try:
            return self.convert_to_parquet_bytes(player_data)
        except Exception as e:
            logger.error(f"Failed to convert player info to Parquet: {e}")
            raise ParquetConversionError(f"Player info conversion failed: {e}") from e

    def convert_standings(self, standings_data: dict[str, Any]) -> bytes:
        """
        Convert league standings to Parquet format.

        Args:
            standings_data: Standings dictionary

        Returns:
            Parquet data as bytes
        """
        try:
            return self.convert_to_parquet_bytes(standings_data)
        except Exception as e:
            logger.error(f"Failed to convert standings to Parquet: {e}")
            raise ParquetConversionError(f"Standings conversion failed: {e}") from e
