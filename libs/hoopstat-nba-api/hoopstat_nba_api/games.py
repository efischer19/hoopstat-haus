"""
Games data fetcher for NBA API.

This module provides functionality to fetch NBA game data for specific dates
and date ranges.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from .client import NBAAPIClient, NBAAPIError


class GamesFetcher:
    """
    Fetcher for NBA games data.

    Provides methods to retrieve game schedules, scores, and details
    for specific dates or date ranges.
    """

    def __init__(self, client: NBAAPIClient):
        """
        Initialize GamesFetcher with an NBA API client.

        Args:
            client: Configured NBAAPIClient instance
        """
        self.client = client
        self.logger = logging.getLogger(__name__)

    def fetch_games_by_date(self, date: str) -> dict[str, Any]:
        """
        Fetch all games for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Dictionary containing games data with metadata

        Raises:
            NBAAPIError: If the API request fails
        """
        self.logger.info(f"Fetching NBA games for date: {date}")

        try:
            scoreboard = self.client.get_scoreboard(date)
            games_data = scoreboard.game_header.get_dict()

            return {
                "date": date,
                "games": games_data["data"],
                "headers": games_data["headers"],
                "fetched_at": datetime.utcnow().isoformat(),
                "total_games": len(games_data["data"]),
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch games for date {date}: {str(e)}")
            raise NBAAPIError(f"Failed to fetch games for {date}: {str(e)}") from e

    def fetch_games_range(self, start_date: str, end_date: str) -> dict[str, Any]:
        """
        Fetch games for a date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary containing games data for the date range

        Raises:
            NBAAPIError: If the API request fails
        """
        self.logger.info(f"Fetching NBA games from {start_date} to {end_date}")

        try:
            # Convert dates to MM/DD/YYYY format for NBA API
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            start_api_format = start_dt.strftime("%m/%d/%Y")
            end_api_format = end_dt.strftime("%m/%d/%Y")

            games_finder = self.client.get_games(
                date_from=start_api_format, date_to=end_api_format
            )

            games_data = games_finder.get_dict()

            return {
                "start_date": start_date,
                "end_date": end_date,
                "games": games_data["data"],
                "headers": games_data["headers"],
                "fetched_at": datetime.utcnow().isoformat(),
                "total_games": len(games_data["data"]),
            }

        except Exception as e:
            self.logger.error(
                f"Failed to fetch games for range {start_date} to {end_date}: {str(e)}"
            )
            raise NBAAPIError(f"Failed to fetch games for date range: {str(e)}") from e

    def fetch_yesterday_games(self) -> dict[str, Any]:
        """
        Fetch games from yesterday (commonly used for daily ingestion).

        Returns:
            Dictionary containing yesterday's games data
        """
        yesterday = datetime.utcnow() - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")

        self.logger.info(f"Fetching yesterday's NBA games: {yesterday_str}")
        return self.fetch_games_by_date(yesterday_str)
