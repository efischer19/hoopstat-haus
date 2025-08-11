"""Tests for the bronze layer ingester."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from app.config import BronzeIngestionConfig
from app.ingester import BronzeIngester


class TestBronzeIngester:
    """Test bronze layer ingestion orchestrator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=BronzeIngestionConfig)

        # Mock dependencies
        with patch("app.ingester.NBAAPIClient") as mock_nba_client_class:
            with patch("app.ingester.S3ParquetClient") as mock_s3_client_class:
                self.mock_nba_client = Mock()
                self.mock_s3_client = Mock()
                mock_nba_client_class.return_value = self.mock_nba_client
                mock_s3_client_class.return_value = self.mock_s3_client

                self.ingester = BronzeIngester(self.config)

    def test_ingest_for_date_no_games(self):
        """Test ingestion when no games exist for the date."""
        # Mock empty schedule
        self.mock_nba_client.get_schedule_for_date.return_value = pd.DataFrame()

        result = self.ingester.ingest_for_date("2024-07-15", dry_run=False)

        # Should only call schedule endpoint
        self.mock_nba_client.get_schedule_for_date.assert_called_once_with("2024-07-15")
        self.mock_nba_client.get_box_score.assert_not_called()
        self.mock_nba_client.get_play_by_play.assert_not_called()

        # Should not write anything to S3
        self.mock_s3_client.write_parquet.assert_not_called()

        # Should return zero counts
        assert result == {"schedule": 0, "box_score": 0, "play_by_play": 0}

    def test_ingest_for_date_with_games(self):
        """Test ingestion when games exist for the date."""
        # Mock schedule with games
        schedule_df = pd.DataFrame(
            {"GAME_ID": ["001", "002"], "TEAM_NAME": ["Lakers", "Celtics"]}
        )
        self.mock_nba_client.get_schedule_for_date.return_value = schedule_df

        # Mock box score data
        box_score_df = pd.DataFrame(
            {
                "GAME_ID": ["001", "001"],
                "PLAYER_NAME": ["LeBron", "AD"],
                "PTS": [25, 30],
            }
        )
        self.mock_nba_client.get_box_score.return_value = box_score_df

        # Mock play-by-play data
        pbp_df = pd.DataFrame(
            {
                "GAME_ID": ["001", "001", "001"],
                "EVENTNUM": [1, 2, 3],
                "DESCRIPTION": ["Shot", "Rebound", "Shot"],
            }
        )
        self.mock_nba_client.get_play_by_play.return_value = pbp_df

        result = self.ingester.ingest_for_date("2024-01-15", dry_run=False)

        # Should call all endpoints
        self.mock_nba_client.get_schedule_for_date.assert_called_once_with("2024-01-15")
        assert self.mock_nba_client.get_box_score.call_count == 2  # 2 games
        assert self.mock_nba_client.get_play_by_play.call_count == 2  # 2 games

        # Should write all data types to S3
        assert self.mock_s3_client.write_parquet.call_count == 3

        # Verify the write calls
        write_calls = self.mock_s3_client.write_parquet.call_args_list

        # Schedule write
        schedule_call = write_calls[0]
        assert schedule_call[0][1] == "schedule"  # entity
        assert schedule_call[0][2] == "2024-01-15"  # date

        # Box score write
        box_score_call = write_calls[1]
        assert box_score_call[0][1] == "box_score"
        assert box_score_call[0][2] == "2024-01-15"

        # Play-by-play write
        pbp_call = write_calls[2]
        assert pbp_call[0][1] == "play_by_play"
        assert pbp_call[0][2] == "2024-01-15"

        # Should return correct counts
        expected_records = {
            "schedule": 2,  # 2 teams/rows in schedule
            "box_score": 4,  # 2 games * 2 players each
            "play_by_play": 6,  # 2 games * 3 plays each
        }
        assert result == expected_records

    def test_ingest_for_date_dry_run(self):
        """Test ingestion in dry run mode doesn't write to S3."""
        # Mock schedule with games
        schedule_df = pd.DataFrame({"GAME_ID": ["001"], "TEAM_NAME": ["Lakers"]})
        self.mock_nba_client.get_schedule_for_date.return_value = schedule_df
        self.mock_nba_client.get_box_score.return_value = pd.DataFrame(
            {"PLAYER": ["LeBron"]}
        )
        self.mock_nba_client.get_play_by_play.return_value = pd.DataFrame(
            {"EVENT": ["Shot"]}
        )

        result = self.ingester.ingest_for_date("2024-01-15", dry_run=True)

        # Should fetch data but not write to S3
        self.mock_nba_client.get_schedule_for_date.assert_called_once()
        self.mock_nba_client.get_box_score.assert_called_once()
        self.mock_nba_client.get_play_by_play.assert_called_once()
        self.mock_s3_client.write_parquet.assert_not_called()

        # Should still return correct counts
        assert result["schedule"] == 1
        assert result["box_score"] == 1
        assert result["play_by_play"] == 1

    def test_ingest_for_date_partial_game_failure(self):
        """Test ingestion continues when individual games fail."""
        # Mock schedule with 2 games
        schedule_df = pd.DataFrame(
            {"GAME_ID": ["001", "002"], "TEAM_NAME": ["Lakers", "Celtics"]}
        )
        self.mock_nba_client.get_schedule_for_date.return_value = schedule_df

        # First game succeeds, second fails
        def box_score_side_effect(game_id):
            if game_id == "001":
                return pd.DataFrame({"PLAYER": ["LeBron"]})
            else:
                raise Exception("API Error")

        self.mock_nba_client.get_box_score.side_effect = box_score_side_effect
        self.mock_nba_client.get_play_by_play.side_effect = box_score_side_effect

        result = self.ingester.ingest_for_date("2024-01-15", dry_run=False)

        # Should continue processing despite partial failure
        assert self.mock_nba_client.get_box_score.call_count == 2
        assert result["schedule"] == 2  # Schedule should still be complete
        assert result["box_score"] == 1  # Only successful game
        assert result["play_by_play"] == 1  # Only successful game

    def test_ingest_for_date_schedule_fetch_failure(self):
        """Test ingestion fails when schedule fetch fails."""
        self.mock_nba_client.get_schedule_for_date.side_effect = Exception("API Error")

        with pytest.raises(ValueError, match="Schedule fetch failed"):
            self.ingester.ingest_for_date("2024-01-15")

    def test_extract_game_ids_standard_column(self):
        """Test game ID extraction with standard GAME_ID column."""
        schedule_df = pd.DataFrame(
            {
                "GAME_ID": ["001", "002", "001", "002"],  # Duplicates
                "TEAM_NAME": ["Lakers", "Celtics", "Lakers", "Celtics"],
            }
        )

        game_ids = self.ingester._extract_game_ids(schedule_df)

        assert set(game_ids) == {"001", "002"}
        assert len(game_ids) == 2  # Should be unique

    def test_extract_game_ids_missing_column(self):
        """Test game ID extraction when GAME_ID column is missing."""
        schedule_df = pd.DataFrame(
            {"TEAM_NAME": ["Lakers", "Celtics"], "SCORE": [100, 95]}
        )

        game_ids = self.ingester._extract_game_ids(schedule_df)

        assert game_ids == []

    def test_extract_game_ids_alternative_column(self):
        """Test game ID extraction with alternative column name."""
        schedule_df = pd.DataFrame(
            {
                "game_id": ["001", "002"],  # lowercase
                "TEAM_NAME": ["Lakers", "Celtics"],
            }
        )

        game_ids = self.ingester._extract_game_ids(schedule_df)

        assert game_ids == ["001", "002"]

    def test_check_existing_data(self):
        """Test checking for existing data files."""

        # Mock S3 responses
        def file_exists_side_effect(entity, date):
            return entity == "schedule"  # Only schedule exists

        self.mock_s3_client.file_exists.side_effect = file_exists_side_effect

        result = self.ingester.check_existing_data("2024-01-15")

        expected = {"schedule": True, "box_score": False, "play_by_play": False}
        assert result == expected

        # Should check all entity types
        assert self.mock_s3_client.file_exists.call_count == 3
