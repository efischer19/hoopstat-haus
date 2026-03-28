"""
DuckDB writer: creates a .duckdb file from an in-memory GoldDataset.

Schema DDL is loaded from schema/duckdb_schema.sql so that the database
structure stays in sync with the canonical schema definitions.
"""

import logging
from pathlib import Path

import duckdb

from app.fetcher import (
    PLAYER_DAILY_COLUMNS,
    PLAYER_SEASON_COLUMNS,
    TEAM_DAILY_COLUMNS,
    TEAM_SEASON_COLUMNS,
    TOP_LISTS_COLUMNS,
    GoldDataset,
)

logger = logging.getLogger(__name__)

# Default schema directory — sibling of the app/ package directory.
_SCHEMA_DIR = Path(__file__).parent.parent / "schema"


def _execute_schema(conn: duckdb.DuckDBPyConnection, schema_path: Path) -> None:
    """Execute all DDL statements from a SQL schema file.

    Processes the file line-by-line so that semicolons inside ``--`` comments
    are not treated as statement terminators.  Each complete statement
    (terminated by a ``;`` on a non-comment portion of a line) is executed
    individually against the DuckDB connection.
    """
    sql = schema_path.read_text()
    current: list[str] = []

    for line in sql.split("\n"):
        # Determine the part of the line that is not inside a -- comment.
        comment_pos = line.find("--")
        code_part = line[:comment_pos] if comment_pos >= 0 else line

        current.append(line)

        if ";" in code_part:
            stmt = "\n".join(current).strip()
            if stmt:
                conn.execute(stmt)
            current = []

    # Execute any trailing statement that lacks a terminating semicolon.
    remaining = "\n".join(current).strip()
    if remaining:
        conn.execute(remaining)


def _insert_rows(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    columns: list[str],
    rows: list[dict],
) -> int:
    """Bulk-insert rows into *table* using parameterised ``INSERT OR REPLACE``.

    Returns the number of rows inserted.  Does nothing and returns 0 when
    *rows* is empty.
    """
    if not rows:
        return 0

    col_list = ", ".join(columns)
    placeholders = ", ".join(["?" for _ in columns])
    sql = f"INSERT OR REPLACE INTO {table} ({col_list}) VALUES ({placeholders})"

    # Build a list of positional value tuples matching *columns* order.
    values = [[row.get(col) for col in columns] for row in rows]
    conn.executemany(sql, values)
    return len(values)


def write_duckdb(
    dataset: GoldDataset,
    output_path: str,
    schema_dir: Path | None = None,
) -> None:
    """Write a DuckDB database file from the in-memory dataset.

    1. Creates (or overwrites) the file at *output_path*.
    2. Runs all DDL from ``duckdb_schema.sql`` to create tables, indexes,
       and views.
    3. Inserts data from *dataset* into each table.

    Args:
        dataset: In-memory Gold artifacts to persist.
        output_path: Destination path for the ``.duckdb`` file.
        schema_dir: Directory containing ``duckdb_schema.sql``.
            Defaults to the ``schema/`` directory next to this package.
    """
    resolved_schema_dir = Path(schema_dir) if schema_dir else _SCHEMA_DIR
    schema_path = resolved_schema_dir / "duckdb_schema.sql"

    logger.info("Writing DuckDB database → %s", output_path)

    conn = duckdb.connect(output_path)
    try:
        _execute_schema(conn, schema_path)

        counts = {
            "player_daily_stats": _insert_rows(
                conn,
                "player_daily_stats",
                PLAYER_DAILY_COLUMNS,
                dataset.player_daily_stats,
            ),
            "team_daily_stats": _insert_rows(
                conn,
                "team_daily_stats",
                TEAM_DAILY_COLUMNS,
                dataset.team_daily_stats,
            ),
            "player_season_summary": _insert_rows(
                conn,
                "player_season_summary",
                PLAYER_SEASON_COLUMNS,
                dataset.player_season_summary,
            ),
            "team_season_summary": _insert_rows(
                conn,
                "team_season_summary",
                TEAM_SEASON_COLUMNS,
                dataset.team_season_summary,
            ),
            "top_lists": _insert_rows(
                conn,
                "top_lists",
                TOP_LISTS_COLUMNS,
                dataset.top_lists,
            ),
        }

        logger.info("DuckDB write complete: %s", counts)
    finally:
        conn.close()
