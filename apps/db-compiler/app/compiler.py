"""
Compiler: orchestrates the load-once / write-twice pipeline.

Ties together the fetcher, the two writers, and the validator into a single
compile_databases() call.  The GoldDataset is loaded from memory exactly once
and then written to both output formats sequentially.
"""

import logging
import os
from pathlib import Path

from app.duckdb_writer import write_duckdb
from app.fetcher import GoldDataset
from app.sqlite_writer import write_sqlite
from app.validator import ValidationResult, validate_duckdb, validate_sqlite

logger = logging.getLogger(__name__)

# Output filenames (both formats share the same base name)
DUCKDB_FILENAME = "nba_current_season.duckdb"
SQLITE_FILENAME = "nba_current_season.sqlite"


def compile_databases(
    dataset: GoldDataset,
    output_dir: str,
    formats: list[str] | None = None,
    schema_dir: Path | None = None,
) -> dict[str, ValidationResult]:
    """Compile Gold artifacts into DuckDB and/or SQLite database files.

    Loads data from *dataset* once and writes it to each requested format
    sequentially.  After writing, runs post-build validation smoke tests
    against each file.

    Args:
        dataset: In-memory Gold artifacts (loaded once by the caller).
        output_dir: Directory where output ``.duckdb`` / ``.sqlite`` files
            will be written.  Created if it does not already exist.
        formats: Which formats to compile.  Accepts any combination of
            ``["duckdb", "sqlite"]``.  Defaults to both.
        schema_dir: Override path to the schema directory.  Defaults to the
            ``schema/`` directory next to the ``app/`` package.

    Returns:
        A dict mapping format name (``"duckdb"`` / ``"sqlite"``) to its
        :class:`~app.validator.ValidationResult`.
    """
    if formats is None:
        formats = ["duckdb", "sqlite"]

    os.makedirs(output_dir, exist_ok=True)

    results: dict[str, ValidationResult] = {}

    if "duckdb" in formats:
        duckdb_path = str(Path(output_dir) / DUCKDB_FILENAME)
        write_duckdb(dataset, duckdb_path, schema_dir=schema_dir)
        results["duckdb"] = validate_duckdb(duckdb_path)

    if "sqlite" in formats:
        sqlite_path = str(Path(output_dir) / SQLITE_FILENAME)
        write_sqlite(dataset, sqlite_path, schema_dir=schema_dir)
        results["sqlite"] = validate_sqlite(sqlite_path)

    # Cross-format record-count parity check (logged only — not a hard error)
    if "duckdb" in results and "sqlite" in results:
        duck_counts = results["duckdb"].table_counts()
        sqlite_counts = results["sqlite"].table_counts()
        for table, duck_n in duck_counts.items():
            sqlite_n = sqlite_counts.get(table)
            if duck_n != sqlite_n:
                logger.warning(
                    "Record count mismatch in '%s': DuckDB=%s, SQLite=%s",
                    table,
                    duck_n,
                    sqlite_n,
                )
            else:
                logger.debug("Record count OK '%s': %s rows", table, duck_n)

    return results
