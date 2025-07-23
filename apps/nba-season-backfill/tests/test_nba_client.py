"""
Tests for NBA API client rate limiting and request handling.

The NBA client now uses the shared hoopstat-nba-client library.
These tests verify the integration works correctly.
"""

import time
from unittest.mock import Mock, patch

import pytest

from app.nba_client import NBAClient


class TestNBAClient:
    """Test NBA API client functionality."""

    def test_nba_client_initialization(self):
        """Test NBA client initialization."""
        client = NBAClient(rate_limit_seconds=3.0, max_retries=5)

        assert client.rate_limiter.base_delay == 3.0
        assert client.max_retries == 5
        assert client.session_stats["total_requests"] == 0

    @patch("hoopstat_nba_client.client.leaguegamefinder.LeagueGameFinder")
    def test_get_season_games_success(self, mock_finder):
        """Test successful season games retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.get_dict.return_value = {
            "resultSets": [
                {
                    "rowSet": [
                        ["game1_data"],
                        ["game2_data"],
                    ]
                }
            ]
        }
        mock_finder.return_value = mock_response

        client = NBAClient(rate_limit_seconds=1.0)  # Minimum allowed for testing
        games = client.get_season_games("2024-25")

        assert len(games) == 2
        assert games[0] == ["game1_data"]
        assert client.session_stats["successful_requests"] == 1
        assert client.session_stats["total_requests"] == 1

    @patch("hoopstat_nba_client.client.boxscoretraditionalv2.BoxScoreTraditionalV2")
    def test_get_box_score_traditional_success(self, mock_box_score):
        """Test successful box score retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.get_dict.return_value = {
            "resultSets": [
                {
                    "headers": ["PLAYER_ID", "PLAYER_NAME", "PTS"],
                    "rowSet": [
                        [123, "Player 1", 25],
                        [456, "Player 2", 18],
                    ],
                }
            ]
        }
        mock_box_score.return_value = mock_response

        client = NBAClient(rate_limit_seconds=1.0)
        box_score = client.get_box_score_traditional("0022400001")

        assert "resultSets" in box_score
        assert client.session_stats["successful_requests"] == 1
        mock_box_score.assert_called_once_with(game_id="0022400001")

    @patch("hoopstat_nba_client.client.boxscoretraditionalv2.BoxScoreTraditionalV2")
    def test_request_failure_tracking(self, mock_box_score):
        """Test request failure tracking."""
        # Mock failure
        mock_box_score.side_effect = Exception("API Error")

        client = NBAClient(rate_limit_seconds=1.0)

        with pytest.raises(Exception, match="API Error"):
            client.get_box_score_traditional("0022400001")

        assert client.session_stats["failed_requests"] == 1
        assert client.session_stats["successful_requests"] == 0

    def test_session_stats(self):
        """Test session statistics tracking."""
        client = NBAClient()
        stats = client.get_session_stats()

        expected_keys = [
            "total_requests",
            "successful_requests",
            "failed_requests",
            "rate_limit_hits",
        ]

        for key in expected_keys:
            assert key in stats
            assert isinstance(stats[key], int)
