"""Tests for the compiler module."""

from pathlib import Path

from app.compiler import DUCKDB_FILENAME, SQLITE_FILENAME, compile_databases
from app.fetcher import GoldDataset


class TestCompileDatabases:
    """Tests for compile_databases()."""

    def test_both_formats_created_by_default(self, sample_dataset, tmp_path):
        results = compile_databases(sample_dataset, str(tmp_path))

        assert (tmp_path / DUCKDB_FILENAME).exists()
        assert (tmp_path / SQLITE_FILENAME).exists()
        assert "duckdb" in results
        assert "sqlite" in results

    def test_duckdb_only_format(self, sample_dataset, tmp_path):
        results = compile_databases(sample_dataset, str(tmp_path), formats=["duckdb"])

        assert (tmp_path / DUCKDB_FILENAME).exists()
        assert not (tmp_path / SQLITE_FILENAME).exists()
        assert "duckdb" in results
        assert "sqlite" not in results

    def test_sqlite_only_format(self, sample_dataset, tmp_path):
        results = compile_databases(sample_dataset, str(tmp_path), formats=["sqlite"])

        assert not (tmp_path / DUCKDB_FILENAME).exists()
        assert (tmp_path / SQLITE_FILENAME).exists()
        assert "sqlite" in results
        assert "duckdb" not in results

    def test_output_dir_is_created_if_missing(self, sample_dataset, tmp_path):
        new_dir = str(tmp_path / "nested" / "output")
        compile_databases(sample_dataset, new_dir)

        assert (Path(new_dir) / DUCKDB_FILENAME).exists()
        assert (Path(new_dir) / SQLITE_FILENAME).exists()

    def test_validation_passes_for_both_formats(self, sample_dataset, tmp_path):
        results = compile_databases(sample_dataset, str(tmp_path))

        assert results["duckdb"].failed == 0
        assert results["sqlite"].failed == 0

    def test_record_counts_match_between_formats(self, sample_dataset, tmp_path):
        """DuckDB and SQLite must contain the same row counts for every table."""
        results = compile_databases(sample_dataset, str(tmp_path))

        duck_counts = results["duckdb"].table_counts()
        sqlite_counts = results["sqlite"].table_counts()

        for table in duck_counts:
            assert duck_counts[table] == sqlite_counts.get(table), (
                f"Count mismatch for {table}: "
                f"DuckDB={duck_counts[table]}, SQLite={sqlite_counts.get(table)}"
            )

    def test_empty_dataset_compiles_without_error(self, tmp_path):
        results = compile_databases(GoldDataset(), str(tmp_path))

        assert results["duckdb"].failed == 0
        assert results["sqlite"].failed == 0

    def test_default_formats_includes_both(self, sample_dataset, tmp_path):
        """When formats is None, both duckdb and sqlite should be compiled."""
        results = compile_databases(sample_dataset, str(tmp_path), formats=None)

        assert "duckdb" in results
        assert "sqlite" in results
