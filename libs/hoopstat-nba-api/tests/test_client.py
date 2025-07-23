"""
Tests for NBA API client functionality.
"""

from unittest.mock import Mock, patch

import pytest

from hoopstat_nba_api.client import NBAAPIClient, NBAAPIError


class TestNBAAPIClient:
    """Test NBA API client functionality."""

    def test_client_initialization(self):
        """Test client initializes with correct defaults."""
        client = NBAAPIClient()

        assert client.timeout == 30
        assert client.max_retries == 3

    def test_client_initialization_with_custom_values(self):
        """Test client initializes with custom values."""
        client = NBAAPIClient(timeout=60, max_retries=5)

        assert client.timeout == 60
        assert client.max_retries == 5

    @patch("hoopstat_nba_api.client.ScoreboardV2")
    def test_get_scoreboard_success(self, mock_scoreboard):
        """Test successful scoreboard request."""
        client = NBAAPIClient()
        mock_instance = Mock()
        mock_scoreboard.return_value = mock_instance

        result = client.get_scoreboard("2025-01-15")

        assert result == mock_instance
        mock_scoreboard.assert_called_once_with(game_date="2025-01-15", timeout=30)

    @patch("hoopstat_nba_api.client.ScoreboardV2")
    def test_get_scoreboard_failure_after_retries(self, mock_scoreboard):
        """Test scoreboard request failure after max retries."""
        client = NBAAPIClient(max_retries=2)
        mock_scoreboard.side_effect = Exception("API Error")

        with pytest.raises(NBAAPIError, match="Failed to fetch data from NBA API"):
            client.get_scoreboard("2025-01-15")

        assert mock_scoreboard.call_count == 3  # initial + 2 retries

    @patch("hoopstat_nba_api.client.LeagueGameFinder")
    def test_get_games_with_dates(self, mock_game_finder):
        """Test get_games with date parameters."""
        client = NBAAPIClient()
        mock_instance = Mock()
        mock_game_finder.return_value = mock_instance

        result = client.get_games(date_from="01/01/2025", date_to="01/31/2025")

        assert result == mock_instance
        mock_game_finder.assert_called_once_with(
            date_from_nullable="01/01/2025", date_to_nullable="01/31/2025", timeout=30
        )

    @patch("hoopstat_nba_api.client.LeagueGameFinder")
    def test_get_games_without_dates(self, mock_game_finder):
        """Test get_games without date parameters."""
        client = NBAAPIClient()
        mock_instance = Mock()
        mock_game_finder.return_value = mock_instance

        result = client.get_games()

        assert result == mock_instance
        mock_game_finder.assert_called_once_with(timeout=30)
