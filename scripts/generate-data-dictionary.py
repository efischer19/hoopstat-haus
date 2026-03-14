#!/usr/bin/env python3
"""
Data Dictionary generation script for Hoopstat Haus.

Imports Pydantic schemas (silver_models.py, gold_models.py) and extracts
field names, types, and descriptions into a clean Markdown Data Dictionary.

Usage:
    python scripts/generate-data-dictionary.py [--output PATH]
"""

import argparse
import importlib.util
import sys
import types
from datetime import datetime, timezone
from pathlib import Path
from typing import Union, get_args, get_origin


def _load_module_from_file(module_name: str, file_path: Path):
    """Load a Python module directly from a file path, bypassing __init__.py."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def get_type_name(annotation) -> str:
    """Convert a type annotation to a readable string."""
    if annotation is type(None):
        return "None"

    origin = get_origin(annotation)

    # Handle Union types (str | None, etc.)
    if origin is Union or origin is types.UnionType:
        args = get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        has_none = len(non_none) < len(args)
        type_strs = [get_type_name(a) for a in non_none]
        result = " | ".join(type_strs)
        if has_none:
            result += " | None"
        return result

    # Handle generic types like list[str], dict[str, Any]
    if origin is not None:
        args = get_args(annotation)
        if args:
            arg_strs = ", ".join(get_type_name(a) for a in args)
            origin_name = getattr(origin, "__name__", str(origin))
            return f"{origin_name}[{arg_strs}]"
        return getattr(origin, "__name__", str(origin))

    # Handle basic types and model classes
    if hasattr(annotation, "__name__"):
        return annotation.__name__

    return str(annotation)


def get_constraints(field_info) -> str:
    """Extract validation constraints from a Pydantic FieldInfo."""
    constraints = []
    for attr in ("ge", "gt", "le", "lt", "min_length", "max_length", "pattern"):
        value = getattr(field_info, attr, None)
        if value is not None:
            constraints.append(f"{attr}={value}")

    # Check metadata for additional constraints
    if hasattr(field_info, "metadata"):
        for meta in field_info.metadata:
            if hasattr(meta, "ge") and meta.ge is not None:
                if f"ge={meta.ge}" not in constraints:
                    constraints.append(f"ge={meta.ge}")
            if hasattr(meta, "le") and meta.le is not None:
                if f"le={meta.le}" not in constraints:
                    constraints.append(f"le={meta.le}")
            if hasattr(meta, "gt") and meta.gt is not None:
                if f"gt={meta.gt}" not in constraints:
                    constraints.append(f"gt={meta.gt}")
            if hasattr(meta, "lt") and meta.lt is not None:
                if f"lt={meta.lt}" not in constraints:
                    constraints.append(f"lt={meta.lt}")

    return ", ".join(constraints) if constraints else "--"


def extract_model_fields(model_class) -> list[dict]:
    """Extract field information from a Pydantic model class."""
    fields = []
    for name, field_info in model_class.model_fields.items():
        fields.append(
            {
                "name": name,
                "type": get_type_name(field_info.annotation),
                "required": field_info.is_required(),
                "constraints": get_constraints(field_info),
                "description": field_info.description or "--",
            }
        )
    return fields


def generate_model_table(model_name: str, model_class, docstring: str) -> list[str]:
    """Generate a Markdown table for a single model."""
    lines = []
    lines.append(f"### {model_name}")
    lines.append("")
    if docstring:
        lines.append(f"_{docstring}_")
        lines.append("")

    fields = extract_model_fields(model_class)
    if not fields:
        lines.append("_No fields defined._")
        lines.append("")
        return lines

    # Table header
    lines.append("| Field | Type | Required | Constraints | Description |")
    lines.append("|-------|------|----------|-------------|-------------|")

    for f in fields:
        required = "Yes" if f["required"] else "No"
        lines.append(
            f"| `{f['name']}` | `{f['type']}` | {required} "
            f"| {f['constraints']} | {f['description']} |"
        )

    lines.append("")
    return lines


def generate_data_dictionary() -> str:
    """Generate the full Data Dictionary as a Markdown string."""
    repo_root = Path(__file__).resolve().parent.parent
    models_dir = repo_root / "libs" / "hoopstat-data" / "hoopstat_data"

    # Load model modules directly to avoid importing the full package
    # (which pulls in heavy dependencies like fuzzywuzzy, pandas, etc.)
    silver_mod = _load_module_from_file(
        "hoopstat_data.silver_models", models_dir / "silver_models.py"
    )
    gold_mod = _load_module_from_file(
        "hoopstat_data.gold_models", models_dir / "gold_models.py"
    )

    DataLineage = silver_mod.DataLineage
    PlayerStats = silver_mod.PlayerStats
    TeamStats = silver_mod.TeamStats
    GameStats = silver_mod.GameStats
    GoldPlayerDailyStats = gold_mod.GoldPlayerDailyStats
    GoldPlayerSeasonSummary = gold_mod.GoldPlayerSeasonSummary
    GoldTeamDailyStats = gold_mod.GoldTeamDailyStats

    lines = []

    # Header
    lines.append("# Data Dictionary")
    lines.append("")
    lines.append(
        "> **Auto-generated** from Pydantic model definitions. Do not edit manually."
    )
    lines.append(">")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"> Last updated: {now}")
    lines.append("")

    lines.append("## Overview")
    lines.append("")
    lines.append(
        "This document describes all data models used in the Hoopstat Haus "
        "medallion data architecture. Models are organized by layer:"
    )
    lines.append("")
    lines.append(
        "- **Common Models** -- Shared types used across layers "
        "(e.g., data lineage tracking)"
    )
    lines.append(
        "- **Silver Layer** -- Cleaned and validated data models "
        "from the Bronze-to-Silver ETL"
    )
    lines.append(
        "- **Gold Layer** -- Analytics-ready models with pre-computed "
        "metrics from the Silver-to-Gold ETL"
    )
    lines.append("")

    # ---- Common Models ----
    lines.append("---")
    lines.append("")
    lines.append("## Common Models")
    lines.append("")
    lines.extend(
        generate_model_table(
            "DataLineage",
            DataLineage,
            DataLineage.__doc__.strip() if DataLineage.__doc__ else "",
        )
    )

    # ---- Silver Layer ----
    lines.append("---")
    lines.append("")
    lines.append("## Silver Layer Models")
    lines.append("")
    lines.append(
        "Cleaned and standardized models produced by the Bronze-to-Silver ETL pipeline."
    )
    lines.append("")

    silver_models = [
        ("PlayerStats", PlayerStats),
        ("TeamStats", TeamStats),
        ("GameStats", GameStats),
    ]
    for name, model in silver_models:
        doc = model.__doc__.strip() if model.__doc__ else ""
        lines.extend(generate_model_table(name, model, doc))

    # ---- Gold Layer ----
    lines.append("---")
    lines.append("")
    lines.append("## Gold Layer Models")
    lines.append("")
    lines.append(
        "Analytics-ready models with pre-computed metrics produced by "
        "the Silver-to-Gold ETL pipeline."
    )
    lines.append("")

    gold_models = [
        ("GoldPlayerDailyStats", GoldPlayerDailyStats),
        ("GoldPlayerSeasonSummary", GoldPlayerSeasonSummary),
        ("GoldTeamDailyStats", GoldTeamDailyStats),
    ]
    for name, model in gold_models:
        doc = model.__doc__.strip() if model.__doc__ else ""
        lines.extend(generate_model_table(name, model, doc))

    return "\n".join(lines)


def main():
    """Generate the Data Dictionary and write to file."""
    parser = argparse.ArgumentParser(
        description="Generate a Markdown Data Dictionary from Pydantic models."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: docs-src/DATA_DICTIONARY.md)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    output_path = (
        Path(args.output)
        if args.output
        else repo_root / "docs-src" / "DATA_DICTIONARY.md"
    )

    content = generate_data_dictionary()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    print(f"Data Dictionary generated -> {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
