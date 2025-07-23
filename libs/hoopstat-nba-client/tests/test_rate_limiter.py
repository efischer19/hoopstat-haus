"""Tests for the rate limiter module."""

import time
from unittest.mock import patch

import pytest

from hoopstat_nba_client.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test cases for RateLimiter class."""

    def test_init(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(base_delay=3.0)
        
        assert limiter.base_delay == 3.0
        assert limiter.current_delay == 3.0
        assert limiter.last_request_time == 0.0
        assert limiter.consecutive_errors == 0

    def test_wait_no_delay_needed(self):
        """Test wait when enough time has passed."""
        limiter = RateLimiter(base_delay=1.0)
        limiter.last_request_time = time.time() - 2.0  # 2 seconds ago
        
        start_time = time.time()
        limiter.wait()
        elapsed = time.time() - start_time
        
        # Should not sleep since enough time has passed
        assert elapsed < 0.1

    @patch("time.sleep")
    def test_wait_with_delay(self, mock_sleep):
        """Test wait when delay is needed."""
        limiter = RateLimiter(base_delay=2.0)
        limiter.last_request_time = time.time() - 0.5  # 0.5 seconds ago
        
        limiter.wait()
        
        # Should sleep for approximately 1.5 seconds
        mock_sleep.assert_called_once()
        sleep_time = mock_sleep.call_args[0][0]
        assert 1.4 <= sleep_time <= 1.6

    def test_adjust_for_rate_limit(self):
        """Test adjustment for rate limit response."""
        limiter = RateLimiter(base_delay=2.0)
        initial_delay = limiter.current_delay
        
        limiter.adjust_for_response(response_time=1.0, status_code=429)
        
        assert limiter.current_delay == initial_delay * 2
        assert limiter.consecutive_errors == 1

    def test_adjust_for_successful_response(self):
        """Test adjustment for successful fast response."""
        limiter = RateLimiter(base_delay=2.0)
        limiter.current_delay = 4.0  # Elevated from previous issues
        
        limiter.adjust_for_response(response_time=0.5, status_code=200)
        
        assert limiter.current_delay < 4.0  # Should decrease
        assert limiter.consecutive_errors == 0

    def test_adjust_for_server_error(self):
        """Test adjustment for server error."""
        limiter = RateLimiter(base_delay=2.0)
        initial_delay = limiter.current_delay
        
        limiter.adjust_for_response(response_time=1.0, status_code=500)
        
        assert limiter.current_delay == initial_delay * 1.5
        assert limiter.consecutive_errors == 1

    def test_reset(self):
        """Test rate limiter reset."""
        limiter = RateLimiter(base_delay=2.0)
        limiter.current_delay = 10.0
        limiter.consecutive_errors = 5
        limiter.last_request_time = time.time()
        
        limiter.reset()
        
        assert limiter.current_delay == 2.0
        assert limiter.consecutive_errors == 0
        assert limiter.last_request_time == 0.0