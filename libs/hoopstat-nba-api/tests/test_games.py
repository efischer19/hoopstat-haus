"""
Tests for NBA API games fetcher functionality.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from hoopstat_nba_api.client import NBAAPIClient, NBAAPIError
from hoopstat_nba_api.games import GamesFetcher


class TestGamesFetcher:
    """Test NBA API games fetcher functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = Mock(spec=NBAAPIClient)
        self.fetcher = GamesFetcher(self.client)

    def test_fetcher_initialization(self):
        """Test fetcher initializes correctly."""
        assert self.fetcher.client == self.client

    def test_fetch_games_by_date_success(self):
        """Test successful fetch of games by date."""
        # Mock the scoreboard response
        mock_scoreboard = Mock()
        mock_game_header = Mock()
        mock_game_header.get_dict.return_value = {
            "data": [{"GAME_ID": "123", "HOME_TEAM": "Lakers"}],
            "headers": ["GAME_ID", "HOME_TEAM"],
        }
        mock_scoreboard.game_header = mock_game_header
        self.client.get_scoreboard.return_value = mock_scoreboard

        result = self.fetcher.fetch_games_by_date("2025-01-15")

        assert result["date"] == "2025-01-15"
        assert result["games"] == [{"GAME_ID": "123", "HOME_TEAM": "Lakers"}]
        assert result["headers"] == ["GAME_ID", "HOME_TEAM"]
        assert result["total_games"] == 1
        assert "fetched_at" in result

        self.client.get_scoreboard.assert_called_once_with("2025-01-15")

    def test_fetch_games_by_date_api_error(self):
        """Test fetch games by date with API error."""
        self.client.get_scoreboard.side_effect = Exception("API Error")

        with pytest.raises(NBAAPIError, match="Failed to fetch games for 2025-01-15"):
            self.fetcher.fetch_games_by_date("2025-01-15")

    def test_fetch_games_range_success(self):
        """Test successful fetch of games by date range."""
        # Mock the games finder response
        mock_games_finder = Mock()
        mock_games_finder.get_dict.return_value = {
            "data": [{"GAME_ID": "123"}, {"GAME_ID": "456"}],
            "headers": ["GAME_ID"],
        }
        self.client.get_games.return_value = mock_games_finder

        result = self.fetcher.fetch_games_range("2025-01-01", "2025-01-31")

        assert result["start_date"] == "2025-01-01"
        assert result["end_date"] == "2025-01-31"
        assert result["total_games"] == 2
        assert "fetched_at" in result

        self.client.get_games.assert_called_once_with(
            date_from="01/01/2025", date_to="01/31/2025"
        )

    def test_fetch_games_range_api_error(self):
        """Test fetch games range with API error."""
        self.client.get_games.side_effect = Exception("API Error")

        with pytest.raises(NBAAPIError, match="Failed to fetch games for date range"):
            self.fetcher.fetch_games_range("2025-01-01", "2025-01-31")

    @patch("hoopstat_nba_api.games.datetime")
    def test_fetch_yesterday_games(self, mock_datetime):
        """Test fetch yesterday's games."""
        # Mock datetime.utcnow() to return a fixed date
        fixed_date = datetime(2025, 1, 16, 12, 0, 0)
        mock_datetime.utcnow.return_value = fixed_date
        mock_datetime.strftime = datetime.strftime

        # Mock the scoreboard response
        mock_scoreboard = Mock()
        mock_game_header = Mock()
        mock_game_header.get_dict.return_value = {
            "data": [{"GAME_ID": "123"}],
            "headers": ["GAME_ID"],
        }
        mock_scoreboard.game_header = mock_game_header
        self.client.get_scoreboard.return_value = mock_scoreboard

        result = self.fetcher.fetch_yesterday_games()

        assert result["date"] == "2025-01-15"  # Yesterday from fixed date
        self.client.get_scoreboard.assert_called_once_with("2025-01-15")
