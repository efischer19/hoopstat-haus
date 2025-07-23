"""
Rate limiting functionality with exponential backoff for respectful API usage.
"""

import logging
import time

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter with exponential backoff for respectful API usage.

    Designed to be conservative and respectful to the NBA API to avoid
    getting blocked or causing issues for the broader community.
    """

    def __init__(
        self,
        min_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        max_retries: int = 5,
    ):
        """
        Initialize the rate limiter.

        Args:
            min_delay: Minimum delay between requests in seconds
            max_delay: Maximum delay between requests in seconds
            backoff_factor: Factor to multiply delay by on each retry
            max_retries: Maximum number of retries before giving up
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.max_retries = max_retries
        self.current_delay = min_delay
        self.last_request_time: float | None = None

    def wait_if_needed(self) -> None:
        """Wait if needed to respect rate limits."""
        if self.last_request_time is None:
            self.last_request_time = time.time()
            return

        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.current_delay:
            sleep_time = self.current_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def handle_rate_limit_error(self) -> bool:
        """
        Handle a rate limit error by increasing delay.

        Returns:
            True if should retry, False if max retries exceeded
        """
        self.current_delay = min(
            self.current_delay * self.backoff_factor, self.max_delay
        )
        logger.warning(
            f"Rate limit hit, increasing delay to {self.current_delay:.2f} seconds"
        )

        # Check if we should retry
        return self.current_delay < self.max_delay

    def reset_delay(self) -> None:
        """Reset delay to minimum after successful requests."""
        if self.current_delay > self.min_delay:
            logger.debug("Resetting rate limit delay to minimum")
            self.current_delay = self.min_delay
