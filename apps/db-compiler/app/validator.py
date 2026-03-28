"""
Validator: post-build smoke-test queries for DuckDB and SQLite databases.

Runs a fixed set of checks against a freshly compiled database and returns
a structured ValidationResult.  The checks are designed to verify:

  - All five tables exist and are queryable.
  - Counts are non-negative (basic structural integrity).
  - Views are queryable without errors.

A failed check means the query raised an exception, not that a particular
count threshold was violated.  Record-count parity between the two formats
is verified in the calling code (compiler.py / main.py).
"""

import logging
import sqlite3
from dataclasses import dataclass, field

import duckdb

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    """Result of a single smoke-test query."""

    name: str
    status: str  # "pass" or "fail"
    value: int | None = None
    error: str | None = None


@dataclass
class ValidationResult:
    """Aggregated result of all smoke-test checks for one database format."""

    format: str  # "duckdb" or "sqlite"
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.status == "pass")

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c.status == "fail")

    def table_counts(self) -> dict[str, int | None]:
        """Return {table_name: row_count} for the five core tables."""
        tables = [
            "player_daily_stats",
            "team_daily_stats",
            "player_season_summary",
            "team_season_summary",
            "top_lists",
        ]
        counts: dict[str, int | None] = {}
        for check in self.checks:
            for table in tables:
                if check.name == f"count_{table}":
                    counts[table] = check.value
        return counts


# ---------------------------------------------------------------------------
# Smoke-test query definitions (same logical checks for both engines)
# ---------------------------------------------------------------------------

_COUNT_CHECKS: list[tuple[str, str]] = [
    ("count_player_daily_stats", "SELECT COUNT(*) FROM player_daily_stats"),
    ("count_team_daily_stats", "SELECT COUNT(*) FROM team_daily_stats"),
    ("count_player_season_summary", "SELECT COUNT(*) FROM player_season_summary"),
    ("count_team_season_summary", "SELECT COUNT(*) FROM team_season_summary"),
    ("count_top_lists", "SELECT COUNT(*) FROM top_lists"),
]

_VIEW_CHECKS: list[tuple[str, str]] = [
    ("view_v_team_standings", "SELECT COUNT(*) FROM v_team_standings"),
    (
        "view_v_player_current_averages",
        "SELECT COUNT(*) FROM v_player_current_averages",
    ),
]


def validate_duckdb(path: str) -> ValidationResult:
    """Run smoke-test queries against a DuckDB database file.

    Args:
        path: Path to the ``.duckdb`` file.

    Returns:
        ValidationResult with pass/fail status for each check.
    """
    result = ValidationResult(format="duckdb")
    conn = duckdb.connect(path, read_only=True)
    try:
        for name, query in _COUNT_CHECKS + _VIEW_CHECKS:
            try:
                row = conn.execute(query).fetchone()
                count = row[0] if row else 0
                result.checks.append(CheckResult(name=name, status="pass", value=count))
                logger.debug("DuckDB check '%s': %s rows", name, count)
            except Exception as exc:
                result.checks.append(
                    CheckResult(name=name, status="fail", error=str(exc))
                )
                logger.warning("DuckDB check '%s' FAILED: %s", name, exc)
    finally:
        conn.close()

    logger.info(
        "DuckDB validation complete — %d passed, %d failed",
        result.passed,
        result.failed,
    )
    return result


def validate_sqlite(path: str) -> ValidationResult:
    """Run smoke-test queries against a SQLite database file.

    Args:
        path: Path to the ``.sqlite`` file.

    Returns:
        ValidationResult with pass/fail status for each check.
    """
    result = ValidationResult(format="sqlite")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        cursor = conn.cursor()
        for name, query in _COUNT_CHECKS + _VIEW_CHECKS:
            try:
                cursor.execute(query)
                row = cursor.fetchone()
                count = row[0] if row else 0
                result.checks.append(CheckResult(name=name, status="pass", value=count))
                logger.debug("SQLite check '%s': %s rows", name, count)
            except Exception as exc:
                result.checks.append(
                    CheckResult(name=name, status="fail", error=str(exc))
                )
                logger.warning("SQLite check '%s' FAILED: %s", name, exc)
    finally:
        conn.close()

    logger.info(
        "SQLite validation complete — %d passed, %d failed",
        result.passed,
        result.failed,
    )
    return result
