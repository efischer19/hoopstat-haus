"""Tests for state manager functionality."""

from datetime import datetime

from app.config import BackfillConfig
from app.state_manager import BackfillStats, GameProcessingState, StateManager


class TestGameProcessingState:
    """Test cases for GameProcessingState dataclass."""

    def test_game_state_creation(self):
        """Test creating a game processing state."""
        state = GameProcessingState(
            game_id="0022400001", game_date="2024-10-15", status="pending"
        )

        assert state.game_id == "0022400001"
        assert state.game_date == "2024-10-15"
        assert state.status == "pending"
        assert state.retry_count == 0
        assert state.data_types_completed == []

    def test_game_state_with_retries(self):
        """Test game state with retry information."""
        state = GameProcessingState(
            game_id="0022400001",
            game_date="2024-10-15",
            status="failed",
            retry_count=2,
            error_message="API timeout",
        )

        assert state.retry_count == 2
        assert state.error_message == "API timeout"
        assert state.status == "failed"


class TestBackfillStats:
    """Test cases for BackfillStats dataclass."""

    def test_stats_creation(self):
        """Test creating backfill statistics."""
        start_time = datetime.now().isoformat()
        stats = BackfillStats(
            start_time=start_time,
            last_update=start_time,
            total_games_discovered=100,
            games_completed=50,
        )

        assert stats.start_time == start_time
        assert stats.total_games_discovered == 100
        assert stats.games_completed == 50
        assert stats.games_failed == 0  # default


