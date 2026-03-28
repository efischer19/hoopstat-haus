"""Tests for the fetcher module."""

from pathlib import Path

import pytest

from app.fetcher import (
    GoldDataset,
    _extract_fields,
    _parse_top_list,
    load_from_local_dir,
    load_from_s3,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestExtractFields:
    """Unit tests for _extract_fields helper."""

    def test_returns_only_requested_columns(self):
        data = {"a": 1, "b": 2, "c": 3, "extra": 99}
        result = _extract_fields(data, ["a", "b"])
        assert result == {"a": 1, "b": 2}

    def test_missing_keys_default_to_none(self):
        data = {"a": 1}
        result = _extract_fields(data, ["a", "b", "c"])
        assert result == {"a": 1, "b": None, "c": None}

    def test_empty_data(self):
        result = _extract_fields({}, ["x", "y"])
        assert result == {"x": None, "y": None}


class TestParseTopList:
    """Unit tests for _parse_top_list helper."""

    def test_flattens_players_into_rows(self):
        data = {
            "metric": "Points Leaders",
            "date": "2024-01-15",
            "players": [
                {
                    "rank": 1,
                    "player_id": "AAA",
                    "player_name": "Alice",
                    "team": "T1",
                    "value": 30.0,
                },
                {
                    "rank": 2,
                    "player_id": "BBB",
                    "player_name": "Bob",
                    "team": "T2",
                    "value": 25.0,
                },
            ],
        }
        rows = _parse_top_list(data)
        assert len(rows) == 2
        assert rows[0]["metric"] == "Points Leaders"
        assert rows[0]["list_date"] == "2024-01-15"
        assert rows[0]["rank"] == 1
        assert rows[0]["value"] == 30.0
        assert rows[1]["player_id"] == "BBB"

    def test_empty_players_returns_empty_list(self):
        data = {"metric": "Assists", "date": "2024-01-15", "players": []}
        assert _parse_top_list(data) == []

    def test_missing_keys_default_to_none(self):
        data = {"players": [{"rank": 1}]}
        rows = _parse_top_list(data)
        assert rows[0]["metric"] == ""
        assert rows[0]["list_date"] == ""
        assert rows[0]["player_id"] is None


class TestGoldDatasetSummary:
    """Unit tests for GoldDataset.summary()."""

    def test_summary_reports_all_counts(self):
        ds = GoldDataset(
            player_daily_stats=[{}, {}],
            team_daily_stats=[{}],
            player_season_summary=[{}, {}, {}],
            team_season_summary=[],
            top_lists=[{}, {}, {}, {}],
        )
        summary = ds.summary()
        assert "player_daily=2" in summary
        assert "team_daily=1" in summary
        assert "player_season=3" in summary
        assert "team_season=0" in summary
        assert "top_list_rows=4" in summary


class TestLoadFromLocalDir:
    """Tests for load_from_local_dir()."""

    def test_loads_player_daily_stats(self, fixtures_dir):
        dataset = load_from_local_dir(str(fixtures_dir))
        assert len(dataset.player_daily_stats) == 2

    def test_player_daily_fields_are_extracted(self, fixtures_dir):
        dataset = load_from_local_dir(str(fixtures_dir))
        player = next(p for p in dataset.player_daily_stats if p["player_id"] == "2544")
        assert player["player_name"] == "LeBron James"
        assert player["team"] == "LAL"
        assert player["points"] == 28
        assert player["season"] == "2024-25"

    def test_lineage_field_is_excluded(self, fixtures_dir):
        """Extra JSON fields like 'lineage' must not appear in dataset rows."""
        dataset = load_from_local_dir(str(fixtures_dir))
        for row in dataset.player_daily_stats:
            assert "lineage" not in row
            assert "partition_key" not in row

    def test_loads_team_daily_stats(self, fixtures_dir):
        dataset = load_from_local_dir(str(fixtures_dir))
        assert len(dataset.team_daily_stats) == 1
        team = dataset.team_daily_stats[0]
        assert team["team_id"] == "1610612747"
        assert team["win"] is True

    def test_loads_player_season_summary(self, fixtures_dir):
        dataset = load_from_local_dir(str(fixtures_dir))
        assert len(dataset.player_season_summary) == 2
        player = next(
            p for p in dataset.player_season_summary if p["player_id"] == "2544"
        )
        assert player["points_per_game"] == 24.5

    def test_loads_team_season_summary(self, fixtures_dir):
        dataset = load_from_local_dir(str(fixtures_dir))
        assert len(dataset.team_season_summary) == 1
        assert dataset.team_season_summary[0]["total_games"] == 82

    def test_loads_and_flattens_top_lists(self, fixtures_dir):
        dataset = load_from_local_dir(str(fixtures_dir))
        # 2 files × 2 players each = 4 rows
        assert len(dataset.top_lists) == 4
        metrics = {row["metric"] for row in dataset.top_lists}
        assert "Points Leaders" in metrics
        assert "Assists Leaders" in metrics

    def test_skips_corrupt_json_files(self, tmp_path):
        """Corrupt JSON files should be skipped with a warning, not crash."""
        bad_dir = tmp_path / "player_daily" / "2024-01-15"
        bad_dir.mkdir(parents=True)
        (bad_dir / "bad.json").write_text("{not valid json}")
        dataset = load_from_local_dir(str(tmp_path))
        # Should not raise; corrupt file is skipped
        assert isinstance(dataset, GoldDataset)

    def test_empty_directory_returns_empty_dataset(self, tmp_path):
        dataset = load_from_local_dir(str(tmp_path))
        assert dataset.player_daily_stats == []
        assert dataset.team_daily_stats == []
        assert dataset.player_season_summary == []
        assert dataset.team_season_summary == []
        assert dataset.top_lists == []


class TestLoadFromS3:
    """Tests for load_from_s3() using moto S3 mock."""

    @pytest.fixture
    def mock_s3_bucket(self):
        """Set up a mocked S3 bucket populated with fixture JSON artifacts."""
        from moto import mock_aws

        with mock_aws():
            import boto3

            s3 = boto3.client("s3", region_name="us-east-1")
            s3.create_bucket(Bucket="test-gold-bucket")

            # Upload fixture files mirroring the served/ prefix structure
            for fixture_file in FIXTURES_DIR.rglob("*.json"):
                relative = fixture_file.relative_to(FIXTURES_DIR)
                # Skip the index file — not part of any served/ prefix
                if str(relative).startswith("index"):
                    continue
                s3_key = f"served/{relative}"
                s3.put_object(
                    Bucket="test-gold-bucket",
                    Key=s3_key,
                    Body=fixture_file.read_bytes(),
                )
            yield s3

    def test_loads_player_daily_stats(self, mock_s3_bucket):
        dataset = load_from_s3("test-gold-bucket", aws_region="us-east-1")
        assert len(dataset.player_daily_stats) == 2

    def test_loads_team_daily_stats(self, mock_s3_bucket):
        dataset = load_from_s3("test-gold-bucket", aws_region="us-east-1")
        assert len(dataset.team_daily_stats) == 1

    def test_loads_player_season_summary(self, mock_s3_bucket):
        dataset = load_from_s3("test-gold-bucket", aws_region="us-east-1")
        assert len(dataset.player_season_summary) == 2

    def test_loads_team_season_summary(self, mock_s3_bucket):
        dataset = load_from_s3("test-gold-bucket", aws_region="us-east-1")
        assert len(dataset.team_season_summary) == 1

    def test_loads_top_lists_flattened(self, mock_s3_bucket):
        dataset = load_from_s3("test-gold-bucket", aws_region="us-east-1")
        assert len(dataset.top_lists) == 4

    def test_season_filter_applied_to_season_artifacts(self, mock_s3_bucket):
        """Season filter narrows season_player/ and season_team/ prefixes."""
        dataset = load_from_s3(
            "test-gold-bucket", season="2024-25", aws_region="us-east-1"
        )
        assert len(dataset.player_season_summary) == 2

    def test_season_filter_excludes_other_seasons(self, mock_s3_bucket):
        """Non-existent season filter should return empty season artifacts."""
        dataset = load_from_s3(
            "test-gold-bucket", season="1999-00", aws_region="us-east-1"
        )
        assert dataset.player_season_summary == []
        assert dataset.team_season_summary == []
        # Daily artifacts are unaffected by season filter
        assert len(dataset.player_daily_stats) == 2

    def test_lineage_excluded_from_s3_data(self, mock_s3_bucket):
        dataset = load_from_s3("test-gold-bucket", aws_region="us-east-1")
        for row in dataset.player_daily_stats:
            assert "lineage" not in row
