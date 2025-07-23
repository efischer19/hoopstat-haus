"""
Bronze Layer Data Ingestion Application for Hoopstat Haus.

This application handles the ingestion of NBA data from various sources
into the Bronze layer of our Medallion Architecture. It fetches raw data
from the NBA API and stores it in S3 as Parquet files.
"""

import logging
from datetime import UTC, datetime

from hoopstat_nba_api import GamesFetcher, NBAAPIClient, PlayerStatsFetcher


def setup_logging() -> None:
    """Configure structured logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format=(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"message": "%(message)s"}'
        ),
        datefmt="%Y-%m-%dT%H:%M:%S.%fZ",
    )


def ingest_nba_data(date: str | None = None) -> None:
    """
    Ingest NBA data for the specified date.

    Args:
        date: Date to ingest data for in YYYY-MM-DD format.
              Defaults to previous day if not specified.
    """
    logger = logging.getLogger(__name__)

    if date is None:
        # Default to previous day for daily ingestion
        from datetime import timedelta

        yesterday = datetime.now(UTC) - timedelta(days=1)
        date = yesterday.strftime("%Y-%m-%d")

    logger.info(f"Starting NBA data ingestion for date: {date}")

    # Initialize NBA API client
    client = NBAAPIClient()
    logger.info("NBA API client initialized successfully")

    try:
        # Fetch games data using the shared library
        games_fetcher = GamesFetcher(client)
        games_data = games_fetcher.fetch_games_by_date(date)
        logger.info(f"Fetched {games_data['total_games']} games for {date}")

        # Fetch player statistics using the shared library
        player_fetcher = PlayerStatsFetcher(client)
        player_stats = player_fetcher.fetch_player_stats(date)
        logger.info(f"Fetched stats for {player_stats['total_players']} players")

        # TODO: Convert to Parquet format and upload to S3
        logger.info("Converting to Parquet format - placeholder")
        logger.info("Uploading to S3 Bronze layer - placeholder")

    except Exception as e:
        logger.error(f"Failed to fetch NBA data: {str(e)}")
        raise

    logger.info(f"Completed NBA data ingestion for date: {date}")


def main() -> None:
    """Main entry point for the bronze ingestion application."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Bronze Layer Data Ingestion Application Starting")

    try:
        ingest_nba_data()
        logger.info("Data ingestion completed successfully")
    except Exception as e:
        logger.error(f"Data ingestion failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
