"""
NBA API Client for accessing basketball data.

This module provides a unified interface for accessing NBA statistics and game data
through the nba-api package.
"""

import logging
from typing import Any

from nba_api.stats.endpoints import LeagueGameFinder, ScoreboardV2


class NBAAPIError(Exception):
    """Exception raised for NBA API related errors."""

    pass


class NBAAPIClient:
    """
    Main client for accessing NBA API endpoints.

    Provides centralized configuration and error handling for NBA API calls.
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize NBA API client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)

    def _make_request(self, endpoint_class, **kwargs) -> Any:
        """
        Make a request to NBA API with error handling and retries.

        Args:
            endpoint_class: NBA API endpoint class to instantiate
            **kwargs: Arguments to pass to the endpoint

        Returns:
            The endpoint instance with data loaded

        Raises:
            NBAAPIError: If the request fails after all retries
        """
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(
                    f"Making NBA API request (attempt {attempt + 1}/"
                    f"{self.max_retries + 1})"
                )
                endpoint = endpoint_class(**kwargs, timeout=self.timeout)
                return endpoint
            except Exception as e:
                if attempt == self.max_retries:
                    self.logger.error(
                        f"NBA API request failed after {self.max_retries + 1} "
                        f"attempts: {str(e)}"
                    )
                    raise NBAAPIError(
                        f"Failed to fetch data from NBA API: {str(e)}"
                    ) from e
                else:
                    self.logger.warning(
                        f"NBA API request attempt {attempt + 1} failed, "
                        f"retrying: {str(e)}"
                    )

        # This should never be reached, but included for completeness
        raise NBAAPIError("Unexpected error in NBA API request")

    def get_scoreboard(self, game_date: str) -> ScoreboardV2:
        """
        Get games scoreboard for a specific date.

        Args:
            game_date: Date in YYYY-MM-DD format

        Returns:
            ScoreboardV2 endpoint instance with game data
        """
        return self._make_request(ScoreboardV2, game_date=game_date)

    def get_games(
        self, date_from: str | None = None, date_to: str | None = None
    ) -> LeagueGameFinder:
        """
        Get games within a date range.

        Args:
            date_from: Start date in MM/DD/YYYY format (optional)
            date_to: End date in MM/DD/YYYY format (optional)

        Returns:
            LeagueGameFinder endpoint instance with game data
        """
        kwargs = {}
        if date_from:
            kwargs["date_from_nullable"] = date_from
        if date_to:
            kwargs["date_to_nullable"] = date_to

        return self._make_request(LeagueGameFinder, **kwargs)
