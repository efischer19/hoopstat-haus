"""
Tests for the NBA client functionality.
"""

from datetime import date
from unittest.mock import Mock, patch

import pytest

from hoopstat_nba_api.nba_client import NBAAPIError, NBAClient
from hoopstat_nba_api.rate_limiter import RateLimiter


class TestNBAClient:
    """Test cases for NBAClient class."""

    def test_init_with_default_rate_limiter(self):
        """Test initialization with default rate limiter."""
        client = NBAClient()
        assert isinstance(client.rate_limiter, RateLimiter)
        assert client.session is not None

    def test_init_with_custom_rate_limiter(self):
        """Test initialization with custom rate limiter."""
        custom_limiter = RateLimiter(min_delay=0.5)
        client = NBAClient(rate_limiter=custom_limiter)
        assert client.rate_limiter is custom_limiter

    @patch("hoopstat_nba_api.nba_client.LeagueGameFinder")
    def test_make_request_success(self, mock_endpoint):
        """Test successful API request."""
        # Mock the endpoint response
        mock_instance = Mock()
        mock_instance.get_dict.return_value = {"test": "data"}
        mock_endpoint.return_value = mock_instance

        client = NBAClient()

        result = client._make_request(mock_endpoint, test_param="value")

        assert result == {"test": "data"}
        mock_endpoint.assert_called_once_with(test_param="value")
        mock_instance.get_dict.assert_called_once()

    @patch("hoopstat_nba_api.nba_client.LeagueGameFinder")
    def test_make_request_with_retries(self, mock_endpoint):
        """Test API request with retries on failure."""
        # Mock endpoint that fails then succeeds
        mock_instance = Mock()
        mock_instance.get_dict.side_effect = [
            Exception("First failure"),
            {"test": "data"},
        ]
        mock_endpoint.return_value = mock_instance

        client = NBAClient()

        result = client._make_request(mock_endpoint)

        assert result == {"test": "data"}
        assert mock_instance.get_dict.call_count == 2

    @patch("hoopstat_nba_api.nba_client.LeagueGameFinder")
    def test_make_request_max_retries_exceeded(self, mock_endpoint):
        """Test API request that exceeds max retries."""
        # Mock endpoint that always fails
        mock_instance = Mock()
        mock_instance.get_dict.side_effect = Exception("Always fails")
        mock_endpoint.return_value = mock_instance

        client = NBAClient()

        with pytest.raises(NBAAPIError):
            client._make_request(mock_endpoint)

    @patch.object(NBAClient, "_make_request")
    def test_get_games_for_date(self, mock_make_request):
        """Test fetching games for a specific date."""
        # Mock API response
        mock_response = {
            "resultSet": {
                "headers": ["GAME_ID", "HOME_TEAM", "AWAY_TEAM"],
                "rowSet": [["001", "Lakers", "Warriors"], ["002", "Bulls", "Heat"]],
            }
        }
        mock_make_request.return_value = mock_response

        client = NBAClient()
        target_date = date(2024, 1, 15)

        games = client.get_games_for_date(target_date)

        assert len(games) == 2
        assert games[0]["GAME_ID"] == "001"
        assert games[0]["HOME_TEAM"] == "Lakers"
        assert "fetch_date" in games[0]

        # Verify the API was called with correct parameters
        mock_make_request.assert_called_once()
        call_args = mock_make_request.call_args
        assert call_args[1]["date_from_nullable"] == "01/15/2024"
        assert call_args[1]["date_to_nullable"] == "01/15/2024"

    @patch.object(NBAClient, "_make_request")
    def test_get_games_for_date_empty_response(self, mock_make_request):
        """Test fetching games when no games are found."""
        # Mock empty API response
        mock_response = {
            "resultSet": {
                "headers": ["GAME_ID", "HOME_TEAM", "AWAY_TEAM"],
                "rowSet": [],
            }
        }
        mock_make_request.return_value = mock_response

        client = NBAClient()
        games = client.get_games_for_date(date(2024, 1, 15))

        assert len(games) == 0

    @patch.object(NBAClient, "_make_request")
    def test_get_box_score(self, mock_make_request):
        """Test fetching box score for a game."""
        mock_response = {
            "resultSet": {
                "headers": ["PLAYER_ID", "POINTS"],
                "rowSet": [[123, 25], [456, 30]],
            }
        }
        mock_make_request.return_value = mock_response

        client = NBAClient()
        game_id = "0022300001"

        box_score = client.get_box_score(game_id)

        assert box_score["game_id"] == game_id
        assert "fetch_date" in box_score
        assert "resultSet" in box_score

    @patch.object(NBAClient, "_make_request")
    def test_get_player_info(self, mock_make_request):
        """Test fetching player information."""
        mock_response = {
            "resultSet": {
                "headers": ["PLAYER_ID", "FIRST_NAME", "LAST_NAME"],
                "rowSet": [[123, "Test", "Player"]],
            }
        }
        mock_make_request.return_value = mock_response

        client = NBAClient()
        player_id = 123

        player_info = client.get_player_info(player_id)

        assert player_info["player_id"] == player_id
        assert "fetch_date" in player_info

    @patch.object(NBAClient, "_make_request")
    def test_get_league_standings(self, mock_make_request):
        """Test fetching league standings."""
        mock_response = {
            "resultSet": {
                "headers": ["TEAM_ID", "WINS", "LOSSES"],
                "rowSet": [[1, 25, 10], [2, 20, 15]],
            }
        }
        mock_make_request.return_value = mock_response

        client = NBAClient()

        standings = client.get_league_standings()

        assert "fetch_date" in standings
        assert "resultSet" in standings

    @patch.object(NBAClient, "_make_request")
    def test_api_error_handling(self, mock_make_request):
        """Test proper error handling for API failures."""
        mock_make_request.side_effect = Exception("API Error")

        client = NBAClient()

        with pytest.raises(NBAAPIError):
            client.get_games_for_date(date(2024, 1, 15))

        with pytest.raises(NBAAPIError):
            client.get_box_score("001")

        with pytest.raises(NBAAPIError):
            client.get_player_info(123)

        with pytest.raises(NBAAPIError):
            client.get_league_standings()
