"""
Integration tests for the complete backfill application.
"""

from unittest.mock import Mock, patch

import pytest

from app.backfill_runner import BackfillRunner
from app.config import BackfillConfig


class TestBackfillRunnerIntegration:
    """Integration tests for the complete backfill process."""

    @pytest.fixture
    def dry_run_config(self):
        """Create configuration for dry run testing."""
        return BackfillConfig(
            target_season="2024-25",
            rate_limit_seconds=1.0,  # Minimum allowed for testing
            dry_run=True,
            checkpoint_frequency=2,  # Frequent checkpoints for testing
            collect_box_scores=True,
            collect_play_by_play=True,
            collect_player_info=False,  # Skip for simplicity
        )

    def test_dry_run_execution(self, dry_run_config):
        """Test complete dry run execution."""
        runner = BackfillRunner(dry_run_config)
        result = runner.run()

        # Verify successful completion
        assert result["completion_status"] == "success"
        assert "progress" in result
        assert "api_statistics" in result

        # In dry run, should process mock games
        progress = result["progress"]
        assert progress["completed_games"] > 0
        assert progress["total_games"] > 0

    @patch("app.backfill_runner.NBAClient")
    @patch("app.backfill_runner.S3Client")
    def test_real_mode_with_mocks(self, mock_s3_class, mock_nba_class, dry_run_config):
        """Test execution with mocked dependencies."""
        # Update config for real mode
        config_dict = dry_run_config.model_dump()
        config_dict["dry_run"] = False
        config_dict["checkpoint_frequency"] = 1  # Save after each game
        config = BackfillConfig(**config_dict)

        # Mock NBA client
        mock_nba = Mock()
        mock_nba.get_season_games.return_value = [
            [None, None, "0022400001", None, None, "2024-10-15"],
            [None, None, "0022400002", None, None, "2024-10-16"],
        ]
        mock_nba.get_box_score_traditional.return_value = {
            "resultSets": [
                {
                    "headers": ["PLAYER_ID", "PLAYER_NAME", "PTS"],
                    "rowSet": [[123, "Test Player", 25]],
                }
            ]
        }
        mock_nba.get_box_score_advanced.return_value = {
            "resultSets": [
                {
                    "headers": ["PLAYER_ID", "PLAYER_NAME", "PIE"],
                    "rowSet": [[123, "Test Player", 0.15]],
                }
            ]
        }
        mock_nba.get_play_by_play.return_value = {
            "resultSets": [
                {
                    "headers": ["EVENTNUM", "EVENTMSGTYPE", "DESCRIPTION"],
                    "rowSet": [[1, 12, "Start Period"]],
                }
            ]
        }
        mock_nba.get_session_stats.return_value = {
            "total_requests": 6,
            "successful_requests": 6,
            "failed_requests": 0,
            "rate_limit_hits": 0,
        }
        mock_nba_class.return_value = mock_nba

        # Mock S3 client
        mock_s3 = Mock()
        mock_s3.download_state_file.return_value = None  # No existing state
        mock_s3.upload_game_data.return_value = "s3://test/key"
        mock_s3_class.return_value = mock_s3

        runner = BackfillRunner(config)
        result = runner.run()

        # Verify successful completion
        assert result["completion_status"] == "success"

        # Verify NBA client calls
        assert mock_nba.get_season_games.called
        assert mock_nba.get_box_score_traditional.call_count == 2
        assert mock_nba.get_box_score_advanced.call_count == 2
        assert mock_nba.get_play_by_play.call_count == 2

        # Verify S3 uploads (3 data types × 2 games = 6 uploads)
        assert mock_s3.upload_game_data.call_count == 6

        # Verify state saves (1 per game + final = 3 saves)
        assert mock_s3.upload_state_file.call_count >= 2

    @patch("app.backfill_runner.NBAClient")
    @patch("app.backfill_runner.S3Client")
    def test_resume_from_checkpoint(self, mock_s3_class, mock_nba_class):
        """Test resuming from existing checkpoint."""
        config = BackfillConfig(
            target_season="2024-25",
            dry_run=False,
            resume_from_checkpoint=True,
        )

        # Mock existing state
        existing_state = {
            "backfill_id": "test-resume-123",
            "start_time": "2024-01-01T00:00:00Z",
            "last_checkpoint": "2024-01-01T00:30:00Z",
            "current_season": "2024-25",
            "completed_games": ["0022400001"],  # One game already done
            "failed_games": {},
            "skipped_games": [],
            "statistics": {
                "total_games_processed": 1,
                "total_api_calls": 3,
                "total_bytes_stored": 1024,
                "total_files_uploaded": 3,
            },
            "config_snapshot": config.model_dump(),
        }

        # Mock S3 client
        mock_s3 = Mock()
        mock_s3.download_state_file.return_value = existing_state
        mock_s3.upload_game_data.return_value = "s3://test/key"
        mock_s3_class.return_value = mock_s3

        # Mock NBA client
        mock_nba = Mock()
        mock_nba.get_season_games.return_value = [
            [None, None, "0022400001", None, None, "2024-10-15"],  # Already completed
            [None, None, "0022400002", None, None, "2024-10-16"],  # Need to process
        ]
        mock_nba.get_box_score_traditional.return_value = {
            "resultSets": [{"headers": [], "rowSet": []}]
        }
        mock_nba.get_box_score_advanced.return_value = {
            "resultSets": [{"headers": [], "rowSet": []}]
        }
        mock_nba.get_play_by_play.return_value = {
            "resultSets": [{"headers": [], "rowSet": []}]
        }
        mock_nba.get_session_stats.return_value = {
            "total_requests": 3,
            "successful_requests": 3,
            "failed_requests": 0,
            "rate_limit_hits": 0,
        }
        mock_nba_class.return_value = mock_nba

        runner = BackfillRunner(config)
        result = runner.run()

        # Verify resume behavior
        assert result["completion_status"] == "success"
        assert result["backfill_id"] == "test-resume-123"

        # Should only process the second game (first was already completed)
        assert mock_nba.get_box_score_traditional.call_count == 1
        assert mock_nba.get_box_score_advanced.call_count == 1
        assert mock_nba.get_play_by_play.call_count == 1

    @patch("app.backfill_runner.NBAClient")
    @patch("app.backfill_runner.S3Client")
    def test_nba_api_failure_handling(self, mock_s3_class, mock_nba_class):
        """Test handling of NBA API failures."""
        config = BackfillConfig(
            target_season="2024-25",
            dry_run=False,
            max_retries=1,  # Limited retries for testing
        )

        # Mock S3 client to avoid credentials issue
        mock_s3 = Mock()
        mock_s3_class.return_value = mock_s3

        # Mock NBA client with failure
        mock_nba = Mock()
        mock_nba.get_season_games.side_effect = Exception("API unavailable")
        mock_nba_class.return_value = mock_nba

        runner = BackfillRunner(config)
        result = runner.run()

        # Should handle failure gracefully
        assert result["completion_status"] == "failed"
        assert "error" in result
        assert result["error"] == "API unavailable"

    def test_config_validation_in_runner(self):
        """Test configuration validation in runner initialization."""
        # Valid config should work
        valid_config = BackfillConfig(target_season="2024-25")
        runner = BackfillRunner(valid_config)
        assert runner.config.target_season == "2024-25"

        # Test that runner properly uses config
        assert runner.config.rate_limit_seconds == 5.0  # Default value