class TestStateManager:
    """Test cases for StateManager class."""

    def setup_method(self):
        """Setup test configuration."""
        self.config = BackfillConfig(
            aws_region="us-east-1",
            s3_bucket_name="test-bucket",
            season="2024-25",
            checkpoint_frequency=5,
        )

    def test_state_manager_initialization(self):
        """Test state manager initialization."""
        manager = StateManager(self.config)

        assert manager.config == self.config
        assert len(manager.games) == 0
        assert manager.stats.games_completed == 0
        assert manager.checkpoint_counter == 0

    def test_add_discovered_games(self):
        """Test adding discovered games to state."""
        manager = StateManager(self.config)

        games_data = [
            {"GAME_ID": "0022400001", "GAME_DATE": "2024-10-15"},
            {"GAME_ID": "0022400002", "GAME_DATE": "2024-10-16"},
        ]

        manager.add_discovered_games(games_data)

        assert len(manager.games) == 2
        assert "0022400001" in manager.games
        assert "0022400002" in manager.games
        assert manager.stats.total_games_discovered == 2
        assert manager.stats.games_pending == 2

    def test_mark_game_completed(self):
        """Test marking a game as completed."""
        manager = StateManager(self.config)

        # Add a game first
        manager.games["0022400001"] = GameProcessingState(
            game_id="0022400001", game_date="2024-10-15", status="pending"
        )
        manager.stats.games_pending = 1

        # Mark as completed
        manager.mark_game_completed("0022400001", ["box-scores", "play-by-play"])

        game = manager.games["0022400001"]
        assert game.status == "completed"
        assert game.data_types_completed == ["box-scores", "play-by-play"]
        assert manager.stats.games_completed == 1
        assert manager.stats.games_pending == 0

    def test_mark_game_failed(self):
        """Test marking a game as failed."""
        manager = StateManager(self.config)

        # Add a game first
        manager.games["0022400001"] = GameProcessingState(
            game_id="0022400001", game_date="2024-10-15", status="pending"
        )
        manager.stats.games_pending = 1

        # Mark as failed
        manager.mark_game_failed("0022400001", "API timeout")

        game = manager.games["0022400001"]
        assert game.retry_count == 1
        assert game.error_message == "API timeout"
        assert game.status == "pending"  # Still pending for retry

    def test_mark_game_permanently_failed(self):
        """Test marking a game as permanently failed after max retries."""
        manager = StateManager(self.config)

        # Add a game with max retries
        manager.games["0022400001"] = GameProcessingState(
            game_id="0022400001",
            game_date="2024-10-15",
            status="pending",
            retry_count=2,  # One less than max
        )
        manager.stats.games_pending = 1

        # Mark as failed again
        manager.mark_game_failed("0022400001", "Permanent failure")

        game = manager.games["0022400001"]
        assert game.retry_count == 3  # At max retries
        assert game.status == "failed"
        assert manager.stats.games_failed == 1
        assert manager.stats.games_pending == 0

    def test_get_next_games_to_process(self):
        """Test getting next games for processing."""
        manager = StateManager(self.config)

        # Add games with different retry counts
        manager.games["0022400001"] = GameProcessingState(
            game_id="0022400001",
            game_date="2024-10-15",
            status="pending",
            retry_count=2,
        )
        manager.games["0022400002"] = GameProcessingState(
            game_id="0022400002",
            game_date="2024-10-16",
            status="pending",
            retry_count=0,
        )
        manager.games["0022400003"] = GameProcessingState(
            game_id="0022400003", game_date="2024-10-17", status="completed"
        )

        next_games = manager.get_next_games_to_process(batch_size=2)

        assert len(next_games) == 2
        # Should prioritize game with fewer retries
        assert next_games[0].game_id == "0022400002"
        assert next_games[1].game_id == "0022400001"

    def test_should_save_checkpoint(self):
        """Test checkpoint saving logic."""
        manager = StateManager(self.config)

        # Should not save initially
        assert not manager.should_save_checkpoint()

        # Should save after checkpoint frequency
        for _ in range(4):
            manager.should_save_checkpoint()

        assert manager.should_save_checkpoint()  # 5th call

    def test_checkpoint_counter_reset(self):
        """Test resetting checkpoint counter."""
        manager = StateManager(self.config)

        # Increment counter
        for _ in range(3):
            manager.should_save_checkpoint()

        assert manager.checkpoint_counter == 3

        manager.reset_checkpoint_counter()
        assert manager.checkpoint_counter == 0

    def test_update_api_stats(self):
        """Test updating API and storage statistics."""
        manager = StateManager(self.config)

        manager.update_api_stats(api_calls=10, files_stored=5, bytes_stored=1024)

        assert manager.stats.total_api_calls == 10
        assert manager.stats.total_files_stored == 5
        assert manager.stats.total_bytes_stored == 1024

    def test_get_progress_summary(self):
        """Test getting progress summary."""
        manager = StateManager(self.config)

        # Add some games
        manager.games["0022400001"] = GameProcessingState(
            game_id="0022400001", game_date="2024-10-15", status="completed"
        )
        manager.games["0022400002"] = GameProcessingState(
            game_id="0022400002", game_date="2024-10-16", status="pending"
        )

        manager.stats.games_completed = 1
        manager.stats.games_pending = 1

        summary = manager.get_progress_summary()

        assert summary["total_games"] == 2
        assert summary["completed_games"] == 1
        assert summary["pending_games"] == 1
        assert summary["completion_percentage"] == 50.0

    def test_to_dict_serialization(self):
        """Test converting state to dictionary."""
        manager = StateManager(self.config)

        # Add a game
        manager.games["0022400001"] = GameProcessingState(
            game_id="0022400001", game_date="2024-10-15", status="pending"
        )

        state_dict = manager.to_dict()

        assert "backfill_id" in state_dict
        assert "season" in state_dict
        assert "games" in state_dict
        assert "stats" in state_dict
        assert "checkpoint_metadata" in state_dict
        assert "0022400001" in state_dict["games"]

    def test_load_existing_state(self):
        """Test loading state from existing data."""
        manager = StateManager(self.config)

        existing_state = {
            "backfill_id": "test-backfill",
            "games": {
                "0022400001": {
                    "game_id": "0022400001",
                    "game_date": "2024-10-15",
                    "status": "completed",
                    "retry_count": 0,
                    "last_attempt": None,
                    "error_message": None,
                    "data_types_completed": ["box-scores"],
                }
            },
            "stats": {
                "start_time": "2024-01-01T00:00:00",
                "last_update": "2024-01-01T01:00:00",
                "total_games_discovered": 1,
                "games_completed": 1,
                "games_failed": 0,
                "games_pending": 0,
            },
        }

        success = manager.load_existing_state(existing_state)

        assert success
        assert manager.backfill_id == "test-backfill"
        assert len(manager.games) == 1
        assert manager.games["0022400001"].status == "completed"
        assert manager.stats.games_completed == 1

    def test_validate_state_integrity(self):
        """Test state integrity validation."""
        manager = StateManager(self.config)

        # Add games
        manager.games["0022400001"] = GameProcessingState(
            game_id="0022400001", game_date="2024-10-15", status="completed"
        )
        manager.games["0022400002"] = GameProcessingState(
            game_id="0022400002", game_date="2024-10-16", status="pending"
        )

        # Set correct stats
        manager.stats.games_completed = 1
        manager.stats.games_pending = 1
        manager.stats.games_failed = 0

        issues = manager.validate_state_integrity()
        assert len(issues) == 0  # No issues

        # Create inconsistency
        manager.stats.games_completed = 2  # Wrong count

        issues = manager.validate_state_integrity()
        assert len(issues) == 1
        assert "Completed games count mismatch" in issues[0]
