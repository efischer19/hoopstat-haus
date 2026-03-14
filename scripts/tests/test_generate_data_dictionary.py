"""Tests for the Data Dictionary generator script."""

import importlib.util
from pathlib import Path
from unittest.mock import patch

from pydantic import BaseModel, Field

# Load the generator module directly to avoid package-level imports
_script_path = Path(__file__).resolve().parent.parent / "generate-data-dictionary.py"
_spec = importlib.util.spec_from_file_location("gen_dd", _script_path)
gen_dd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen_dd)


# ---------------------------------------------------------------------------
# Fixtures: lightweight Pydantic models for testing
# ---------------------------------------------------------------------------


class _SampleModel(BaseModel):
    """A sample model for testing."""

    id: str = Field(..., description="Primary key")
    name: str | None = Field(None, description="Display name")
    score: int = Field(ge=0, le=100, description="Score value")
    ratio: float | None = Field(None, ge=0, le=1, description="A ratio")


# ---------------------------------------------------------------------------
# Tests for get_type_name
# ---------------------------------------------------------------------------


class TestGetTypeName:
    """Tests for the get_type_name helper."""

    def test_basic_types(self):
        """Basic Python types render as their name."""
        assert gen_dd.get_type_name(str) == "str"
        assert gen_dd.get_type_name(int) == "int"
        assert gen_dd.get_type_name(float) == "float"
        assert gen_dd.get_type_name(bool) == "bool"

    def test_optional_type(self):
        """Union with None renders with '| None'."""
        result = gen_dd.get_type_name(str | None)
        assert "str" in result
        assert "None" in result

    def test_none_type(self):
        """NoneType renders as 'None'."""
        assert gen_dd.get_type_name(type(None)) == "None"


# ---------------------------------------------------------------------------
# Tests for get_constraints
# ---------------------------------------------------------------------------


class TestGetConstraints:
    """Tests for the get_constraints helper."""

    def test_no_constraints(self):
        """Fields without constraints return '--'."""
        field_info = _SampleModel.model_fields["id"]
        assert gen_dd.get_constraints(field_info) == "--"

    def test_ge_le_constraints(self):
        """Fields with ge/le constraints are extracted."""
        field_info = _SampleModel.model_fields["score"]
        result = gen_dd.get_constraints(field_info)
        assert "ge=0" in result
        assert "le=100" in result

    def test_ratio_constraints(self):
        """Optional fields preserve constraints."""
        field_info = _SampleModel.model_fields["ratio"]
        result = gen_dd.get_constraints(field_info)
        assert "ge=0" in result
        assert "le=1" in result


# ---------------------------------------------------------------------------
# Tests for extract_model_fields
# ---------------------------------------------------------------------------


class TestExtractModelFields:
    """Tests for extract_model_fields."""

    def test_extracts_all_fields(self):
        """All model fields are extracted."""
        fields = gen_dd.extract_model_fields(_SampleModel)
        names = [f["name"] for f in fields]
        assert "id" in names
        assert "name" in names
        assert "score" in names
        assert "ratio" in names

    def test_required_flag(self):
        """Required vs optional is detected correctly."""
        fields = {f["name"]: f for f in gen_dd.extract_model_fields(_SampleModel)}
        assert fields["id"]["required"] is True
        assert fields["name"]["required"] is False
        assert fields["score"]["required"] is True
        assert fields["ratio"]["required"] is False

    def test_descriptions(self):
        """Descriptions from Field() are extracted."""
        fields = {f["name"]: f for f in gen_dd.extract_model_fields(_SampleModel)}
        assert fields["id"]["description"] == "Primary key"
        assert fields["name"]["description"] == "Display name"

    def test_types(self):
        """Type annotations are rendered as strings."""
        fields = {f["name"]: f for f in gen_dd.extract_model_fields(_SampleModel)}
        assert fields["id"]["type"] == "str"
        assert "None" in fields["name"]["type"]
        assert fields["score"]["type"] == "int"


# ---------------------------------------------------------------------------
# Tests for generate_model_table
# ---------------------------------------------------------------------------


class TestGenerateModelTable:
    """Tests for generate_model_table."""

    def test_table_header(self):
        """Generated table includes a Markdown header and column row."""
        lines = gen_dd.generate_model_table("SampleModel", _SampleModel, "A sample.")
        text = "\n".join(lines)
        assert "### SampleModel" in text
        assert "| Field | Type | Required | Constraints | Description |" in text

    def test_table_rows(self):
        """Each field appears as a table row."""
        lines = gen_dd.generate_model_table("SampleModel", _SampleModel, "")
        text = "\n".join(lines)
        assert "`id`" in text
        assert "`name`" in text
        assert "`score`" in text

    def test_docstring_rendered(self):
        """Model docstring appears as italicised text."""
        lines = gen_dd.generate_model_table("SampleModel", _SampleModel, "A sample.")
        text = "\n".join(lines)
        assert "_A sample._" in text


# ---------------------------------------------------------------------------
# Tests for generate_data_dictionary (integration)
# ---------------------------------------------------------------------------


class TestGenerateDataDictionary:
    """Integration tests for the full generator."""

    def test_output_contains_all_sections(self):
        """Generated output contains Silver and Gold layer sections."""
        content = gen_dd.generate_data_dictionary()
        assert "# Data Dictionary" in content
        assert "## Common Models" in content
        assert "## Silver Layer Models" in content
        assert "## Gold Layer Models" in content

    def test_output_contains_key_models(self):
        """All expected models appear in the output."""
        content = gen_dd.generate_data_dictionary()
        assert "### DataLineage" in content
        assert "### PlayerStats" in content
        assert "### TeamStats" in content
        assert "### GameStats" in content
        assert "### GoldPlayerDailyStats" in content
        assert "### GoldPlayerSeasonSummary" in content
        assert "### GoldTeamDailyStats" in content

    def test_output_contains_auto_generated_notice(self):
        """Output includes the auto-generated notice."""
        content = gen_dd.generate_data_dictionary()
        assert "Auto-generated" in content
        assert "Do not edit manually" in content

    def test_output_is_valid_markdown_tables(self):
        """Output contains properly formatted Markdown tables."""
        content = gen_dd.generate_data_dictionary()
        assert "| Field | Type | Required | Constraints | Description |" in content
        assert "|-------|------|----------|-------------|-------------|" in content

    def test_known_fields_present(self):
        """Spot-check that known fields from the models are present."""
        content = gen_dd.generate_data_dictionary()
        # Silver
        assert "`player_id`" in content
        assert "`team_name`" in content
        assert "`game_id`" in content
        # Gold
        assert "`efficiency_rating`" in content
        assert "`true_shooting_percentage`" in content
        assert "`offensive_rating`" in content


# ---------------------------------------------------------------------------
# Tests for main (CLI)
# ---------------------------------------------------------------------------


class TestMain:
    """Tests for the main CLI entry point."""

    def test_writes_output_file(self, tmp_path):
        """main() writes the Data Dictionary to the specified output path."""
        output = tmp_path / "DATA_DICTIONARY.md"
        with patch("sys.argv", ["prog", "--output", str(output)]):
            result = gen_dd.main()
        assert result == 0
        assert output.exists()
        content = output.read_text()
        assert "# Data Dictionary" in content

    def test_default_output_path(self, tmp_path, monkeypatch):
        """Without --output, main() uses the default docs-src/ location."""
        # Redirect to tmp_path by patching __file__ resolution
        with patch("sys.argv", ["prog", "--output", str(tmp_path / "out.md")]):
            result = gen_dd.main()
        assert result == 0
