"""Tests for the validator module."""

from app.duckdb_writer import write_duckdb
from app.fetcher import GoldDataset
from app.sqlite_writer import write_sqlite
from app.validator import ValidationResult, validate_duckdb, validate_sqlite


class TestValidateDuckDB:
    """Tests for validate_duckdb()."""

    def test_all_checks_pass_with_populated_db(self, sample_dataset, tmp_path):
        path = str(tmp_path / "test.duckdb")
        write_duckdb(sample_dataset, path)

        result = validate_duckdb(path)

        assert result.format == "duckdb"
        assert result.failed == 0
        assert result.passed == len(result.checks)

    def test_returns_at_least_five_checks(self, sample_dataset, tmp_path):
        path = str(tmp_path / "test.duckdb")
        write_duckdb(sample_dataset, path)

        result = validate_duckdb(path)

        assert len(result.checks) >= 5

    def test_count_checks_report_correct_values(self, sample_dataset, tmp_path):
        path = str(tmp_path / "test.duckdb")
        write_duckdb(sample_dataset, path)

        result = validate_duckdb(path)
        counts = result.table_counts()

        assert counts["player_daily_stats"] == len(sample_dataset.player_daily_stats)
        assert counts["team_daily_stats"] == len(sample_dataset.team_daily_stats)
        assert counts["player_season_summary"] == len(
            sample_dataset.player_season_summary
        )
        assert counts["top_lists"] == len(sample_dataset.top_lists)

    def test_checks_pass_with_empty_dataset(self, tmp_path):
        """All queries should succeed even on an empty database."""
        path = str(tmp_path / "empty.duckdb")
        write_duckdb(GoldDataset(), path)

        result = validate_duckdb(path)
        assert result.failed == 0


class TestValidateSQLite:
    """Tests for validate_sqlite()."""

    def test_all_checks_pass_with_populated_db(self, sample_dataset, tmp_path):
        path = str(tmp_path / "test.sqlite")
        write_sqlite(sample_dataset, path)

        result = validate_sqlite(path)

        assert result.format == "sqlite"
        assert result.failed == 0
        assert result.passed == len(result.checks)

    def test_returns_at_least_five_checks(self, sample_dataset, tmp_path):
        path = str(tmp_path / "test.sqlite")
        write_sqlite(sample_dataset, path)

        result = validate_sqlite(path)

        assert len(result.checks) >= 5

    def test_count_checks_report_correct_values(self, sample_dataset, tmp_path):
        path = str(tmp_path / "test.sqlite")
        write_sqlite(sample_dataset, path)

        result = validate_sqlite(path)
        counts = result.table_counts()

        assert counts["player_daily_stats"] == len(sample_dataset.player_daily_stats)
        assert counts["team_daily_stats"] == len(sample_dataset.team_daily_stats)
        assert counts["player_season_summary"] == len(
            sample_dataset.player_season_summary
        )
        assert counts["top_lists"] == len(sample_dataset.top_lists)

    def test_checks_pass_with_empty_dataset(self, tmp_path):
        """All queries should succeed even on an empty database."""
        path = str(tmp_path / "empty.sqlite")
        write_sqlite(GoldDataset(), path)

        result = validate_sqlite(path)
        assert result.failed == 0


class TestValidationResult:
    """Unit tests for the ValidationResult dataclass."""

    def test_passed_count(self):
        from app.validator import CheckResult

        result = ValidationResult(
            format="duckdb",
            checks=[
                CheckResult(name="a", status="pass", value=10),
                CheckResult(name="b", status="fail", error="boom"),
                CheckResult(name="c", status="pass", value=0),
            ],
        )
        assert result.passed == 2
        assert result.failed == 1

    def test_table_counts_returns_known_tables(self):
        from app.validator import CheckResult

        result = ValidationResult(
            format="sqlite",
            checks=[
                CheckResult(name="count_player_daily_stats", status="pass", value=5),
                CheckResult(name="count_team_daily_stats", status="pass", value=2),
                CheckResult(name="view_v_team_standings", status="pass", value=1),
            ],
        )
        counts = result.table_counts()
        assert counts["player_daily_stats"] == 5
        assert counts["team_daily_stats"] == 2
        # view checks are not in table_counts
        assert "v_team_standings" not in counts
