"""
Tests for NBA API player stats fetcher functionality.
"""

from unittest.mock import Mock

import pytest

from hoopstat_nba_api.client import NBAAPIClient, NBAAPIError
from hoopstat_nba_api.players import PlayerStatsFetcher


class TestPlayerStatsFetcher:
    """Test NBA API player stats fetcher functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = Mock(spec=NBAAPIClient)
        self.fetcher = PlayerStatsFetcher(self.client)

    def test_fetcher_initialization(self):
        """Test fetcher initializes correctly."""
        assert self.fetcher.client == self.client

    def test_fetch_player_stats_placeholder(self):
        """Test fetch player stats placeholder implementation."""
        result = self.fetcher.fetch_player_stats("2025-01-15")

        assert result["date"] == "2025-01-15"
        assert result["season_type"] == "Regular Season"
        assert result["player_stats"] == []
        assert result["total_players"] == 0
        assert "fetched_at" in result

    def test_fetch_player_stats_with_season_type(self):
        """Test fetch player stats with custom season type."""
        result = self.fetcher.fetch_player_stats("2025-01-15", "Playoffs")

        assert result["season_type"] == "Playoffs"

    def test_fetch_player_game_logs_success(self):
        """Test successful fetch of player game logs."""
        # Mock the game logs response
        mock_game_logs = Mock()
        mock_game_logs.get_dict.return_value = {
            "data": [{"GAME_ID": "123", "PTS": 25}],
            "headers": ["GAME_ID", "PTS"],
        }
        self.client._make_request.return_value = mock_game_logs

        result = self.fetcher.fetch_player_game_logs(123456, "2024-25")

        assert result["player_id"] == 123456
        assert result["season"] == "2024-25"
        assert result["game_logs"] == [{"GAME_ID": "123", "PTS": 25}]
        assert result["headers"] == ["GAME_ID", "PTS"]
        assert result["total_games"] == 1
        assert "fetched_at" in result

    def test_fetch_player_game_logs_api_error(self):
        """Test fetch player game logs with API error."""
        self.client._make_request.side_effect = Exception("API Error")

        with pytest.raises(
            NBAAPIError, match="Failed to fetch game logs for player 123456"
        ):
            self.fetcher.fetch_player_game_logs(123456, "2024-25")
