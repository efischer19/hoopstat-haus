#!/usr/bin/env python3
"""
Database schema documentation generator for Hoopstat Haus.

Reads the DuckDB and SQLite DDL files from apps/db-compiler/schema/ and
generates a Markdown data dictionary section suitable for inclusion in
docs-src/DATABASE_GUIDE.md.

Usage:
    python scripts/generate-db-schema-docs.py [--output PATH]
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def _parse_columns(ddl: str, table_name: str) -> list[dict]:
    """Extract column definitions from a CREATE TABLE block."""
    pattern = (
        rf"CREATE TABLE IF NOT EXISTS {re.escape(table_name)}\s*\((.*?)\);"
    )
    match = re.search(pattern, ddl, re.DOTALL)
    if not match:
        return []

    body = match.group(1)
    columns = []

    for line in body.split("\n"):
        line = line.strip()
        if not line or line.startswith("--") or line.startswith("PRIMARY KEY"):
            continue

        # Match column definitions: name TYPE [NOT NULL], -- comment
        col_match = re.match(
            r"(\w+)\s+([\w()]+)(\s+NOT NULL)?\s*,?\s*(?:--\s*(.*))?$",
            line,
        )
        if col_match:
            columns.append(
                {
                    "name": col_match.group(1),
                    "type": col_match.group(2),
                    "nullable": col_match.group(3) is None,
                    "description": (col_match.group(4) or "").strip(),
                }
            )

    return columns


def _parse_tables(ddl: str) -> list[dict]:
    """Parse all CREATE TABLE statements from DDL text."""
    tables = []
    # Find table names
    for match in re.finditer(
        r"CREATE TABLE IF NOT EXISTS (\w+)", ddl
    ):
        table_name = match.group(1)
        columns = _parse_columns(ddl, table_name)
        tables.append({"name": table_name, "columns": columns})
    return tables


def _parse_indexes(ddl: str) -> list[dict]:
    """Parse all CREATE INDEX statements from DDL text."""
    indexes = []
    for match in re.finditer(
        r"CREATE INDEX IF NOT EXISTS (\w+)\s+ON\s+(\w+)\s+\(([^)]+)\)",
        ddl,
    ):
        indexes.append(
            {
                "name": match.group(1),
                "table": match.group(2),
                "columns": match.group(3).strip(),
            }
        )
    return indexes


def _parse_views(ddl: str) -> list[str]:
    """Parse view names from DDL text."""
    return re.findall(r"CREATE VIEW IF NOT EXISTS (\w+)", ddl)


def generate_schema_docs(duckdb_ddl: str, sqlite_ddl: str) -> str:
    """Generate Markdown schema documentation from DDL files."""
    duckdb_tables = _parse_tables(duckdb_ddl)
    sqlite_tables = _parse_tables(sqlite_ddl)
    duckdb_indexes = _parse_indexes(duckdb_ddl)
    duckdb_views = _parse_views(duckdb_ddl)
    sqlite_views = _parse_views(sqlite_ddl)

    # Build sqlite type lookup: table.column -> type
    sqlite_types = {}
    for table in sqlite_tables:
        for col in table["columns"]:
            sqlite_types[f"{table['name']}.{col['name']}"] = col["type"]

    lines = []
    lines.append("# Database Schema Reference")
    lines.append("")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(
        "> **Auto-generated** from DDL files in `apps/db-compiler/schema/`."
        " Do not edit manually."
    )
    lines.append(">")
    lines.append(f"> Last updated: {now}")
    lines.append("")

    # Tables summary
    lines.append("## Tables")
    lines.append("")
    lines.append("| Table | Description |")
    lines.append("|-------|-------------|")
    for table in duckdb_tables:
        lines.append(f"| `{table['name']}` | {len(table['columns'])} columns |")
    lines.append("")

    # Detailed tables
    for table in duckdb_tables:
        lines.append(f"### {table['name']}")
        lines.append("")
        lines.append(
            "| Column | DuckDB Type | SQLite Type | Nullable | Description |"
        )
        lines.append(
            "|--------|-------------|-------------|----------|-------------|"
        )
        for col in table["columns"]:
            key = f"{table['name']}.{col['name']}"
            sq_type = sqlite_types.get(key, col["type"])
            nullable = "Yes" if col["nullable"] else "NOT NULL"
            lines.append(
                f"| `{col['name']}` | {col['type']} | {sq_type}"
                f" | {nullable} | {col['description']} |"
            )
        lines.append("")

    # Indexes
    lines.append("## Indexes")
    lines.append("")
    lines.append("| Index | Table | Columns |")
    lines.append("|-------|-------|---------|")
    for idx in duckdb_indexes:
        lines.append(f"| `{idx['name']}` | {idx['table']} | `{idx['columns']}` |")
    lines.append("")

    # Views
    lines.append("## Views")
    lines.append("")
    lines.append("| View | DuckDB | SQLite |")
    lines.append("|------|--------|--------|")
    all_views = sorted(set(duckdb_views + sqlite_views))
    for view in all_views:
        in_duck = "✅" if view in duckdb_views else "❌"
        in_sqlite = "✅" if view in sqlite_views else "❌"
        lines.append(f"| `{view}` | {in_duck} | {in_sqlite} |")
    lines.append("")

    return "\n".join(lines)


def main():
    """Generate database schema documentation from DDL files."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate Markdown schema docs from DuckDB and SQLite DDL files."
        )
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: stdout)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    schema_dir = repo_root / "apps" / "db-compiler" / "schema"

    duckdb_ddl = (schema_dir / "duckdb_schema.sql").read_text()
    sqlite_ddl = (schema_dir / "sqlite_schema.sql").read_text()

    content = generate_schema_docs(duckdb_ddl, sqlite_ddl)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        print(f"Database schema docs generated -> {output_path}")
    else:
        print(content)

    return 0


if __name__ == "__main__":
    sys.exit(main())
