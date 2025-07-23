"""
Tests for the bronze ingestion application main module.
"""

import logging
from unittest.mock import Mock, patch

import pytest

from app.main import ingest_nba_data, main, setup_logging


class TestSetupLogging:
    """Test logging configuration."""

    @patch("app.main.logging.basicConfig")
    def test_setup_logging_configuration(self, mock_basic_config):
        """Test that logging is configured correctly."""
        setup_logging()

        mock_basic_config.assert_called_once_with(
            level=logging.INFO,
            format=(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"message": "%(message)s"}'
            ),
            datefmt="%Y-%m-%dT%H:%M:%S.%fZ",
        )


class TestIngestNBAData:
    """Test NBA data ingestion functionality."""

    @patch("app.main.PlayerStatsFetcher")
    @patch("app.main.GamesFetcher")
    @patch("app.main.NBAAPIClient")
    def test_ingest_nba_data_with_date(
        self, mock_client_class, mock_games_fetcher_class, mock_player_fetcher_class
    ):
        """Test data ingestion with specific date."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_games_fetcher = Mock()
        mock_games_fetcher.fetch_games_by_date.return_value = {
            "total_games": 5,
            "games": [],
        }
        mock_games_fetcher_class.return_value = mock_games_fetcher

        mock_player_fetcher = Mock()
        mock_player_fetcher.fetch_player_stats.return_value = {
            "total_players": 20,
            "player_stats": [],
        }
        mock_player_fetcher_class.return_value = mock_player_fetcher

        # Test the function
        ingest_nba_data("2025-01-15")

        # Verify calls
        mock_client_class.assert_called_once()
        mock_games_fetcher_class.assert_called_once_with(mock_client)
        mock_games_fetcher.fetch_games_by_date.assert_called_once_with("2025-01-15")
        mock_player_fetcher_class.assert_called_once_with(mock_client)
        mock_player_fetcher.fetch_player_stats.assert_called_once_with("2025-01-15")

    @patch("app.main.datetime")
    @patch("app.main.PlayerStatsFetcher")
    @patch("app.main.GamesFetcher")
    @patch("app.main.NBAAPIClient")
    def test_ingest_nba_data_default_date(
        self,
        mock_client_class,
        mock_games_fetcher_class,
        mock_player_fetcher_class,
        mock_datetime,
    ):
        """Test data ingestion with default date (yesterday)."""
        # Mock datetime to return a fixed date
        from datetime import UTC, datetime

        fixed_date = datetime(2025, 1, 16, 12, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = fixed_date
        mock_datetime.strftime = datetime.strftime

        # Setup other mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_games_fetcher = Mock()
        mock_games_fetcher.fetch_games_by_date.return_value = {
            "total_games": 3,
            "games": [],
        }
        mock_games_fetcher_class.return_value = mock_games_fetcher

        mock_player_fetcher = Mock()
        mock_player_fetcher.fetch_player_stats.return_value = {
            "total_players": 15,
            "player_stats": [],
        }
        mock_player_fetcher_class.return_value = mock_player_fetcher

        # Test the function
        ingest_nba_data()

        # Verify calls with yesterday's date
        mock_games_fetcher.fetch_games_by_date.assert_called_once_with("2025-01-15")
        mock_player_fetcher.fetch_player_stats.assert_called_once_with("2025-01-15")


class TestMain:
    """Test main function."""

    @patch("app.main.ingest_nba_data")
    @patch("app.main.setup_logging")
    def test_main_success(self, mock_setup_logging, mock_ingest_nba_data):
        """Test successful main execution."""
        main()

        mock_setup_logging.assert_called_once()
        mock_ingest_nba_data.assert_called_once()

    @patch("app.main.ingest_nba_data")
    @patch("app.main.setup_logging")
    def test_main_with_exception(self, mock_setup_logging, mock_ingest_nba_data):
        """Test main execution with exception."""
        mock_ingest_nba_data.side_effect = Exception("Test error")

        with pytest.raises(Exception, match="Test error"):
            main()

        mock_setup_logging.assert_called_once()
        mock_ingest_nba_data.assert_called_once()
