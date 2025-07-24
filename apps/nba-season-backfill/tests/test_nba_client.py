"""Tests for NBA API client with rate limiting."""

import time
from unittest.mock import Mock, patch

import pytest
import requests

from app.config import BackfillConfig
from app.nba_client import APIResponse, NBAClient, RateLimiter


class TestRateLimiter:
    """Test cases for RateLimiter class."""

    def test_initial_delay(self):
        """Test initial rate limiter configuration."""
        limiter = RateLimiter(base_delay_seconds=10)

        assert limiter.base_delay == 10
        assert limiter.current_delay == 10
        assert limiter.consecutive_errors == 0

    def test_wait_timing(self):
        """Test that rate limiter waits appropriate time on subsequent calls."""
        limiter = RateLimiter(base_delay_seconds=0.1)  # Shorter delay for testing

        # First call to establish last_request_time
        limiter.wait()

        # Second call should wait the full delay
        start_time = time.time()
        limiter.wait()
        elapsed = time.time() - start_time

        # Should wait close to 0.1 second (allowing some variance for execution)
        assert 0.05 <= elapsed <= 0.2

    def test_adjust_for_rate_limit_response(self):
        """Test rate limit adjustment for 429 responses."""
        limiter = RateLimiter(base_delay_seconds=5)
        initial_delay = limiter.current_delay

        limiter.adjust_for_response(1.0, 429)

        assert limiter.current_delay == initial_delay * 2
        assert limiter.consecutive_errors == 1

    def test_adjust_for_server_error(self):
        """Test rate limit adjustment for server errors."""
        limiter = RateLimiter(base_delay_seconds=5)
        initial_delay = limiter.current_delay

        limiter.adjust_for_response(1.0, 500)

        assert limiter.current_delay == initial_delay * 1.5
        assert limiter.consecutive_errors == 1

    def test_adjust_for_successful_response(self):
        """Test rate limit adjustment for successful fast responses."""
        limiter = RateLimiter(base_delay_seconds=5)
        limiter.current_delay = 10  # Set higher than base

        limiter.adjust_for_response(0.5, 200)  # Fast successful response

        assert limiter.current_delay < 10  # Should decrease
        assert limiter.current_delay >= 5  # But not below base
        assert limiter.consecutive_errors == 0

    def test_maximum_delay_cap(self):
        """Test that delay doesn't exceed maximum."""
        limiter = RateLimiter(base_delay_seconds=5)

        # Simulate many rate limit responses
        for _ in range(10):
            limiter.adjust_for_response(1.0, 429)

        assert limiter.current_delay <= 60.0


class TestNBAClient:
    """Test cases for NBAClient class."""

    def setup_method(self):
        """Setup test configuration."""
        self.config = BackfillConfig(
            aws_region="us-east-1",
            s3_bucket_name="test-bucket",
            season="2024-25",
            rate_limit_seconds=1,  # Faster for testing
        )

    def test_client_initialization(self):
        """Test NBA client initialization."""
        client = NBAClient(self.config)

        assert client.config == self.config
        assert client.rate_limiter.base_delay == 1
        assert client.stats["total_requests"] == 0

    def test_get_season_games_success(self):
        """Test successful season games retrieval."""
        client = NBAClient(self.config)

        # Mock the _make_request method directly
        mock_response = APIResponse(
            data=[Mock()], endpoint="LeagueGameFinder", status_code=200
        )

        with patch.object(client, "_make_request", return_value=mock_response):
            response = client.get_season_games("2024-25")

        assert isinstance(response, APIResponse)
        assert response.endpoint == "LeagueGameFinder"
        assert response.status_code == 200

    def test_get_box_score_success(self):
        """Test successful box score retrieval."""
        client = NBAClient(self.config)

        # Mock the _make_request method directly
        mock_response = APIResponse(
            data=[Mock()],
            endpoint="BoxScoreTraditionalV2",
            game_id="0022400001",
            status_code=200,
        )

        with patch.object(client, "_make_request", return_value=mock_response):
            response = client.get_game_box_score_traditional("0022400001")

        assert isinstance(response, APIResponse)
        assert response.endpoint == "BoxScoreTraditionalV2"
        assert response.game_id == "0022400001"

    def test_api_error_handling(self):
        """Test API error handling and retry logic."""
        client = NBAClient(self.config)

        # Mock _make_request to raise an exception
        with patch.object(
            client,
            "_make_request",
            side_effect=requests.exceptions.HTTPError("Rate limited"),
        ):
            with pytest.raises(requests.exceptions.HTTPError):
                client.get_game_box_score_traditional("0022400001")

    def test_stats_summary(self):
        """Test API statistics summary."""
        client = NBAClient(self.config)
        client.stats["total_requests"] = 10
        client.stats["successful_requests"] = 8
        client.stats["failed_requests"] = 2
        client.stats["total_response_time"] = 5000  # 5 seconds total

        summary = client.get_stats_summary()

        assert summary["total_requests"] == 10
        assert summary["successful_requests"] == 8
        assert summary["failed_requests"] == 2
        assert summary["success_rate"] == 0.8
        assert summary["average_response_time_ms"] == 625  # 5000/8


class TestAPIResponse:
    """Test cases for APIResponse dataclass."""

    def test_api_response_creation(self):
        """Test APIResponse object creation."""
        response = APIResponse(
            data=[Mock()],
            endpoint="TestEndpoint",
            game_id="0022400001",
            response_time_ms=1500.0,
        )

        assert response.endpoint == "TestEndpoint"
        assert response.game_id == "0022400001"
        assert response.response_time_ms == 1500.0
        assert response.status_code == 200  # default
        assert response.error is None  # default
