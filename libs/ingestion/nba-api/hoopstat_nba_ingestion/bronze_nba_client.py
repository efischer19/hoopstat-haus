"""Bronze-ingestion specific NBA API client wrapper."""

from .nba_client import NBAClient

try:
    from hoopstat_observability import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class NBAAPIClient:
    """NBA API client wrapper for bronze-ingestion app compatibility."""

    def __init__(self, config):
        """Initialize the NBA API client.

        Args:
            config: Configuration object with rate limiting and retry settings
        """
        self.config = config
        # Use the library's enhanced NBA client
        self.nba_client = NBAClient(config=config)

    def get_schedule_for_date(self, game_date: str):
        """Get NBA schedule for a specific date.

        Args:
            game_date: Date in YYYY-MM-DD format

        Returns:
            DataFrame with game schedule data for the date
        """
        return self.nba_client.get_schedule_for_date(game_date)

    def get_box_score(self, game_id: str):
        """Get box score data for a specific game.

        Args:
            game_id: NBA game ID

        Returns:
            DataFrame with box score data
        """
        return self.nba_client.get_box_score_dataframe(game_id)

    def get_play_by_play(self, game_id: str):
        """Get play-by-play data for a specific game.

        Args:
            game_id: NBA game ID

        Returns:
            DataFrame with play-by-play data
        """
        return self.nba_client.get_play_by_play_dataframe(game_id)