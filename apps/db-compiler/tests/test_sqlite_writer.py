"""Tests for the SQLite writer module."""

import sqlite3

from app.sqlite_writer import write_sqlite


class TestWriteSQLite:
    """Tests for write_sqlite()."""

    def test_creates_all_tables(self, sample_dataset, tmp_path):
        output_path = str(tmp_path / "test.sqlite")
        write_sqlite(sample_dataset, output_path)

        conn = sqlite3.connect(output_path)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()

        assert "player_daily_stats" in tables
        assert "team_daily_stats" in tables
        assert "player_season_summary" in tables
        assert "team_season_summary" in tables
        assert "top_lists" in tables

    def test_player_daily_stats_row_count(self, sample_dataset, tmp_path):
        output_path = str(tmp_path / "test.sqlite")
        write_sqlite(sample_dataset, output_path)

        conn = sqlite3.connect(output_path)
        count = conn.execute("SELECT COUNT(*) FROM player_daily_stats").fetchone()[0]
        conn.close()

        assert count == len(sample_dataset.player_daily_stats)

    def test_team_daily_stats_row_count(self, sample_dataset, tmp_path):
        output_path = str(tmp_path / "test.sqlite")
        write_sqlite(sample_dataset, output_path)

        conn = sqlite3.connect(output_path)
        count = conn.execute("SELECT COUNT(*) FROM team_daily_stats").fetchone()[0]
        conn.close()

        assert count == len(sample_dataset.team_daily_stats)

    def test_player_season_summary_row_count(self, sample_dataset, tmp_path):
        output_path = str(tmp_path / "test.sqlite")
        write_sqlite(sample_dataset, output_path)

        conn = sqlite3.connect(output_path)
        count = conn.execute("SELECT COUNT(*) FROM player_season_summary").fetchone()[0]
        conn.close()

        assert count == len(sample_dataset.player_season_summary)

    def test_top_lists_row_count(self, sample_dataset, tmp_path):
        output_path = str(tmp_path / "test.sqlite")
        write_sqlite(sample_dataset, output_path)

        conn = sqlite3.connect(output_path)
        count = conn.execute("SELECT COUNT(*) FROM top_lists").fetchone()[0]
        conn.close()

        assert count == len(sample_dataset.top_lists)

    def test_player_data_values_are_correct(self, sample_dataset, tmp_path):
        output_path = str(tmp_path / "test.sqlite")
        write_sqlite(sample_dataset, output_path)

        conn = sqlite3.connect(output_path)
        row = conn.execute(
            "SELECT player_name, points, season FROM player_daily_stats "
            "WHERE player_id = '2544'"
        ).fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "LeBron James"
        assert row[1] == 28
        assert row[2] == "2024-25"

    def test_boolean_fields_stored_as_integers(self, sample_dataset, tmp_path):
        """SQLite stores booleans as 0/1 integers."""
        output_path = str(tmp_path / "test.sqlite")
        write_sqlite(sample_dataset, output_path)

        conn = sqlite3.connect(output_path)
        row = conn.execute(
            "SELECT home_game, win FROM team_daily_stats WHERE team_id = '1610612747'"
        ).fetchone()
        conn.close()

        assert row is not None
        # Python True is stored as 1 in SQLite
        assert row[0] == 1
        assert row[1] == 1

    def test_creates_views(self, sample_dataset, tmp_path):
        output_path = str(tmp_path / "test.sqlite")
        write_sqlite(sample_dataset, output_path)

        conn = sqlite3.connect(output_path)
        views = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='view'"
            ).fetchall()
        }
        conn.close()

        assert "v_team_standings" in views
        assert "v_player_current_averages" in views

    def test_v_team_standings_is_queryable(self, sample_dataset, tmp_path):
        output_path = str(tmp_path / "test.sqlite")
        write_sqlite(sample_dataset, output_path)

        conn = sqlite3.connect(output_path)
        count = conn.execute("SELECT COUNT(*) FROM v_team_standings").fetchone()[0]
        conn.close()

        assert count >= 0

    def test_empty_dataset_produces_empty_tables(self, tmp_path):
        from app.fetcher import GoldDataset

        output_path = str(tmp_path / "empty.sqlite")
        write_sqlite(GoldDataset(), output_path)

        conn = sqlite3.connect(output_path)
        count = conn.execute("SELECT COUNT(*) FROM player_daily_stats").fetchone()[0]
        conn.close()

        assert count == 0

    def test_or_replace_handles_duplicate_keys(self, sample_dataset, tmp_path):
        """Writing the same dataset twice should not raise a duplicate key error."""
        output_path = str(tmp_path / "dup.sqlite")
        write_sqlite(sample_dataset, output_path)
        write_sqlite(sample_dataset, output_path)

        conn = sqlite3.connect(output_path)
        count = conn.execute("SELECT COUNT(*) FROM player_daily_stats").fetchone()[0]
        conn.close()

        assert count == len(sample_dataset.player_daily_stats)
