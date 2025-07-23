"""
NBA API client with rate limiting and error handling.
"""

import logging
from datetime import date, datetime
from typing import Any

import requests
from nba_api.stats.endpoints import (
    BoxScoreTraditionalV3,
    CommonPlayerInfo,
    LeagueGameFinder,
    LeagueStandings,
)

from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class NBAAPIError(Exception):
    """Custom exception for NBA API errors."""

    pass


class NBAClient:
    """
    NBA API client with respectful rate limiting and error handling.

    Follows ADR-013 decision to use nba-api library as primary data source.
    """

    def __init__(self, rate_limiter: RateLimiter | None = None):
        """
        Initialize the NBA API client.

        Args:
            rate_limiter: Optional custom rate limiter instance
        """
        self.rate_limiter = rate_limiter or RateLimiter()
        self.session = requests.Session()
        # Set a user agent to be respectful
        self.session.headers.update(
            {"User-Agent": "hoopstat-haus/0.1.0 (Basketball Analytics Project)"}
        )

    def _make_request(self, endpoint_class, **kwargs) -> dict[str, Any]:
        """
        Make a request to the NBA API with rate limiting and error handling.

        Args:
            endpoint_class: NBA API endpoint class to instantiate
            **kwargs: Parameters to pass to the endpoint

        Returns:
            Raw JSON response data

        Raises:
            NBAAPIError: If the request fails after retries
        """
        retry_count = 0
        max_retries = 3

        while retry_count <= max_retries:
            try:
                # Wait for rate limiting
                self.rate_limiter.wait_if_needed()

                # Make the API call
                endpoint = endpoint_class(**kwargs)
                data = endpoint.get_json()

                # Reset rate limiter on success
                self.rate_limiter.reset_delay()

                logger.debug(
                    f"Successfully fetched data from {endpoint_class.__name__}"
                )
                return data

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    if self.rate_limiter.handle_rate_limit_error():
                        retry_count += 1
                        logger.warning(
                            f"Rate limited, retrying "
                            f"(attempt {retry_count}/{max_retries})"
                        )
                        continue
                    else:
                        raise NBAAPIError(
                            f"Rate limit exceeded after {max_retries} retries"
                        ) from e
                else:
                    raise NBAAPIError(
                        f"HTTP error {e.response.status_code}: {e}"
                    ) from e

            except Exception as e:
                retry_count += 1
                if retry_count > max_retries:
                    raise NBAAPIError(
                        f"Failed to fetch data after {max_retries} retries: {e}"
                    ) from e

                logger.warning(
                    f"Request failed, retrying "
                    f"(attempt {retry_count}/{max_retries}): {e}"
                )
                # Simple backoff for non-rate-limit errors
                import time

                time.sleep(min(2**retry_count, 10))

        raise NBAAPIError(f"Failed to fetch data after {max_retries} retries")

    def get_games_for_date(self, target_date: date) -> list[dict[str, Any]]:
        """
        Get all games for a specific date.

        Args:
            target_date: Date to fetch games for

        Returns:
            List of game data dictionaries
        """
        date_str = target_date.strftime("%m/%d/%Y")

        try:
            data = self._make_request(
                LeagueGameFinder,
                date_from_nullable=date_str,
                date_to_nullable=date_str,
                league_id_nullable="00",  # NBA
            )

            games = data.get("resultSet", {}).get("rowSet", [])
            headers = data.get("resultSet", {}).get("headers", [])

            # Convert to list of dictionaries
            games_data = []
            for game_row in games:
                game_dict = dict(zip(headers, game_row, strict=False))
                game_dict["fetch_date"] = datetime.now().isoformat()
                games_data.append(game_dict)

            logger.info(f"Fetched {len(games_data)} games for {target_date}")
            return games_data

        except Exception as e:
            logger.error(f"Failed to fetch games for {target_date}: {e}")
            raise NBAAPIError(f"Failed to fetch games for {target_date}") from e

    def get_box_score(self, game_id: str) -> dict[str, Any]:
        """
        Get detailed box score for a specific game.

        Args:
            game_id: NBA game ID

        Returns:
            Box score data dictionary
        """
        try:
            data = self._make_request(BoxScoreTraditionalV3, game_id=game_id)

            # Add metadata
            data["fetch_date"] = datetime.now().isoformat()
            data["game_id"] = game_id

            logger.debug(f"Fetched box score for game {game_id}")
            return data

        except Exception as e:
            logger.error(f"Failed to fetch box score for game {game_id}: {e}")
            raise NBAAPIError(f"Failed to fetch box score for game {game_id}") from e

    def get_player_info(self, player_id: int) -> dict[str, Any]:
        """
        Get player information.

        Args:
            player_id: NBA player ID

        Returns:
            Player info dictionary
        """
        try:
            data = self._make_request(CommonPlayerInfo, player_id=player_id)

            # Add metadata
            data["fetch_date"] = datetime.now().isoformat()
            data["player_id"] = player_id

            logger.debug(f"Fetched info for player {player_id}")
            return data

        except Exception as e:
            logger.error(f"Failed to fetch info for player {player_id}: {e}")
            raise NBAAPIError(f"Failed to fetch info for player {player_id}") from e

    def get_league_standings(self) -> dict[str, Any]:
        """
        Get current league standings.

        Returns:
            League standings dictionary
        """
        try:
            data = self._make_request(LeagueStandings)

            # Add metadata
            data["fetch_date"] = datetime.now().isoformat()

            logger.debug("Fetched league standings")
            return data

        except Exception as e:
            logger.error(f"Failed to fetch league standings: {e}")
            raise NBAAPIError("Failed to fetch league standings") from e
