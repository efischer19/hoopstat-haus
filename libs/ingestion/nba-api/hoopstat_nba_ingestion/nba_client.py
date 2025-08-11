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

# Optional imports for bronze-ingestion compatibility
try:
    import pandas as pd
    from nba_api.stats.endpoints import (
        boxscoretraditionalv2,
        playbyplayv3,
        scoreboardv2,
    )
    from tenacity import (
        retry,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential,
    )
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from hoopstat_observability import get_logger
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class NBAAPIError(Exception):
    """Custom exception for NBA API errors."""

    pass


class NBAClient:
    """
    NBA API client with respectful rate limiting and error handling.

    Follows ADR-013 decision to use nba-api library as primary data source.
    Enhanced to support bronze-ingestion app specific endpoints with DataFrame returns.
    """

    def __init__(self, rate_limiter: RateLimiter | None = None, config: Any = None):
        """
        Initialize the NBA API client.

        Args:
            rate_limiter: Optional custom rate limiter instance
            config: Optional configuration object with retry settings
        """
        self.rate_limiter = rate_limiter or RateLimiter()
        self.config = config
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

                endpoint_name = getattr(endpoint_class, "__name__", str(endpoint_class))
                logger.debug(f"Successfully fetched data from {endpoint_name}")
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

    # Bronze-ingestion specific methods that return DataFrames

    def get_schedule_for_date(self, game_date: str):
        """Get NBA schedule for a specific date (bronze-ingestion method).

        Args:
            game_date: Date in YYYY-MM-DD format

        Returns:
            DataFrame with game schedule data for the date

        Raises:
            ConnectionError: If API call fails after retries
            ImportError: If pandas is not available
        """
        if not HAS_PANDAS:
            raise ImportError("pandas is required for DataFrame methods")
        
        return self._get_schedule_for_date_impl(game_date)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def _get_schedule_for_date_impl(self, game_date: str):
        """Implementation of get_schedule_for_date."""
        self.rate_limiter.wait_if_needed()

        # Convert YYYY-MM-DD to MM/DD/YYYY format expected by NBA API
        date_obj = datetime.strptime(game_date, "%Y-%m-%d")
        nba_api_date = date_obj.strftime("%m/%d/%Y")

        logger.info(f"Fetching NBA schedule for date: {game_date}")

        try:
            scoreboard = scoreboardv2.ScoreboardV2(game_date=nba_api_date)
            games_df = scoreboard.line_score.get_data_frame()

            # Reset rate limiter delay on success
            self.rate_limiter.reset_delay()

            logger.info(
                "Retrieved schedule data",
                extra={
                    "game_date": game_date,
                    "games_found": len(games_df) // 2
                    if len(games_df) > 0
                    else 0,  # 2 rows per game
                    "total_records": len(games_df),
                },
            )

            return games_df

        except Exception as e:
            logger.error(f"Failed to fetch schedule for {game_date}: {e}")
            raise ConnectionError(f"NBA API request failed: {e}") from e

    def get_box_score_dataframe(self, game_id: str):
        """Get box score data for a specific game (bronze-ingestion method).

        Args:
            game_id: NBA game ID

        Returns:
            DataFrame with box score data

        Raises:
            ImportError: If pandas is not available
        """
        if not HAS_PANDAS:
            raise ImportError("pandas is required for DataFrame methods")
        
        return self._get_box_score_dataframe_impl(game_id)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def _get_box_score_dataframe_impl(self, game_id: str):
        """Implementation of get_box_score_dataframe."""
        self.rate_limiter.wait_if_needed()

        logger.debug(f"Fetching box score for game: {game_id}")

        try:
            box_score = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
            players_df = box_score.player_stats.get_data_frame()

            # Reset rate limiter delay on success
            self.rate_limiter.reset_delay()

            logger.debug(
                f"Retrieved box score data for game {game_id}: "
                f"{len(players_df)} player records"
            )

            return players_df

        except Exception as e:
            logger.error(f"Failed to fetch box score for game {game_id}: {e}")
            raise ConnectionError(f"NBA API request failed: {e}") from e

    def get_play_by_play_dataframe(self, game_id: str):
        """Get play-by-play data for a specific game (bronze-ingestion method).

        Args:
            game_id: NBA game ID

        Returns:
            DataFrame with play-by-play data

        Raises:
            ImportError: If pandas is not available
        """
        if not HAS_PANDAS:
            raise ImportError("pandas is required for DataFrame methods")
        
        return self._get_play_by_play_dataframe_impl(game_id)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def _get_play_by_play_dataframe_impl(self, game_id: str):
        """Implementation of get_play_by_play_dataframe."""
        self.rate_limiter.wait_if_needed()

        logger.debug(f"Fetching play-by-play for game: {game_id}")

        try:
            play_by_play = playbyplayv3.PlayByPlayV3(game_id=game_id)
            plays_df = play_by_play.plays.get_data_frame()

            # Reset rate limiter delay on success
            self.rate_limiter.reset_delay()

            logger.debug(
                f"Retrieved play-by-play data for game {game_id}: {len(plays_df)} plays"
            )

            return plays_df

        except Exception as e:
            logger.error(f"Failed to fetch play-by-play for game {game_id}: {e}")
            raise ConnectionError(f"NBA API request failed: {e}") from e
