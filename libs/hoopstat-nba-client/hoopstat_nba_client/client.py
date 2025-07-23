"""
NBA API client with rate limiting and error handling.

Implements respectful NBA API interaction following ADR-013 with proper
rate limiting, retry logic, and structured logging per ADR-015.
"""

import time
from typing import Any

from hoopstat_observability import get_logger
from nba_api.stats.endpoints import (
    boxscoreadvancedv2,
    boxscoretraditionalv2,
    commonplayerinfo,
    leaguegamefinder,
    playbyplayv2,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .rate_limiter import RateLimiter

logger = get_logger(__name__)


class NBAClient:
    """
    NBA API client with rate limiting and error handling.

    Provides high-level interface for NBA data collection with proper
    error handling, retries, and observability.
    """

    def __init__(self, rate_limit_seconds: float = 5.0, max_retries: int = 3):
        """
        Initialize NBA API client.

        Args:
            rate_limit_seconds: Base delay between requests
            max_retries: Maximum retry attempts for transient failures
        """
        self.rate_limiter = RateLimiter(rate_limit_seconds)
        self.max_retries = max_retries
        self.session_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limit_hits": 0,
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    )
    def _make_request(self, endpoint_func, **kwargs) -> dict[str, Any]:
        """
        Make rate-limited request to NBA API endpoint.

        Args:
            endpoint_func: NBA API endpoint function to call
            **kwargs: Arguments for the endpoint function

        Returns:
            API response data

        Raises:
            Exception: For permanent errors or after max retries
        """
        self.rate_limiter.wait()

        start_time = time.time()
        self.session_stats["total_requests"] += 1

        try:
            # Make the API request
            response = endpoint_func(**kwargs)
            response_time = time.time() - start_time

            # Get the data
            data = response.get_dict()

            # Adjust rate limiting based on successful response
            self.rate_limiter.adjust_for_response(response_time, 200)
            self.session_stats["successful_requests"] += 1

            logger.debug(
                "NBA API request successful",
                endpoint=getattr(endpoint_func, "__name__", "unknown"),
                response_time=round(response_time, 3),
                data_size=len(str(data)),
            )

            return data

        except Exception as e:
            response_time = time.time() - start_time
            self.session_stats["failed_requests"] += 1

            # Handle rate limiting
            if "429" in str(e) or "rate" in str(e).lower():
                self.rate_limiter.adjust_for_response(response_time, 429)
                self.session_stats["rate_limit_hits"] += 1

            logger.error(
                "NBA API request failed",
                endpoint=getattr(endpoint_func, "__name__", "unknown"),
                error=str(e),
                error_type=type(e).__name__,
                response_time=round(response_time, 3),
            )
            raise

    def get_season_games(self, season: str) -> list[dict[str, Any]]:
        """
        Get all games for a season.

        Args:
            season: Season in format YYYY-YY

        Returns:
            List of game dictionaries
        """
        logger.info("Fetching season games", season=season)

        response = self._make_request(
            leaguegamefinder.LeagueGameFinder,
            season_nullable=season,
            season_type_nullable="Regular Season",
        )

        games = response["resultSets"][0]["rowSet"]

        logger.info(
            "Season games fetched",
            season=season,
            total_games=len(games),
        )

        return games

    def get_box_score_traditional(self, game_id: str) -> dict[str, Any]:
        """
        Get traditional box score for a game.

        Args:
            game_id: NBA game ID

        Returns:
            Box score data
        """
        return self._make_request(
            boxscoretraditionalv2.BoxScoreTraditionalV2,
            game_id=game_id,
        )

    def get_box_score_advanced(self, game_id: str) -> dict[str, Any]:
        """
        Get advanced box score for a game.

        Args:
            game_id: NBA game ID

        Returns:
            Advanced box score data
        """
        return self._make_request(
            boxscoreadvancedv2.BoxScoreAdvancedV2,
            game_id=game_id,
        )

    def get_play_by_play(self, game_id: str) -> dict[str, Any]:
        """
        Get play-by-play data for a game.

        Args:
            game_id: NBA game ID

        Returns:
            Play-by-play data
        """
        return self._make_request(
            playbyplayv2.PlayByPlayV2,
            game_id=game_id,
        )

    def get_player_info(self, player_id: str) -> dict[str, Any]:
        """
        Get player information.

        Args:
            player_id: NBA player ID

        Returns:
            Player information
        """
        return self._make_request(
            commonplayerinfo.CommonPlayerInfo,
            player_id=player_id,
        )

    def get_session_stats(self) -> dict[str, Any]:
        """Get session statistics for monitoring."""
        return self.session_stats.copy()

    def reset_session_stats(self) -> None:
        """Reset session statistics."""
        self.session_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limit_hits": 0,
        }

    def reset_rate_limiter(self) -> None:
        """Reset rate limiter to initial state."""
        self.rate_limiter.reset()