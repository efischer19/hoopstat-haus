"""
Tests for state management functionality.
"""

from datetime import datetime

import pytest

from app.state_manager import BackfillState


class TestBackfillState:
    """Test backfill state management."""
    
    def test_state_initialization(self):
        """Test state initialization."""
        state = BackfillState()
        
        assert state.backfill_id.startswith("nba-backfill-")
        assert state.current_season is None
        assert len(state.completed_games) == 0
        assert len(state.failed_games) == 0
        assert state.statistics["total_games_processed"] == 0
    
    def test_state_initialization_with_id(self):
        """Test state initialization with specific ID."""
        custom_id = "test-backfill-123"
        state = BackfillState(backfill_id=custom_id)
        
        assert state.backfill_id == custom_id
    
    def test_set_current_season(self):
        """Test setting current season."""
        state = BackfillState()
        state.set_current_season("2024-25")
        
        assert state.current_season == "2024-25"
    
    def test_mark_game_completed(self):
        """Test marking game as completed."""
        state = BackfillState()
        
        state.mark_game_completed(
            game_id="0022400001",
            files_uploaded=3,
            bytes_stored=1024,
            api_calls=4,
        )
        
        assert state.is_game_completed("0022400001")
        assert not state.is_game_failed("0022400001")
        assert state.statistics["total_games_processed"] == 1
        assert state.statistics["total_files_uploaded"] == 3
        assert state.statistics["total_bytes_stored"] == 1024
        assert state.statistics["total_api_calls"] == 4
    
    def test_mark_game_failed(self):
        """Test marking game as failed."""
        state = BackfillState()
        
        state.mark_game_failed(
            game_id="0022400002",
            error_message="API timeout",
            error_type="TimeoutError",
            retry_count=1,
        )
        
        assert state.is_game_failed("0022400002")
        assert not state.is_game_completed("0022400002")
        assert state.get_failed_game_retry_count("0022400002") == 1
        
        failure_info = state.failed_games["0022400002"]
        assert failure_info["error"] == "API timeout"
        assert failure_info["error_type"] == "TimeoutError"
        assert failure_info["retry_count"] == 1
    
    def test_mark_game_skipped(self):
        """Test marking game as skipped."""
        state = BackfillState()
        
        state.mark_game_skipped("0022400003", "Already processed")
        
        assert "0022400003" in state.skipped_games
    
    def test_failed_to_completed_transition(self):
        """Test transitioning game from failed to completed."""
        state = BackfillState()
        
        # Mark as failed first
        state.mark_game_failed("0022400004", "Network error", "ConnectionError")
        assert state.is_game_failed("0022400004")
        
        # Mark as completed - should remove from failed
        state.mark_game_completed("0022400004")
        assert state.is_game_completed("0022400004")
        assert not state.is_game_failed("0022400004")
        assert "0022400004" not in state.failed_games
    
    def test_get_games_to_retry(self):
        """Test getting games that should be retried."""
        state = BackfillState()
        
        # Add failed games with different retry counts
        state.mark_game_failed("game1", "Error", "Error", retry_count=1)
        state.mark_game_failed("game2", "Error", "Error", retry_count=3)
        state.mark_game_failed("game3", "Error", "Error", retry_count=2)
        
        # Get games to retry with max_retries=3
        retry_games = state.get_games_to_retry(max_retries=3)

        assert "game1" in retry_games
        assert "game2" not in retry_games  # retry_count=3 >= max_retries
        assert "game3" in retry_games

        # Get games to retry with max_retries=2
        retry_games = state.get_games_to_retry(max_retries=2)

        assert "game1" in retry_games
        assert "game2" not in retry_games  # retry_count=3 > max_retries=2
        assert "game3" not in retry_games  # retry_count=2 >= max_retries=2
    
    def test_update_checkpoint(self):
        """Test checkpoint update."""
        state = BackfillState()
        initial_checkpoint = state.last_checkpoint
        
        # Wait a tiny bit to ensure timestamp changes
        import time
        time.sleep(0.01)
        
        state.update_checkpoint()
        
        assert state.last_checkpoint != initial_checkpoint
        assert state.statistics["last_checkpoint_time"] == state.last_checkpoint
    
    def test_get_progress_summary(self):
        """Test progress summary generation."""
        state = BackfillState()
        state.set_current_season("2024-25")
        
        # Add some progress
        state.mark_game_completed("game1")
        state.mark_game_completed("game2")
        state.mark_game_failed("game3", "Error", "Error")
        state.mark_game_skipped("game4", "Duplicate")
        
        summary = state.get_progress_summary(total_games=100)
        
        assert summary["backfill_id"] == state.backfill_id
        assert summary["current_season"] == "2024-25"
        assert summary["progress"]["completed_games"] == 2
        assert summary["progress"]["failed_games"] == 1
        assert summary["progress"]["skipped_games"] == 1
        assert summary["progress"]["total_games"] == 100
        assert summary["progress"]["progress_percentage"] == 2.0
    
    def test_to_dict_and_from_dict(self):
        """Test state serialization and deserialization."""
        # Create state with some data
        original_state = BackfillState("test-id")
        original_state.set_current_season("2024-25")
        original_state.mark_game_completed("game1", files_uploaded=2, bytes_stored=500)
        original_state.mark_game_failed("game2", "Error", "Error", retry_count=1)
        original_state.mark_game_skipped("game3", "Duplicate")
        
        # Convert to dict
        state_dict = original_state.to_dict()
        
        # Verify dict structure
        assert state_dict["backfill_id"] == "test-id"
        assert state_dict["current_season"] == "2024-25"
        assert "game1" in state_dict["completed_games"]
        assert "game2" in state_dict["failed_games"]
        assert "game3" in state_dict["skipped_games"]
        
        # Recreate from dict
        restored_state = BackfillState.from_dict(state_dict)
        
        # Verify restored state
        assert restored_state.backfill_id == original_state.backfill_id
        assert restored_state.current_season == original_state.current_season
        assert restored_state.is_game_completed("game1")
        assert restored_state.is_game_failed("game2")
        assert "game3" in restored_state.skipped_games
        assert restored_state.statistics["total_games_processed"] == 1