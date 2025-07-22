"""
Tests for NBA API client rate limiting and request handling.
"""

import time
from unittest.mock import Mock, patch

import pytest

from app.nba_client import NBAClient, RateLimiter


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(base_delay=3.0)
        
        assert limiter.base_delay == 3.0
        assert limiter.current_delay == 3.0
        assert limiter.consecutive_errors == 0
    
    def test_rate_limiter_wait(self):
        """Test rate limiter wait functionality."""
        limiter = RateLimiter(base_delay=0.1)  # Short delay for testing
        
        start_time = time.time()
        limiter.wait()
        first_wait = time.time()
        
        # Second wait should delay
        limiter.wait()
        second_wait = time.time()
        
        # Should have delayed approximately the base delay amount
        assert (second_wait - first_wait) >= 0.05  # Allow some tolerance
    
    def test_rate_limiter_adjust_success(self):
        """Test rate limiter adjustment for successful responses."""
        limiter = RateLimiter(base_delay=5.0)
        limiter.current_delay = 10.0  # Start with elevated delay
        
        # Fast successful response should reduce delay
        limiter.adjust_for_response(response_time=0.5, status_code=200)
        
        # Should reduce delay (but not below base)
        assert limiter.current_delay < 10.0
        assert limiter.current_delay >= limiter.base_delay
        assert limiter.consecutive_errors == 0
    
    def test_rate_limiter_adjust_rate_limit(self):
        """Test rate limiter adjustment for rate limit responses."""
        limiter = RateLimiter(base_delay=5.0)
        initial_delay = limiter.current_delay
        
        # Rate limit response should increase delay
        limiter.adjust_for_response(response_time=2.0, status_code=429)
        
        assert limiter.current_delay > initial_delay
        assert limiter.consecutive_errors == 1
    
    def test_rate_limiter_adjust_server_error(self):
        """Test rate limiter adjustment for server errors."""
        limiter = RateLimiter(base_delay=5.0)
        initial_delay = limiter.current_delay
        
        # Server error should increase delay moderately
        limiter.adjust_for_response(response_time=2.0, status_code=503)
        
        assert limiter.current_delay > initial_delay
        assert limiter.consecutive_errors == 1


class TestNBAClient:
    """Test NBA API client functionality."""
    
    def test_nba_client_initialization(self):
        """Test NBA client initialization."""
        client = NBAClient(rate_limit_seconds=3.0, max_retries=5)
        
        assert client.rate_limiter.base_delay == 3.0
        assert client.max_retries == 5
        assert client.session_stats["total_requests"] == 0
    
    @patch('app.nba_client.leaguegamefinder.LeagueGameFinder')
    def test_get_season_games_success(self, mock_finder):
        """Test successful season games retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.get_dict.return_value = {
            "resultSets": [{
                "rowSet": [
                    ["game1_data"],
                    ["game2_data"],
                ]
            }]
        }
        mock_finder.return_value = mock_response
        
        client = NBAClient(rate_limit_seconds=1.0)  # Minimum allowed for testing
        games = client.get_season_games("2024-25")
        
        assert len(games) == 2
        assert games[0] == ["game1_data"]
        assert client.session_stats["successful_requests"] == 1
        assert client.session_stats["total_requests"] == 1
    
    @patch('app.nba_client.boxscoretraditionalv2.BoxScoreTraditionalV2')
    def test_get_box_score_traditional_success(self, mock_box_score):
        """Test successful box score retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.get_dict.return_value = {
            "resultSets": [{
                "headers": ["PLAYER_ID", "PLAYER_NAME", "PTS"],
                "rowSet": [
                    [123, "Player 1", 25],
                    [456, "Player 2", 18],
                ]
            }]
        }
        mock_box_score.return_value = mock_response
        
        client = NBAClient(rate_limit_seconds=1.0)
        box_score = client.get_box_score_traditional("0022400001")
        
        assert "resultSets" in box_score
        assert client.session_stats["successful_requests"] == 1
        mock_box_score.assert_called_once_with(game_id="0022400001")
    
    @patch('app.nba_client.boxscoretraditionalv2.BoxScoreTraditionalV2')
    def test_request_failure_tracking(self, mock_box_score):
        """Test request failure tracking."""
        # Mock failure
        mock_box_score.side_effect = Exception("API Error")
        
        client = NBAClient(rate_limit_seconds=1.0)
        
        with pytest.raises(Exception):
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