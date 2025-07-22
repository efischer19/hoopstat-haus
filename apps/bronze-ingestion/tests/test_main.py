"""Tests for the bronze ingestion main module."""

from unittest.mock import patch

from app.main import ingest_nba_data, main, setup_logging


def test_setup_logging():
    """Test that logging setup runs without error."""
    # This should not raise an exception
    setup_logging()


def test_ingest_nba_data_with_default_date():
    """Test ingest_nba_data function with default date."""
    with patch("app.main.logging") as mock_logging:
        mock_logger = mock_logging.getLogger.return_value

        ingest_nba_data()

        # Verify logging calls were made
        assert mock_logger.info.call_count >= 2
        # Verify the logger was called with expected patterns
        calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("Starting NBA data ingestion for date:" in call for call in calls)
        assert any("Completed NBA data ingestion for date:" in call for call in calls)


def test_ingest_nba_data_with_specific_date():
    """Test ingest_nba_data function with specific date."""
    test_date = "2024-01-15"

    with patch("app.main.logging") as mock_logging:
        mock_logger = mock_logging.getLogger.return_value

        ingest_nba_data(test_date)

        # Verify logging calls were made with the specific date
        calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any(
            f"Starting NBA data ingestion for date: {test_date}" in call
            for call in calls
        )
        assert any(
            f"Completed NBA data ingestion for date: {test_date}" in call
            for call in calls
        )


def test_main_runs_without_error():
    """Test that main function runs without error."""
    with (
        patch("app.main.setup_logging") as mock_setup,
        patch("app.main.ingest_nba_data") as mock_ingest,
    ):

        main()

        # Verify setup_logging was called
        mock_setup.assert_called_once()
        # Verify ingest_nba_data was called
        mock_ingest.assert_called_once()


def test_main_handles_exception():
    """Test that main function properly handles exceptions."""
    with (
        patch("app.main.setup_logging"),
        patch("app.main.ingest_nba_data", side_effect=Exception("Test error")),
        patch("app.main.logging") as mock_logging,
    ):

        mock_logger = mock_logging.getLogger.return_value

        try:
            main()
            raise AssertionError("Expected exception to be raised")
        except Exception as e:
            assert str(e) == "Test error"
            # Verify error was logged
            mock_logger.error.assert_called_once()
            error_call = mock_logger.error.call_args[0][0]
            assert "Data ingestion failed: Test error" in error_call
