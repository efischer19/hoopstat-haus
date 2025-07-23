"""
Rate limiting functionality for NBA API requests.

Implements token bucket rate limiter with adaptive behavior based on API response patterns.
"""

import time

from hoopstat_observability import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for NBA API requests.

    Implements conservative rate limiting with adaptive behavior
    based on API response patterns.
    """

    def __init__(self, base_delay: float = 5.0):
        """
        Initialize rate limiter.

        Args:
            base_delay: Base delay between requests in seconds
        """
        self.base_delay = base_delay
        self.current_delay = base_delay
        self.last_request_time = 0.0
        self.consecutive_errors = 0

    def wait(self) -> None:
        """Wait appropriate time before next request."""
        elapsed = time.time() - self.last_request_time
        sleep_time = self.current_delay - elapsed

        if sleep_time > 0:
            logger.debug(
                "Rate limiting delay",
                sleep_time=round(sleep_time, 2),
                current_delay=self.current_delay,
            )
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def adjust_for_response(self, response_time: float, status_code: int) -> None:
        """
        Adjust rate limiting based on API response.

        Args:
            response_time: Response time in seconds
            status_code: HTTP status code (429 for rate limited)
        """
        if status_code == 429:
            # Rate limited - exponential backoff
            self.current_delay *= 2
            self.consecutive_errors += 1
            logger.warning(
                "Rate limit hit, increasing delay",
                new_delay=self.current_delay,
                consecutive_errors=self.consecutive_errors,
            )
        elif status_code == 200 and response_time < 1.0:
            # Successful fast response - gradual return to base rate
            self.current_delay = max(self.base_delay, self.current_delay * 0.95)
            self.consecutive_errors = 0
        elif status_code >= 500:
            # Server error - increase delay moderately
            self.current_delay *= 1.5
            self.consecutive_errors += 1
            logger.warning(
                "Server error, increasing delay",
                status_code=status_code,
                new_delay=self.current_delay,
            )

    def reset(self) -> None:
        """Reset rate limiter to initial state."""
        self.current_delay = self.base_delay
        self.consecutive_errors = 0
        self.last_request_time = 0.0