"""Tests for configuration file loaders."""

import json
import tempfile
from pathlib import Path

import pytest

from hoopstat_config.exceptions import ConfigFileError
from hoopstat_config.loaders import get_supported_formats, load_config_file


class TestConfigFileLoaders:
    """Test configuration file loading functionality."""

    def test_get_supported_formats(self):
        """Test getting supported file formats."""
        formats = get_supported_formats()

        # JSON should always be supported
        assert formats["json"] is True

        # YAML and TOML may or may not be available
        assert "yaml" in formats
        assert "toml" in formats

    def test_load_json_file(self):
        """Test loading JSON configuration file."""
        config_data = {
            "debug": True,
            "port": 8080,
            "database_url": "postgresql://localhost/test",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            result = load_config_file(config_file)
            assert result == config_data
        finally:
            Path(config_file).unlink()

    def test_load_yaml_file(self):
        """Test loading YAML configuration file."""
        yaml_content = """
debug: true
port: 8080
database_url: "postgresql://localhost/test"
nested:
  key: value
  list:
    - item1
    - item2
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            config_file = f.name

        try:
            result = load_config_file(config_file)
            assert result["debug"] is True
            assert result["port"] == 8080
            assert result["database_url"] == "postgresql://localhost/test"
            assert result["nested"]["key"] == "value"
            assert result["nested"]["list"] == ["item1", "item2"]
        finally:
            Path(config_file).unlink()

    def test_load_toml_file(self):
        """Test loading TOML configuration file."""
        toml_content = """
debug = true
port = 8080
database_url = "postgresql://localhost/test"

[nested]
key = "value"
list = ["item1", "item2"]
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_file = f.name

        try:
            result = load_config_file(config_file)
            assert result["debug"] is True
            assert result["port"] == 8080
            assert result["database_url"] == "postgresql://localhost/test"
            assert result["nested"]["key"] == "value"
            assert result["nested"]["list"] == ["item1", "item2"]
        finally:
            Path(config_file).unlink()

    def test_file_not_found(self):
        """Test error handling when file doesn't exist."""
        with pytest.raises(ConfigFileError) as exc_info:
            load_config_file("/nonexistent/path/config.json")

        assert "Configuration file not found" in str(exc_info.value)
        assert exc_info.value.file_path == "/nonexistent/path/config.json"

    def test_unsupported_file_format(self):
        """Test error handling for unsupported file formats."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("<config></config>")
            config_file = f.name

        try:
            with pytest.raises(ConfigFileError) as exc_info:
                load_config_file(config_file)

            assert "Unsupported file format '.xml'" in str(exc_info.value)
        finally:
            Path(config_file).unlink()

    def test_invalid_json_syntax(self):
        """Test error handling for invalid JSON syntax."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            config_file = f.name

        try:
            with pytest.raises(ConfigFileError) as exc_info:
                load_config_file(config_file)

            assert "Invalid JSON syntax" in str(exc_info.value)
            assert exc_info.value.file_path == config_file
        finally:
            Path(config_file).unlink()

    def test_non_dict_json(self):
        """Test error handling when JSON is not an object."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(["not", "an", "object"], f)
            config_file = f.name

        try:
            with pytest.raises(ConfigFileError) as exc_info:
                load_config_file(config_file)

            assert "JSON configuration must be an object" in str(exc_info.value)
        finally:
            Path(config_file).unlink()

    def test_invalid_yaml_syntax(self):
        """Test error handling for invalid YAML syntax."""
        yaml_content = """
debug: true
port: 8080
invalid: [unclosed list
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            config_file = f.name

        try:
            with pytest.raises(ConfigFileError) as exc_info:
                load_config_file(config_file)

            assert "Invalid YAML syntax" in str(exc_info.value)
        finally:
            Path(config_file).unlink()

    def test_empty_yaml_file(self):
        """Test handling of empty YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            config_file = f.name

        try:
            result = load_config_file(config_file)
            assert result == {}
        finally:
            Path(config_file).unlink()

    def test_non_dict_yaml(self):
        """Test error handling when YAML is not a mapping."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("- not\n- a\n- mapping")
            config_file = f.name

        try:
            with pytest.raises(ConfigFileError) as exc_info:
                load_config_file(config_file)

            assert "YAML configuration must be a mapping" in str(exc_info.value)
        finally:
            Path(config_file).unlink()

    def test_invalid_toml_syntax(self):
        """Test error handling for invalid TOML syntax."""
        toml_content = """
debug = true
port = 8080
invalid = [unclosed_array
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_file = f.name

        try:
            with pytest.raises(ConfigFileError) as exc_info:
                load_config_file(config_file)

            assert "Invalid TOML syntax" in str(exc_info.value)
        finally:
            Path(config_file).unlink()

    def test_directory_instead_of_file(self):
        """Test error handling when path points to directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ConfigFileError) as exc_info:
                load_config_file(temp_dir)

            assert "Configuration path is not a file" in str(exc_info.value)
