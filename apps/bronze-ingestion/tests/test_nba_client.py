"""Tests for the NBA API client."""

import time
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from app.config import BronzeIngestionConfig
from hoopstat_nba_ingestion import NBAAPIClient


class TestNBAAPIClient:
    """Test NBA API client functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=BronzeIngestionConfig)
        self.config.rate_limit_seconds = 1.0
        self.client = NBAAPIClient(self.config)

    def test_rate_limiting(self):
        """Test that rate limiting enforces delays between calls."""
        # First call should not sleep
        start_time = time.time()
        self.client.rate_limiter.wait_if_needed()
        first_call_time = time.time() - start_time
        assert first_call_time < 0.1  # Should be very fast

        # Second call should enforce rate limit
        start_time = time.time()
        self.client.rate_limiter.wait_if_needed()
        second_call_time = time.time() - start_time
        assert (
            second_call_time >= self.config.rate_limit_seconds * 0.9
        )  # Allow some tolerance

    @patch("hoopstat_nba_ingestion.nba_client.scoreboardv2.ScoreboardV2")
    def test_get_schedule_for_date_success(self, mock_scoreboard_class):
        """Test successful schedule retrieval."""
        # Mock NBA API response
        mock_scoreboard = Mock()
        mock_line_score = Mock()
        mock_df = pd.DataFrame(
            {"GAME_ID": ["001", "002"], "TEAM_NAME": ["Lakers", "Celtics"]}
        )
        mock_line_score.get_data_frame.return_value = mock_df
        mock_scoreboard.line_score = mock_line_score
        mock_scoreboard_class.return_value = mock_scoreboard

        # Test the method
        result = self.client.get_schedule_for_date("2024-01-15")

        # Verify API was called with correct date format
        mock_scoreboard_class.assert_called_once_with(game_date="01/15/2024")

        # Verify result
        assert len(result) == 2
        assert list(result["GAME_ID"]) == ["001", "002"]

    @patch("hoopstat_nba_ingestion.nba_client.scoreboardv2.ScoreboardV2")
    def test_get_schedule_for_date_no_games(self, mock_scoreboard_class):
        """Test schedule retrieval when no games exist."""
        # Mock empty response
        mock_scoreboard = Mock()
        mock_line_score = Mock()
        mock_line_score.get_data_frame.return_value = pd.DataFrame()
        mock_scoreboard.line_score = mock_line_score
        mock_scoreboard_class.return_value = mock_scoreboard

        result = self.client.get_schedule_for_date("2024-07-15")  # Off-season date

        assert len(result) == 0
        assert result.empty

    @patch("hoopstat_nba_ingestion.nba_client.scoreboardv2.ScoreboardV2")
    def test_get_schedule_for_date_api_error(self, mock_scoreboard_class):
        """Test schedule retrieval handles API errors."""
        # Mock API error
        mock_scoreboard_class.side_effect = Exception("API Error")

        with pytest.raises(ConnectionError, match="NBA API request failed"):
            self.client.get_schedule_for_date("2024-01-15")

    @patch("hoopstat_nba_ingestion.nba_client.boxscoretraditionalv2.BoxScoreTraditionalV2")
    def test_get_box_score_success(self, mock_boxscore_class):
        """Test successful box score retrieval."""
        # Mock NBA API response
        mock_boxscore = Mock()
        mock_player_stats = Mock()
        mock_df = pd.DataFrame(
            {
                "PLAYER_ID": [1, 2],
                "PLAYER_NAME": ["LeBron James", "Anthony Davis"],
                "PTS": [25, 30],
            }
        )
        mock_player_stats.get_data_frame.return_value = mock_df
        mock_boxscore.player_stats = mock_player_stats
        mock_boxscore_class.return_value = mock_boxscore

        result = self.client.get_box_score("0022400001")

        mock_boxscore_class.assert_called_once_with(game_id="0022400001")
        assert len(result) == 2
        assert "PLAYER_NAME" in result.columns

    @patch("hoopstat_nba_ingestion.nba_client.playbyplayv3.PlayByPlayV3")
    def test_get_play_by_play_success(self, mock_pbp_class):
        """Test successful play-by-play retrieval."""
        # Mock NBA API response
        mock_pbp = Mock()
        mock_plays = Mock()
        mock_df = pd.DataFrame(
            {
                "EVENTNUM": [1, 2, 3],
                "EVENTMSGTYPE": [1, 2, 1],
                "DESCRIPTION": ["Shot", "Rebound", "Shot"],
            }
        )
        mock_plays.get_data_frame.return_value = mock_df
        mock_pbp.plays = mock_plays
        mock_pbp_class.return_value = mock_pbp

        result = self.client.get_play_by_play("0022400001")

        mock_pbp_class.assert_called_once_with(game_id="0022400001")
        assert len(result) == 3
        assert "DESCRIPTION" in result.columns

    @patch("hoopstat_nba_ingestion.nba_client.boxscoretraditionalv2.BoxScoreTraditionalV2")
    def test_retry_mechanism(self, mock_boxscore_class):
        """Test that retry mechanism works for transient failures."""
        # First two calls fail, third succeeds
        mock_boxscore_class.side_effect = [
            ConnectionError("Network error"),
            TimeoutError("Timeout"),
            Mock(player_stats=Mock(get_data_frame=Mock(return_value=pd.DataFrame()))),
        ]

        # Should succeed after retries
        result = self.client.get_box_score("0022400001")

        # Verify it was called 3 times (2 failures + 1 success)
        assert mock_boxscore_class.call_count == 3
        assert isinstance(result, pd.DataFrame)

    @patch("hoopstat_nba_ingestion.nba_client.boxscoretraditionalv2.BoxScoreTraditionalV2")
    def test_retry_exhaustion(self, mock_boxscore_class):
        """Test that method fails after retry limit is reached."""
        # All calls fail
        mock_boxscore_class.side_effect = ConnectionError("Persistent error")

        with pytest.raises(ConnectionError):
            self.client.get_box_score("0022400001")

        # Should have tried 3 times (default retry limit)
        assert mock_boxscore_class.call_count == 3
