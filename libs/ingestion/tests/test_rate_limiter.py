"""
Tests for the rate limiter functionality.
"""

import time
from unittest.mock import patch

from hoopstat_nba_ingestion.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test cases for RateLimiter class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        limiter = RateLimiter()
        assert limiter.min_delay == 1.0
        assert limiter.max_delay == 60.0
        assert limiter.backoff_factor == 2.0
        assert limiter.max_retries == 5
        assert limiter.current_delay == 1.0
        assert limiter.last_request_time is None

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        limiter = RateLimiter(
            min_delay=0.5,
            max_delay=30.0,
            backoff_factor=1.5,
            max_retries=3,
        )
        assert limiter.min_delay == 0.5
        assert limiter.max_delay == 30.0
        assert limiter.backoff_factor == 1.5
        assert limiter.max_retries == 3
        assert limiter.current_delay == 0.5

    def test_wait_if_needed_first_call(self):
        """Test that first call doesn't wait."""
        limiter = RateLimiter(min_delay=1.0)

        start_time = time.time()
        limiter.wait_if_needed()
        end_time = time.time()

        # Should not wait on first call
        assert end_time - start_time < 0.1
        assert limiter.last_request_time is not None

    @patch("time.sleep")
    def test_wait_if_needed_subsequent_call(self, mock_sleep):
        """Test that subsequent calls wait if needed."""
        limiter = RateLimiter(min_delay=2.0)

        # First call
        limiter.wait_if_needed()

        # Simulate time passing but not enough
        with patch("time.time", return_value=limiter.last_request_time + 1.0):
            limiter.wait_if_needed()
            mock_sleep.assert_called_once()
            # Should sleep for remaining time (2.0 - 1.0 = 1.0)
            assert abs(mock_sleep.call_args[0][0] - 1.0) < 0.01

    def test_handle_rate_limit_error(self):
        """Test rate limit error handling."""
        limiter = RateLimiter(min_delay=1.0, backoff_factor=2.0, max_delay=10.0)

        # First rate limit error
        should_retry = limiter.handle_rate_limit_error()
        assert should_retry is True
        assert limiter.current_delay == 2.0

        # Second rate limit error
        should_retry = limiter.handle_rate_limit_error()
        assert should_retry is True
        assert limiter.current_delay == 4.0

        # Continue until max delay
        limiter.handle_rate_limit_error()  # 8.0
        assert limiter.current_delay == 8.0

        should_retry = limiter.handle_rate_limit_error()  # 10.0 (max)
        assert limiter.current_delay == 10.0
        assert should_retry is False  # Should not retry when at max

    def test_reset_delay(self):
        """Test delay reset functionality."""
        limiter = RateLimiter(min_delay=1.0)

        # Increase delay
        limiter.handle_rate_limit_error()
        assert limiter.current_delay == 2.0

        # Reset delay
        limiter.reset_delay()
        assert limiter.current_delay == 1.0

    def test_reset_delay_already_at_min(self):
        """Test reset delay when already at minimum."""
        limiter = RateLimiter(min_delay=1.0)

        # Should not change if already at minimum
        original_delay = limiter.current_delay
        limiter.reset_delay()
        assert limiter.current_delay == original_delay
