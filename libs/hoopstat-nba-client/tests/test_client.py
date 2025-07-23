"""Tests for the NBA client module."""

from unittest.mock import Mock, patch

import pytest

from hoopstat_nba_client.client import NBAClient


class TestNBAClient:
    """Test cases for NBAClient class."""

    def test_init(self):
        """Test NBA client initialization."""
        client = NBAClient(rate_limit_seconds=3.0, max_retries=5)
        
        assert client.rate_limiter.base_delay == 3.0
        assert client.max_retries == 5
        assert client.session_stats["total_requests"] == 0
        assert client.session_stats["successful_requests"] == 0
        assert client.session_stats["failed_requests"] == 0
        assert client.session_stats["rate_limit_hits"] == 0

    @patch("hoopstat_nba_client.client.leaguegamefinder.LeagueGameFinder")
    def test_get_season_games_success(self, mock_endpoint):
        """Test successful season games retrieval."""
        # Mock the API response
        mock_response = Mock()
        mock_response.get_dict.return_value = {
            "resultSets": [{"rowSet": [["game1"], ["game2"]]}]
        }
        mock_endpoint.return_value = mock_response
        
        client = NBAClient()
        games = client.get_season_games("2024-25")
        
        assert len(games) == 2
        assert games == [["game1"], ["game2"]]
        assert client.session_stats["successful_requests"] == 1
        assert client.session_stats["total_requests"] == 1

    @patch("hoopstat_nba_client.client.boxscoretraditionalv2.BoxScoreTraditionalV2")
    def test_get_box_score_traditional(self, mock_endpoint):
        """Test traditional box score retrieval."""
        mock_response = Mock()
        mock_response.get_dict.return_value = {"game_data": "traditional"}
        mock_endpoint.return_value = mock_response
        
        client = NBAClient()
        result = client.get_box_score_traditional("game123")
        
        assert result == {"game_data": "traditional"}
        mock_endpoint.assert_called_once_with(game_id="game123")

    @patch("hoopstat_nba_client.client.boxscoreadvancedv2.BoxScoreAdvancedV2")
    def test_get_box_score_advanced(self, mock_endpoint):
        """Test advanced box score retrieval."""
        mock_response = Mock()
        mock_response.get_dict.return_value = {"game_data": "advanced"}
        mock_endpoint.return_value = mock_response
        
        client = NBAClient()
        result = client.get_box_score_advanced("game123")
        
        assert result == {"game_data": "advanced"}
        mock_endpoint.assert_called_once_with(game_id="game123")

    @patch("hoopstat_nba_client.client.playbyplayv2.PlayByPlayV2")
    def test_get_play_by_play(self, mock_endpoint):
        """Test play-by-play data retrieval."""
        mock_response = Mock()
        mock_response.get_dict.return_value = {"pbp_data": "plays"}
        mock_endpoint.return_value = mock_response
        
        client = NBAClient()
        result = client.get_play_by_play("game123")
        
        assert result == {"pbp_data": "plays"}
        mock_endpoint.assert_called_once_with(game_id="game123")

    @patch("hoopstat_nba_client.client.commonplayerinfo.CommonPlayerInfo")
    def test_get_player_info(self, mock_endpoint):
        """Test player info retrieval."""
        mock_response = Mock()
        mock_response.get_dict.return_value = {"player_data": "info"}
        mock_endpoint.return_value = mock_response
        
        client = NBAClient()
        result = client.get_player_info("player123")
        
        assert result == {"player_data": "info"}
        mock_endpoint.assert_called_once_with(player_id="player123")

    def test_get_session_stats(self):
        """Test session statistics retrieval."""
        client = NBAClient()
        client.session_stats["successful_requests"] = 5
        client.session_stats["failed_requests"] = 2
        
        stats = client.get_session_stats()
        
        # Should return a copy
        assert stats["successful_requests"] == 5
        assert stats["failed_requests"] == 2
        
        # Modifying returned stats shouldn't affect original
        stats["successful_requests"] = 10
        assert client.session_stats["successful_requests"] == 5

    def test_reset_session_stats(self):
        """Test session statistics reset."""
        client = NBAClient()
        client.session_stats["successful_requests"] = 5
        client.session_stats["failed_requests"] = 2
        
        client.reset_session_stats()
        
        assert client.session_stats["successful_requests"] == 0
        assert client.session_stats["failed_requests"] == 0
        assert client.session_stats["total_requests"] == 0
        assert client.session_stats["rate_limit_hits"] == 0

    def test_reset_rate_limiter(self):
        """Test rate limiter reset."""
        client = NBAClient()
        client.rate_limiter.current_delay = 10.0
        client.rate_limiter.consecutive_errors = 3
        
        client.reset_rate_limiter()
        
        assert client.rate_limiter.current_delay == client.rate_limiter.base_delay
        assert client.rate_limiter.consecutive_errors == 0

    @patch("hoopstat_nba_client.client.leaguegamefinder.LeagueGameFinder")
    def test_make_request_failure_updates_stats(self, mock_endpoint):
        """Test that failed requests update statistics properly."""
        mock_endpoint.side_effect = Exception("API Error")
        
        client = NBAClient()
        
        with pytest.raises(Exception, match="API Error"):
            client.get_season_games("2024-25")
        
        assert client.session_stats["total_requests"] == 1
        assert client.session_stats["successful_requests"] == 0
        assert client.session_stats["failed_requests"] == 1

    @patch("hoopstat_nba_client.client.leaguegamefinder.LeagueGameFinder")
    def test_make_request_rate_limit_detection(self, mock_endpoint):
        """Test that rate limit errors are properly detected and tracked."""
        mock_endpoint.side_effect = Exception("429 rate limit exceeded")
        
        client = NBAClient()
        
        with pytest.raises(Exception, match="429 rate limit exceeded"):
            client.get_season_games("2024-25")
        
        assert client.session_stats["rate_limit_hits"] == 1
        assert client.session_stats["failed_requests"] == 1