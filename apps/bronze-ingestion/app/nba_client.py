"""NBA API client with retry logic and rate limiting."""

import time
from datetime import datetime

import pandas as pd
from hoopstat_observability import get_logger
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

from .config import BronzeIngestionConfig

logger = get_logger(__name__)


class NBAAPIClient:
    """NBA API client with rate limiting and retry logic."""

    def __init__(self, config: BronzeIngestionConfig):
        """Initialize the NBA API client.

        Args:
            config: Configuration object with rate limiting and retry settings
        """
        self.config = config
        self.last_request_time: float | None = None

    def _rate_limit(self) -> None:
        """Enforce rate limiting between API calls."""
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.config.rate_limit_seconds:
                sleep_time = self.config.rate_limit_seconds - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)

        self.last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),  # Will be configurable
        wait=wait_exponential(multiplier=1, min=1, max=60),  # Will be configurable
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def get_schedule_for_date(self, game_date: str) -> pd.DataFrame:
        """Get NBA schedule for a specific date.

        Args:
            game_date: Date in YYYY-MM-DD format

        Returns:
            DataFrame with game schedule data for the date

        Raises:
            ConnectionError: If API call fails after retries
        """
        self._rate_limit()

        # Convert YYYY-MM-DD to MM/DD/YYYY format expected by NBA API
        date_obj = datetime.strptime(game_date, "%Y-%m-%d")
        nba_api_date = date_obj.strftime("%m/%d/%Y")

        logger.info(f"Fetching NBA schedule for date: {game_date}")

        try:
            scoreboard = scoreboardv2.ScoreboardV2(game_date=nba_api_date)
            games_df = scoreboard.line_score.get_data_frame()

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def get_box_score(self, game_id: str) -> pd.DataFrame:
        """Get box score data for a specific game.

        Args:
            game_id: NBA game ID

        Returns:
            DataFrame with box score data
        """
        self._rate_limit()

        logger.debug(f"Fetching box score for game: {game_id}")

        try:
            box_score = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
            players_df = box_score.player_stats.get_data_frame()

            logger.debug(
                f"Retrieved box score data for game {game_id}: "
                f"{len(players_df)} player records"
            )

            return players_df

        except Exception as e:
            logger.error(f"Failed to fetch box score for game {game_id}: {e}")
            raise ConnectionError(f"NBA API request failed: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def get_play_by_play(self, game_id: str) -> pd.DataFrame:
        """Get play-by-play data for a specific game.

        Args:
            game_id: NBA game ID

        Returns:
            DataFrame with play-by-play data
        """
        self._rate_limit()

        logger.debug(f"Fetching play-by-play for game: {game_id}")

        try:
            play_by_play = playbyplayv3.PlayByPlayV3(game_id=game_id)
            plays_df = play_by_play.plays.get_data_frame()

            logger.debug(
                f"Retrieved play-by-play data for game {game_id}: {len(plays_df)} plays"
            )

            return plays_df

        except Exception as e:
            logger.error(f"Failed to fetch play-by-play for game {game_id}: {e}")
            raise ConnectionError(f"NBA API request failed: {e}") from e
