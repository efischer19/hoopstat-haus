"""
SQLite writer: creates a .sqlite file from an in-memory GoldDataset.

Schema DDL is loaded from schema/sqlite_schema.sql so that the database
structure stays in sync with the canonical schema definitions.
"""

import logging
import sqlite3
from pathlib import Path

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


def _insert_rows(
    cursor: sqlite3.Cursor,
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
    # Python booleans are automatically stored as 0/1 by sqlite3, which is
    # the correct representation for the INTEGER boolean columns in the schema.
    values = [[row.get(col) for col in columns] for row in rows]
    cursor.executemany(sql, values)
    return len(values)


def write_sqlite(
    dataset: GoldDataset,
    output_path: str,
    schema_dir: Path | None = None,
) -> None:
    """Write a SQLite database file from the in-memory dataset.

    1. Creates (or overwrites) the file at *output_path*.
    2. Runs all DDL from ``sqlite_schema.sql`` via ``executescript`` to create
       tables, indexes, and views.
    3. Inserts data from *dataset* into each table.

    Args:
        dataset: In-memory Gold artifacts to persist.
        output_path: Destination path for the ``.sqlite`` file.
        schema_dir: Directory containing ``sqlite_schema.sql``.
            Defaults to the ``schema/`` directory next to this package.
    """
    resolved_schema_dir = Path(schema_dir) if schema_dir else _SCHEMA_DIR
    schema_path = resolved_schema_dir / "sqlite_schema.sql"

    logger.info("Writing SQLite database → %s", output_path)

    conn = sqlite3.connect(output_path)
    try:
        cursor = conn.cursor()

        # executescript commits any open transaction and then runs all DDL
        # statements in the schema file atomically.
        cursor.executescript(schema_path.read_text())

        counts = {
            "player_daily_stats": _insert_rows(
                cursor,
                "player_daily_stats",
                PLAYER_DAILY_COLUMNS,
                dataset.player_daily_stats,
            ),
            "team_daily_stats": _insert_rows(
                cursor,
                "team_daily_stats",
                TEAM_DAILY_COLUMNS,
                dataset.team_daily_stats,
            ),
            "player_season_summary": _insert_rows(
                cursor,
                "player_season_summary",
                PLAYER_SEASON_COLUMNS,
                dataset.player_season_summary,
            ),
            "team_season_summary": _insert_rows(
                cursor,
                "team_season_summary",
                TEAM_SEASON_COLUMNS,
                dataset.team_season_summary,
            ),
            "top_lists": _insert_rows(
                cursor,
                "top_lists",
                TOP_LISTS_COLUMNS,
                dataset.top_lists,
            ),
        }

        conn.commit()
        logger.info("SQLite write complete: %s", counts)
    finally:
        conn.close()
