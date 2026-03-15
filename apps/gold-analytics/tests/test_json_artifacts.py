"""
Tests for JSON artifact generation and S3 writing.

These tests validate the JSON artifact writer functionality including:
- Player daily artifact generation
- Team daily artifact generation
- Top lists generation
- Latest index generation
- S3 writing with moto mocking
- Error handling scenarios
"""

import json
from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest
from moto import mock_aws

from app.json_artifacts import JSONArtifactWriter


class TestJSONArtifactWriter:
    """Test cases for JSON artifact writer."""

    @pytest.fixture
    def mock_s3(self):
        """Mock S3 for testing."""
        with mock_aws():
            import boto3

            # Create mock S3 bucket
            s3_client = boto3.client("s3", region_name="us-east-1")
            s3_client.create_bucket(Bucket="test-gold-bucket")
            yield s3_client

    @pytest.fixture
    def writer(self, mock_s3):
        """Create JSONArtifactWriter instance for testing."""
        return JSONArtifactWriter("test-gold-bucket", "us-east-1")

    @pytest.fixture
    def sample_player_analytics(self):
        """Sample player analytics data for testing."""
        return pd.DataFrame(
            {
                "player_id": ["player_001", "player_002"],
                "player_name": ["Test Player One", "Test Player Two"],
                "team": ["TEAM1", "TEAM2"],
                "position": ["F", "G"],
                "points": [25, 30],
                "rebounds": [8, 5],
                "assists": [7, 6],
                "steals": [2, 3],
                "blocks": [1, 0],
                "turnovers": [3, 2],
                "field_goals_made": [10, 11],
                "field_goals_attempted": [18, 20],
                "three_pointers_made": [2, 5],
                "three_pointers_attempted": [6, 12],
                "free_throws_made": [3, 3],
                "free_throws_attempted": [4, 4],
                "minutes_played": [35.0, 32.0],
                "efficiency_rating": [22.5, 25.8],
                "true_shooting_percentage": [0.58, 0.65],
                "usage_rate": [0.28, 0.32],
                "plus_minus": [5, 8],
            }
        )

    @pytest.fixture
    def sample_team_analytics(self):
        """Sample team analytics data for testing."""
        return pd.DataFrame(
            {
                "team_id": ["team_001", "team_002"],
                "team_name": ["Test Team One", "Test Team Two"],
                "points": [110, 115],
                "field_goals_made": [42, 45],
                "field_goals_attempted": [85, 88],
                "three_pointers_made": [12, 15],
                "three_pointers_attempted": [35, 38],
                "free_throws_made": [14, 10],
                "free_throws_attempted": [18, 12],
                "rebounds": [44, 42],
                "assists": [25, 28],
                "steals": [8, 10],
                "blocks": [5, 3],
                "turnovers": [15, 12],
                "fouls": [20, 18],
                "offensive_rating": [115.3, 118.7],
                "defensive_rating": [110.5, 108.2],
                "pace": [102.3, 104.1],
                "true_shooting_percentage": [0.58, 0.65],
                "home_game": [True, False],
                "win": [True, True],
            }
        )

    def test_writer_initialization(self, mock_s3):
        """Test JSONArtifactWriter initialization."""
        writer = JSONArtifactWriter("test-bucket", "us-west-2")

        assert writer.gold_bucket == "test-bucket"
        assert writer.aws_region == "us-west-2"
        assert writer.s3_client is not None

    def test_write_player_daily_artifacts(
        self, writer, mock_s3, sample_player_analytics
    ):
        """Test writing player daily artifacts to S3."""
        target_date = date(2024, 1, 15)

        success = writer.write_player_daily_artifacts(
            sample_player_analytics, target_date
        )

        assert success is True

        # Verify files were written to S3
        response = mock_s3.list_objects_v2(
            Bucket="test-gold-bucket", Prefix="served/player_daily/2024-01-15/"
        )

        assert "Contents" in response
        assert len(response["Contents"]) == 2  # Two players

        # Verify file names
        keys = [obj["Key"] for obj in response["Contents"]]
        assert "served/player_daily/2024-01-15/player_001.json" in keys
        assert "served/player_daily/2024-01-15/player_002.json" in keys

    def test_write_player_daily_artifacts_validates_json(
        self, writer, mock_s3, sample_player_analytics
    ):
        """Test that player daily artifacts contain valid JSON."""
        target_date = date(2024, 1, 15)

        writer.write_player_daily_artifacts(sample_player_analytics, target_date)

        # Read and validate JSON
        response = mock_s3.get_object(
            Bucket="test-gold-bucket",
            Key="served/player_daily/2024-01-15/player_001.json",
        )
        content = response["Body"].read().decode("utf-8")
        data = json.loads(content)

        # Verify expected fields
        assert data["player_id"] == "player_001"
        assert data["player_name"] == "Test Player One"
        assert data["points"] == 25
        assert data["rebounds"] == 8
        assert data["efficiency_rating"] == 22.5

    def test_write_team_daily_artifacts(self, writer, mock_s3, sample_team_analytics):
        """Test writing team daily artifacts to S3."""
        target_date = date(2024, 1, 15)

        success = writer.write_team_daily_artifacts(sample_team_analytics, target_date)

        assert success is True

        # Verify files were written to S3
        response = mock_s3.list_objects_v2(
            Bucket="test-gold-bucket", Prefix="served/team_daily/2024-01-15/"
        )

        assert "Contents" in response
        assert len(response["Contents"]) == 2  # Two teams

    def test_write_team_daily_artifacts_validates_json(
        self, writer, mock_s3, sample_team_analytics
    ):
        """Test that team daily artifacts contain valid JSON."""
        target_date = date(2024, 1, 15)

        writer.write_team_daily_artifacts(sample_team_analytics, target_date)

        # Read and validate JSON
        response = mock_s3.get_object(
            Bucket="test-gold-bucket",
            Key="served/team_daily/2024-01-15/team_001.json",
        )
        content = response["Body"].read().decode("utf-8")
        data = json.loads(content)

        # Verify expected fields
        assert data["team_id"] == "team_001"
        assert data["team_name"] == "Test Team One"
        assert data["points"] == 110
        assert data["offensive_rating"] == 115.3

    def test_write_top_lists(self, writer, mock_s3, sample_player_analytics):
        """Test writing top lists to S3."""
        target_date = date(2024, 1, 15)

        success = writer.write_top_lists(sample_player_analytics, target_date)

        assert success is True

        # Verify top lists were written
        response = mock_s3.list_objects_v2(
            Bucket="test-gold-bucket", Prefix="served/top_lists/2024-01-15/"
        )

        assert "Contents" in response
        keys = [obj["Key"] for obj in response["Contents"]]

        # Check for expected metric files
        assert "served/top_lists/2024-01-15/points.json" in keys
        assert "served/top_lists/2024-01-15/efficiency_rating.json" in keys
        assert "served/top_lists/2024-01-15/true_shooting_percentage.json" in keys

    def test_write_top_lists_validates_content(
        self, writer, mock_s3, sample_player_analytics
    ):
        """Test that top lists contain valid content."""
        target_date = date(2024, 1, 15)

        writer.write_top_lists(sample_player_analytics, target_date)

        # Read and validate points top list
        response = mock_s3.get_object(
            Bucket="test-gold-bucket", Key="served/top_lists/2024-01-15/points.json"
        )
        content = response["Body"].read().decode("utf-8")
        data = json.loads(content)

        # Verify structure
        assert data["metric"] == "Points Leaders"
        assert data["date"] == "2024-01-15"
        assert "players" in data
        assert len(data["players"]) == 2

        # Verify top player (player_002 with 30 points)
        assert data["players"][0]["rank"] == 1
        assert data["players"][0]["player_id"] == "player_002"
        assert data["players"][0]["value"] == 30

    def test_write_latest_index(self, writer, mock_s3):
        """Test writing latest index to S3."""
        target_date = date(2024, 1, 15)

        success = writer.write_latest_index(target_date)

        assert success is True

        # Verify index was written
        response = mock_s3.get_object(
            Bucket="test-gold-bucket", Key="served/index/latest.json"
        )
        assert response is not None

    def test_write_latest_index_validates_content(self, writer, mock_s3):
        """Test that latest index contains valid content."""
        target_date = date(2024, 1, 15)

        writer.write_latest_index(target_date)

        # Read and validate index
        response = mock_s3.get_object(
            Bucket="test-gold-bucket", Key="served/index/latest.json"
        )
        content = response["Body"].read().decode("utf-8")
        data = json.loads(content)

        # Verify structure
        assert data["latest_date"] == "2024-01-15"
        assert "available_data" in data
        assert "player_daily" in data["available_data"]
        assert "team_daily" in data["available_data"]
        assert "top_lists" in data["available_data"]

    def test_write_empty_player_analytics(self, writer, mock_s3):
        """Test writing empty player analytics returns True."""
        empty_df = pd.DataFrame()
        target_date = date(2024, 1, 15)

        success = writer.write_player_daily_artifacts(empty_df, target_date)

        assert success is True

        # Verify no files were written
        response = mock_s3.list_objects_v2(
            Bucket="test-gold-bucket", Prefix="served/player_daily/2024-01-15/"
        )
        assert "Contents" not in response

    def test_write_empty_team_analytics(self, writer, mock_s3):
        """Test writing empty team analytics returns True."""
        empty_df = pd.DataFrame()
        target_date = date(2024, 1, 15)

        success = writer.write_team_daily_artifacts(empty_df, target_date)

        assert success is True

        # Verify no files were written
        response = mock_s3.list_objects_v2(
            Bucket="test-gold-bucket", Prefix="served/team_daily/2024-01-15/"
        )
        assert "Contents" not in response

    def test_player_artifact_missing_player_id(self, writer, mock_s3):
        """Test handling of player row missing player_id."""
        bad_data = pd.DataFrame(
            {
                "player_name": ["Test Player"],
                "points": [20],
                # Missing player_id
            }
        )
        target_date = date(2024, 1, 15)

        # Should skip row with warning but not fail
        success = writer.write_player_daily_artifacts(bad_data, target_date)

        assert success is True

    def test_team_artifact_missing_team_id(self, writer, mock_s3):
        """Test handling of team row missing team_id."""
        bad_data = pd.DataFrame(
            {
                "team_name": ["Test Team"],
                "points": [100],
                # Missing team_id
            }
        )
        target_date = date(2024, 1, 15)

        # Should skip row with warning but not fail
        success = writer.write_team_daily_artifacts(bad_data, target_date)

        assert success is True

    def test_s3_upload_error_handling(self, writer):
        """Test error handling when S3 upload fails."""
        sample_data = pd.DataFrame(
            {
                "player_id": ["123"],
                "player_name": ["Test Player"],
                "team": ["TST"],
                "points": [20],
                "rebounds": [5],
                "assists": [3],
                "steals": [1],
                "blocks": [0],
                "turnovers": [2],
            }
        )
        target_date = date(2024, 1, 15)

        # Mock S3 client to raise error
        writer.s3_client.put_object = MagicMock(
            side_effect=Exception("S3 upload failed")
        )

        # Should return False on error
        success = writer.write_player_daily_artifacts(sample_data, target_date)

        assert success is False

    def test_json_content_type_and_cache_headers(self, writer, mock_s3):
        """Test that index objects have correct content type and short cache."""
        target_date = date(2024, 1, 15)

        writer.write_latest_index(target_date)

        # Get object metadata
        response = mock_s3.head_object(
            Bucket="test-gold-bucket", Key="served/index/latest.json"
        )

        assert response["ContentType"] == "application/json"
        assert response["CacheControl"] == "public, max-age=300"

    def test_historical_data_gets_immutable_cache_headers(
        self, writer, mock_s3, sample_player_analytics
    ):
        """Test that historical data artifacts get immutable 1-year cache headers."""
        target_date = date(2024, 1, 15)

        writer.write_player_daily_artifacts(sample_player_analytics, target_date)

        # Get object metadata for a player daily artifact
        response = mock_s3.head_object(
            Bucket="test-gold-bucket",
            Key="served/player_daily/2024-01-15/player_001.json",
        )

        assert response["ContentType"] == "application/json"
        assert response["CacheControl"] == "public, max-age=31536000, immutable"

    def test_team_daily_gets_immutable_cache_headers(
        self, writer, mock_s3, sample_team_analytics
    ):
        """Test that team daily artifacts get immutable 1-year cache headers."""
        target_date = date(2024, 1, 15)

        writer.write_team_daily_artifacts(sample_team_analytics, target_date)

        response = mock_s3.head_object(
            Bucket="test-gold-bucket",
            Key="served/team_daily/2024-01-15/team_001.json",
        )

        assert response["CacheControl"] == "public, max-age=31536000, immutable"

    def test_top_lists_gets_immutable_cache_headers(
        self, writer, mock_s3, sample_player_analytics
    ):
        """Test that top lists artifacts get immutable 1-year cache headers."""
        target_date = date(2024, 1, 15)

        writer.write_top_lists(sample_player_analytics, target_date)

        response = mock_s3.head_object(
            Bucket="test-gold-bucket",
            Key="served/top_lists/2024-01-15/points.json",
        )

        assert response["CacheControl"] == "public, max-age=31536000, immutable"

    def test_get_cache_control_index_path(self, writer):
        """Test that index paths get the short TTL cache control."""
        assert (
            writer._get_cache_control("served/index/latest.json")
            == "public, max-age=300"
        )

    def test_get_cache_control_historical_paths(self, writer):
        """Test that non-index paths get the immutable cache control."""
        assert (
            writer._get_cache_control("served/player_daily/2024-01-15/123.json")
            == "public, max-age=31536000, immutable"
        )
        assert (
            writer._get_cache_control("served/team_daily/2024-01-15/456.json")
            == "public, max-age=31536000, immutable"
        )
        assert (
            writer._get_cache_control("served/top_lists/2024-01-15/points.json")
            == "public, max-age=31536000, immutable"
        )

    def test_prepare_player_daily_data_field_mapping(self, writer):
        """Test that player data preparation maps fields correctly."""
        raw_data = {
            "player_id": 2544,
            "player_name": "LeBron James",
            "team_id": "LAL",
            "points": 25,
            "rebounds": 8,
            "assists": 7,
            "steals": 2,
            "blocks": 1,
            "turnovers": 3,
            "player_efficiency_rating": 22.5,
            "true_shooting_pct": 0.58,
        }
        target_date = date(2024, 1, 15)

        prepared = writer._prepare_player_daily_data(raw_data, target_date)

        assert prepared["player_id"] == "2544"
        assert prepared["player_name"] == "LeBron James"
        assert prepared["team"] == "LAL"
        assert prepared["efficiency_rating"] == 22.5
        assert prepared["true_shooting_percentage"] == 0.58
        assert prepared["game_date"] == "2024-01-15"

    def test_prepare_team_daily_data_field_mapping(self, writer):
        """Test that team data preparation maps fields correctly."""
        raw_data = {
            "team_id": 1610612747,
            "team_name": "Los Angeles Lakers",
            "points": 110,
            "field_goals_made": 42,
            "field_goals_attempted": 85,
            "rebounds": 44,
            "assists": 25,
            "offensive_rating": 115.3,
            "is_home": True,
        }
        target_date = date(2024, 1, 15)

        prepared = writer._prepare_team_daily_data(raw_data, target_date)

        assert prepared["team_id"] == "1610612747"
        assert prepared["team_name"] == "Los Angeles Lakers"
        assert prepared["points"] == 110
        assert prepared["offensive_rating"] == 115.3
        assert prepared["home_game"] is True
        assert prepared["game_date"] == "2024-01-15"

    @pytest.fixture
    def sample_season_aggregations(self):
        """Sample player season aggregation data for testing."""
        return {
            "player_001": {
                "player_id": "player_001",
                "player_name": "Test Player One",
                "season": "2023-24",
                "team": "TEAM1",
                "total_games": 60,
                "total_minutes": 1800.0,
                "points_per_game": 22.5,
                "rebounds_per_game": 7.3,
                "assists_per_game": 5.1,
                "steals_per_game": 1.5,
                "blocks_per_game": 0.8,
                "turnovers_per_game": 2.3,
                "field_goal_percentage": 0.485,
                "three_point_percentage": 0.372,
                "free_throw_percentage": 0.885,
                "efficiency_rating": 21.4,
                "true_shooting_percentage": 0.592,
                "usage_rate": 0.28,
            },
            "player_002": {
                "player_id": "player_002",
                "player_name": "Test Player Two",
                "season": "2023-24",
                "team": "TEAM2",
                "total_games": 72,
                "total_minutes": 2520.0,
                "points_per_game": 28.1,
                "rebounds_per_game": 4.5,
                "assists_per_game": 8.2,
                "steals_per_game": 1.8,
                "blocks_per_game": 0.3,
                "turnovers_per_game": 3.1,
                "field_goal_percentage": 0.512,
                "three_point_percentage": 0.401,
                "free_throw_percentage": 0.910,
                "efficiency_rating": 26.8,
                "true_shooting_percentage": 0.648,
                "usage_rate": 0.32,
            },
        }

    def test_write_player_season_artifacts(
        self, writer, mock_s3, sample_season_aggregations
    ):
        """Test writing player season aggregation artifacts to S3."""
        success = writer.write_player_season_artifacts(
            sample_season_aggregations, "2023-24"
        )

        assert success is True

        # Verify files were written to S3
        response = mock_s3.list_objects_v2(
            Bucket="test-gold-bucket", Prefix="served/season_player/2023-24/"
        )

        assert "Contents" in response
        assert len(response["Contents"]) == 2

        # Verify file names
        keys = [obj["Key"] for obj in response["Contents"]]
        assert "served/season_player/2023-24/player_001.json" in keys
        assert "served/season_player/2023-24/player_002.json" in keys

    def test_write_player_season_artifacts_validates_json(
        self, writer, mock_s3, sample_season_aggregations
    ):
        """Test that player season artifacts contain valid JSON with expected fields."""
        writer.write_player_season_artifacts(sample_season_aggregations, "2023-24")

        # Read and validate JSON
        response = mock_s3.get_object(
            Bucket="test-gold-bucket",
            Key="served/season_player/2023-24/player_001.json",
        )
        content = response["Body"].read().decode("utf-8")
        data = json.loads(content)

        # Verify expected fields
        assert data["player_id"] == "player_001"
        assert data["player_name"] == "Test Player One"
        assert data["season"] == "2023-24"
        assert data["team"] == "TEAM1"
        assert data["total_games"] == 60
        assert data["total_minutes"] == 1800.0
        assert data["points_per_game"] == 22.5
        assert data["rebounds_per_game"] == 7.3
        assert data["assists_per_game"] == 5.1
        assert data["field_goal_percentage"] == 0.485
        assert data["efficiency_rating"] == 21.4
        assert data["true_shooting_percentage"] == 0.592

    def test_write_player_season_artifacts_empty(self, writer, mock_s3):
        """Test writing empty season aggregations returns True."""
        success = writer.write_player_season_artifacts({}, "2023-24")

        assert success is True

        # Verify no files were written
        response = mock_s3.list_objects_v2(
            Bucket="test-gold-bucket", Prefix="served/season_player/2023-24/"
        )
        assert "Contents" not in response

    def test_player_season_artifacts_immutable_cache_headers(
        self, writer, mock_s3, sample_season_aggregations
    ):
        """Test that season player artifacts get immutable 1-year cache headers."""
        writer.write_player_season_artifacts(sample_season_aggregations, "2023-24")

        response = mock_s3.head_object(
            Bucket="test-gold-bucket",
            Key="served/season_player/2023-24/player_001.json",
        )

        assert response["ContentType"] == "application/json"
        assert response["CacheControl"] == "public, max-age=31536000, immutable"

    def test_player_season_artifact_size_under_limit(
        self, writer, mock_s3, sample_season_aggregations
    ):
        """Test that season artifacts are under the 100KB size limit."""
        writer.write_player_season_artifacts(sample_season_aggregations, "2023-24")

        response = mock_s3.get_object(
            Bucket="test-gold-bucket",
            Key="served/season_player/2023-24/player_001.json",
        )
        content = response["Body"].read()
        size_kb = len(content) / 1024

        assert size_kb <= 100

    def test_player_season_artifact_s3_error_handling(self, writer):
        """Test error handling when S3 upload fails for season artifacts."""
        aggregations = {
            "player_001": {
                "player_id": "player_001",
                "player_name": "Test Player",
                "season": "2023-24",
                "team": "TST",
                "total_games": 10,
                "total_minutes": 300.0,
                "points_per_game": 15.0,
                "rebounds_per_game": 5.0,
                "assists_per_game": 3.0,
                "steals_per_game": 1.0,
                "blocks_per_game": 0.5,
                "turnovers_per_game": 2.0,
            },
        }

        # Mock S3 client to raise error
        writer.s3_client.put_object = MagicMock(
            side_effect=Exception("S3 upload failed")
        )

        success = writer.write_player_season_artifacts(aggregations, "2023-24")
        assert success is False

    def test_prepare_player_season_data_field_mapping(self, writer):
        """Test that player season data preparation maps fields correctly."""
        stats = {
            "player_id": "2544",
            "player_name": "LeBron James",
            "season": "2023-24",
            "team": "LAL",
            "total_games": 71,
            "total_minutes": 2500.0,
            "points_per_game": 25.7,
            "rebounds_per_game": 7.3,
            "assists_per_game": 8.3,
            "steals_per_game": 1.3,
            "blocks_per_game": 0.5,
            "turnovers_per_game": 3.5,
            "field_goal_percentage": 0.540,
            "three_point_percentage": 0.410,
            "free_throw_percentage": 0.750,
            "efficiency_rating": 22.1,
            "true_shooting_percentage": 0.640,
            "usage_rate": 0.300,
            "scoring_trend": 0.05,
            "efficiency_trend": -0.02,
        }

        prepared = writer._prepare_player_season_data(stats, "2544", "2023-24")

        assert prepared["player_id"] == "2544"
        assert prepared["player_name"] == "LeBron James"
        assert prepared["season"] == "2023-24"
        assert prepared["team"] == "LAL"
        assert prepared["total_games"] == 71
        assert prepared["total_minutes"] == 2500.0
        assert prepared["points_per_game"] == 25.7
        assert prepared["field_goal_percentage"] == 0.540
        assert prepared["efficiency_rating"] == 22.1
        assert prepared["true_shooting_percentage"] == 0.640
        assert prepared["scoring_trend"] == 0.05

    def test_get_cache_control_season_player_path(self, writer):
        """Test that season_player paths get the immutable cache control."""
        assert (
            writer._get_cache_control("served/season_player/2023-24/player_001.json")
            == "public, max-age=31536000, immutable"
        )
