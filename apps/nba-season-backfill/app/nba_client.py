"""NBA API client with rate limiting and error handling."""

import logging
import time
from dataclasses import dataclass
from typing import Any

import requests
from nba_api.stats.endpoints import (
    boxscoreadvancedv2,
    boxscoretraditionalv2,
    commonplayerinfo,
    leaguegamefinder,
    playbyplayv2,
    teaminfocommon,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import BackfillConfig


@dataclass
class APIResponse:
    """Wrapper for NBA API responses with metadata."""

    data: Any
    endpoint: str
    game_id: str | None = None
    response_time_ms: float = 0.0
    status_code: int = 200
    error: str | None = None


class RateLimiter:
    """Rate limiter with adaptive behavior."""

    def __init__(self, base_delay_seconds: int = 5):
        self.base_delay = base_delay_seconds
        self.current_delay = base_delay_seconds
        self.last_request_time = 0.0
        self.consecutive_errors = 0
        self.logger = logging.getLogger(__name__)

    def wait(self) -> None:
        """Wait appropriate time before next request."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.current_delay:
            sleep_time = self.current_delay - time_since_last
            self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def adjust_for_response(self, response_time: float, status_code: int) -> None:
        """Adjust rate limiting based on response."""
        if status_code == 429:  # Rate limited
            self.current_delay *= 2
            self.consecutive_errors += 1
            self.logger.warning(
                f"Rate limited, increasing delay to {self.current_delay}s"
            )
        elif status_code >= 500:  # Server error
            self.current_delay *= 1.5
            self.consecutive_errors += 1
            self.logger.warning(
                f"Server error, increasing delay to {self.current_delay}s"
            )
        elif status_code == 200 and response_time < 1.0:
            # Gradually return to base rate on successful fast responses
            self.current_delay = max(self.base_delay, self.current_delay * 0.95)
            self.consecutive_errors = 0

        # Cap maximum delay at 60 seconds
        self.current_delay = min(self.current_delay, 60.0)


class NBAClient:
    """NBA API client with rate limiting and error handling."""

    def __init__(self, config: BackfillConfig):
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit_seconds)
        self.logger = logging.getLogger(__name__)

        # API request statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_requests": 0,
            "total_response_time": 0.0,
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(
            (requests.RequestException, ConnectionError, TimeoutError)
        ),
    )
    def _make_request(self, endpoint_func, **kwargs) -> APIResponse:
        """Make a rate-limited API request with retry logic."""
        self.rate_limiter.wait()

        start_time = time.time()
        endpoint_name = endpoint_func.__name__

        try:
            self.stats["total_requests"] += 1

            # Make the API request
            endpoint = endpoint_func(**kwargs)
            data = endpoint.get_data_frames()

            response_time = (time.time() - start_time) * 1000
            self.stats["total_response_time"] += response_time
            self.stats["successful_requests"] += 1

            # Adjust rate limiting based on successful response
            self.rate_limiter.adjust_for_response(response_time / 1000, 200)

            self.logger.debug(
                "API request successful",
                extra={
                    "endpoint": endpoint_name,
                    "response_time_ms": response_time,
                    "kwargs": kwargs,
                },
            )

            return APIResponse(
                data=data,
                endpoint=endpoint_name,
                game_id=kwargs.get("game_id"),
                response_time_ms=response_time,
                status_code=200,
            )

        except requests.exceptions.HTTPError as e:
            response_time = (time.time() - start_time) * 1000
            self.stats["failed_requests"] += 1

            # Handle specific HTTP status codes
            if hasattr(e.response, "status_code"):
                status_code = e.response.status_code
                if status_code == 429:
                    self.stats["rate_limited_requests"] += 1
                    self.rate_limiter.adjust_for_response(response_time / 1000, 429)
                    self.logger.warning(f"Rate limited on {endpoint_name}")
                elif status_code >= 500:
                    self.rate_limiter.adjust_for_response(
                        response_time / 1000, status_code
                    )
                    self.logger.warning(
                        f"Server error {status_code} on {endpoint_name}"
                    )

            raise

        except Exception as e:
            self.stats["failed_requests"] += 1
            self.logger.error(
                "API request failed",
                extra={"endpoint": endpoint_name, "error": str(e), "kwargs": kwargs},
            )
            raise

    def get_season_games(self, season: str) -> APIResponse:
        """Get all games for a season."""
        self.logger.info(f"Fetching games for season {season}")

        return self._make_request(
            leaguegamefinder.LeagueGameFinder,
            season_nullable=season,
            season_type_nullable="Regular Season",
        )

    def get_game_box_score_traditional(self, game_id: str) -> APIResponse:
        """Get traditional box score for a game."""
        return self._make_request(
            boxscoretraditionalv2.BoxScoreTraditionalV2, game_id=game_id
        )

    def get_game_box_score_advanced(self, game_id: str) -> APIResponse:
        """Get advanced box score for a game."""
        return self._make_request(
            boxscoreadvancedv2.BoxScoreAdvancedV2, game_id=game_id
        )

    def get_game_play_by_play(self, game_id: str) -> APIResponse:
        """Get play-by-play data for a game."""
        return self._make_request(playbyplayv2.PlayByPlayV2, game_id=game_id)

    def get_player_info(self, player_id: str) -> APIResponse:
        """Get player information."""
        return self._make_request(
            commonplayerinfo.CommonPlayerInfo, player_id=player_id
        )

    def get_team_info(self, team_id: str) -> APIResponse:
        """Get team information."""
        return self._make_request(teaminfocommon.TeamInfoCommon, team_id=team_id)

    def get_stats_summary(self) -> dict[str, Any]:
        """Get API usage statistics."""
        avg_response_time = self.stats["total_response_time"] / max(
            self.stats["successful_requests"], 1
        )

        return {
            "total_requests": self.stats["total_requests"],
            "successful_requests": self.stats["successful_requests"],
            "failed_requests": self.stats["failed_requests"],
            "rate_limited_requests": self.stats["rate_limited_requests"],
            "success_rate": (
                self.stats["successful_requests"] / max(self.stats["total_requests"], 1)
            ),
            "average_response_time_ms": avg_response_time,
            "current_rate_limit_delay": self.rate_limiter.current_delay,
        }
