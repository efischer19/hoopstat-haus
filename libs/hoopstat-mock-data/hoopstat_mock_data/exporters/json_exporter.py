"""JSON exporter for Bronze layer data."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class JSONExporter:
    """Exporter for JSON format (Bronze layer)."""

    @staticmethod
    def export_to_file(
        data: list[BaseModel] | dict[str, list[BaseModel]] | BaseModel,
        filepath: str | Path,
    ) -> None:
        """
        Export data to JSON file.

        Args:
            data: Data to export (models or list of models)
            filepath: Output file path
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Convert Pydantic models to dictionaries
        if isinstance(data, BaseModel):
            json_data = data.model_dump()
        elif isinstance(data, list):
            json_data = [
                item.model_dump() if isinstance(item, BaseModel) else item
                for item in data
            ]
        elif isinstance(data, dict):
            json_data = {}
            for key, value in data.items():
                if isinstance(value, list):
                    json_data[key] = [
                        item.model_dump() if isinstance(item, BaseModel) else item
                        for item in value
                    ]
                elif isinstance(value, BaseModel):
                    json_data[key] = value.model_dump()
                else:
                    json_data[key] = value
        else:
            json_data = data

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, default=str)

    @staticmethod
    def export_to_string(
        data: list[BaseModel] | dict[str, list[BaseModel]] | BaseModel,
    ) -> str:
        """
        Export data to JSON string.

        Args:
            data: Data to export

        Returns:
            JSON string
        """
        # Convert Pydantic models to dictionaries
        if isinstance(data, BaseModel):
            json_data = data.model_dump()
        elif isinstance(data, list):
            json_data = [
                item.model_dump() if isinstance(item, BaseModel) else item
                for item in data
            ]
        elif isinstance(data, dict):
            json_data = {}
            for key, value in data.items():
                if isinstance(value, list):
                    json_data[key] = [
                        item.model_dump() if isinstance(item, BaseModel) else item
                        for item in value
                    ]
                elif isinstance(value, BaseModel):
                    json_data[key] = value.model_dump()
                else:
                    json_data[key] = value
        else:
            json_data = data

        return json.dumps(json_data, indent=2, default=str)

    @staticmethod
    def load_from_file(filepath: str | Path) -> Any:
        """
        Load data from JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            Loaded data
        """
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def load_from_string(json_string: str) -> Any:
        """
        Load data from JSON string.

        Args:
            json_string: JSON string

        Returns:
            Loaded data
        """
        return json.loads(json_string)
