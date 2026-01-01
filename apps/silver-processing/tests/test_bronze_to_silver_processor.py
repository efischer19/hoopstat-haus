"""Tests for the BronzeToSilverProcessor class."""

import json
from datetime import date
from unittest.mock import Mock, patch

from app.processors import BronzeToSilverProcessor


class TestBronzeToSilverProcessor:
    """Test cases for the BronzeToSilverProcessor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = BronzeToSilverProcessor(
            bronze_bucket="test-bronze-bucket", region_name="us-east-1"
        )

    @patch("boto3.client")
    def test_processor_initialization(self, mock_boto_client):
        """Test that processor can be initialized."""
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client

        processor = BronzeToSilverProcessor("test-bucket")

        assert processor is not None
        assert processor.bronze_bucket == "test-bucket"
        assert processor.region_name == "us-east-1"
        mock_boto_client.assert_called_once_with("s3", region_name="us-east-1")

    @patch("boto3.client")
    def test_read_bronze_json_success(self, mock_boto_client):
        """Test successful reading of Bronze JSON data (ADR-031: multiple files)."""
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client

        # Mock S3 list_objects_v2 response with multiple game files
        test_data_1 = {
            "game_id": "0022400123",
            "home_team": {"id": 1, "name": "Lakers"},
        }
        test_data_2 = {
            "game_id": "0022400124",
            "home_team": {"id": 2, "name": "Celtics"},
        }

        mock_list_response = {
            "Contents": [
                {"Key": "raw/box/2024-01-01/0022400123.json"},
                {"Key": "raw/box/2024-01-01/0022400124.json"},
            ]
        }
        mock_s3_client.list_objects_v2.return_value = mock_list_response

        # Mock get_object responses for each file
        mock_response_1 = {"Body": Mock()}
        mock_response_1["Body"].read.return_value = json.dumps(test_data_1).encode(
            "utf-8"
        )
        mock_response_2 = {"Body": Mock()}
        mock_response_2["Body"].read.return_value = json.dumps(test_data_2).encode(
            "utf-8"
        )

        mock_s3_client.get_object.side_effect = [mock_response_1, mock_response_2]

        processor = BronzeToSilverProcessor("test-bucket")
        result = processor.read_bronze_json("box", date(2024, 1, 1))

        # Should return list of games
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == test_data_1
        assert result[1] == test_data_2

        # Verify list_objects_v2 was called with correct prefix
        mock_s3_client.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket", Prefix="raw/box/2024-01-01/"
        )

    @patch("boto3.client")
    def test_read_bronze_json_not_found(self, mock_boto_client):
        """Test reading Bronze JSON when no files exist."""
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client

        # Mock empty list_objects_v2 response (no Contents key)
        mock_s3_client.list_objects_v2.return_value = {}

        processor = BronzeToSilverProcessor("test-bucket")
        result = processor.read_bronze_json("box", date(2024, 1, 1))

        # Should return empty list
        assert result == []

    @patch("boto3.client")
    def test_read_bronze_json_single_file(self, mock_boto_client):
        """Test reading Bronze JSON with single file."""
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client

        # Mock S3 list_objects_v2 response with single game file
        test_data = {"game_id": "0022400123", "home_team": {"id": 1, "name": "Lakers"}}

        mock_list_response = {
            "Contents": [
                {"Key": "raw/box/2024-01-01/0022400123.json"},
            ]
        }
        mock_s3_client.list_objects_v2.return_value = mock_list_response

        # Mock get_object response
        mock_response = {"Body": Mock()}
        mock_response["Body"].read.return_value = json.dumps(test_data).encode("utf-8")
        mock_s3_client.get_object.return_value = mock_response

        processor = BronzeToSilverProcessor("test-bucket")
        result = processor.read_bronze_json("box", date(2024, 1, 1))

        # Should return list with single game
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == test_data

    def test_convert_minutes_to_decimal(self):
        """Test minutes conversion utility."""
        processor = self.processor

        # Test MM:SS format
        assert processor._convert_minutes_to_decimal("32:42") == 32.7
        assert processor._convert_minutes_to_decimal("0:30") == 0.5

        # Test numeric formats
        assert processor._convert_minutes_to_decimal("32.5") == 32.5
        assert processor._convert_minutes_to_decimal(25) == 25.0
        assert processor._convert_minutes_to_decimal(30.5) == 30.5

        # Test edge cases
        assert processor._convert_minutes_to_decimal(None) is None
        assert processor._convert_minutes_to_decimal("") is None
        assert processor._convert_minutes_to_decimal("invalid") is None

    def test_transform_to_silver_with_mock_data(self):
        """Test transformation of Bronze data to Silver models."""
        # Create realistic Bronze data
        bronze_data = {
            "game_id": 123,
            "game_date": "2024-01-01",
            "arena": "Staples Center",
            "home_team": {"id": 1, "name": "Los Angeles Lakers", "city": "Los Angeles"},
            "away_team": {"id": 2, "name": "Boston Celtics", "city": "Boston"},
            "home_team_stats": {
                "points": 108,
                "field_goals_made": 40,
                "field_goals_attempted": 85,
                "three_pointers_made": 12,
                "three_pointers_attempted": 30,
                "free_throws_made": 16,
                "free_throws_attempted": 20,
                "offensive_rebounds": 8,
                "defensive_rebounds": 32,
                "assists": 25,
                "steals": 7,
                "blocks": 5,
                "turnovers": 12,
                "fouls": 18,
            },
            "away_team_stats": {
                "points": 102,
                "field_goals_made": 38,
                "field_goals_attempted": 82,
                "three_pointers_made": 10,
                "three_pointers_attempted": 28,
                "free_throws_made": 16,
                "free_throws_attempted": 18,
                "offensive_rebounds": 6,
                "defensive_rebounds": 30,
                "assists": 22,
                "steals": 5,
                "blocks": 3,
                "turnovers": 15,
                "fouls": 20,
            },
            "home_players": [
                {
                    "player_id": 1001,
                    "player_name": "LeBron James",
                    "team": "Los Angeles Lakers",
                    "position": "SF",
                    "points": 28,
                    "offensive_rebounds": 2,
                    "defensive_rebounds": 6,
                    "assists": 8,
                    "steals": 2,
                    "blocks": 1,
                    "turnovers": 3,
                    "field_goals_made": 11,
                    "field_goals_attempted": 18,
                    "three_pointers_made": 3,
                    "three_pointers_attempted": 6,
                    "free_throws_made": 3,
                    "free_throws_attempted": 4,
                    "minutes_played": "36:24",
                }
            ],
            "away_players": [
                {
                    "player_id": 2001,
                    "player_name": "Jayson Tatum",
                    "team": "Boston Celtics",
                    "position": "SF",
                    "points": 25,
                    "offensive_rebounds": 1,
                    "defensive_rebounds": 7,
                    "assists": 5,
                    "steals": 1,
                    "blocks": 0,
                    "turnovers": 2,
                    "field_goals_made": 9,
                    "field_goals_attempted": 20,
                    "three_pointers_made": 4,
                    "three_pointers_attempted": 10,
                    "free_throws_made": 3,
                    "free_throws_attempted": 3,
                    "minutes_played": "38:12",
                }
            ],
        }

        # Transform to Silver
        result = self.processor.transform_to_silver(bronze_data, "box")

        # Verify structure
        assert "player_stats" in result
        assert "team_stats" in result
        assert "game_stats" in result

        # Verify player stats
        assert len(result["player_stats"]) == 2
        lebron_stats = result["player_stats"][0]
        assert lebron_stats["player_name"] == "LeBron James"
        assert lebron_stats["points"] == 28
        assert lebron_stats["rebounds"] == 8  # 2 + 6
        assert lebron_stats["assists"] == 8
        assert lebron_stats["minutes_played"] == 36.4  # 36:24 converted

        # Verify team stats
        assert len(result["team_stats"]) == 2
        home_team = result["team_stats"][0]
        assert (
            home_team["team_name"] == "Los Angeles Lakers"
        )  # normalized by rules engine
        assert home_team["points"] == 108
        assert home_team["rebounds"] == 40  # 8 + 32

        # Verify game stats
        assert len(result["game_stats"]) == 1
        game = result["game_stats"][0]
        assert game["game_id"] == "123"
        assert game["home_score"] == 108
        assert game["away_score"] == 102
        assert game["venue"] == "Staples Center"

    def test_apply_quality_checks(self):
        """Test quality checking functionality."""
        silver_data = {
            "player_stats": [
                {
                    "player_id": "1001",
                    "points": 28,
                    "rebounds": 8,
                    "assists": 8,
                    "steals": 2,
                    "blocks": 1,
                    "turnovers": 3,
                },
                {
                    "player_id": "1002",
                    "points": 15,
                    "rebounds": 5,
                    "assists": 3,
                    "steals": 1,
                    "blocks": 0,
                    "turnovers": 2,
                },
            ],
            "team_stats": [
                {
                    "team_id": "1",
                    "points": 108,
                    "rebounds": 40,
                    "assists": 25,
                    "steals": 7,
                    "blocks": 5,
                    "turnovers": 12,
                }
            ],
        }

        result = self.processor.apply_quality_checks(silver_data)

        # Verify structure
        assert "player_stats_quality" in result
        assert "team_stats_quality" in result
        assert "outliers" in result
        assert "overall_quality" in result
        assert "average_completeness" in result

        # Should have quality metrics for each player and team
        assert len(result["player_stats_quality"]) == 2
        assert len(result["team_stats_quality"]) == 1

        # Check completeness ratios
        for quality in result["player_stats_quality"].values():
            assert "completeness_ratio" in quality
            assert quality["completeness_ratio"] >= 0.0
            assert quality["completeness_ratio"] <= 1.0

    def test_validate_silver_data_with_processor(self):
        """Test validation integration with SilverProcessor."""
        from app.processors import SilverProcessor

        # Valid silver data
        valid_data = {
            "player_stats": [
                {
                    "player_id": "test_player",
                    "points": 25,
                    "rebounds": 10,
                    "assists": 5,
                    "steals": 2,
                    "blocks": 1,
                    "turnovers": 3,
                    "lineage": {
                        "source_system": "test",
                        "schema_version": "1.0.0",
                        "transformation_stage": "silver",
                        "validation_mode": "strict",
                    },
                }
            ],
            "team_stats": [
                {
                    "team_id": "test_team",
                    "team_name": "Test Team",
                    "points": 108,
                    "field_goals_made": 40,
                    "field_goals_attempted": 85,
                    "rebounds": 45,
                    "assists": 25,
                    "lineage": {
                        "source_system": "test",
                        "schema_version": "1.0.0",
                        "transformation_stage": "silver",
                        "validation_mode": "strict",
                    },
                }
            ],
            "game_stats": [
                {
                    "game_id": "test_game",
                    "home_team_id": "team1",
                    "away_team_id": "team2",
                    "home_score": 108,
                    "away_score": 102,
                    "lineage": {
                        "source_system": "test",
                        "schema_version": "1.0.0",
                        "transformation_stage": "silver",
                        "validation_mode": "strict",
                    },
                }
            ],
        }

        processor = SilverProcessor()
        result = processor.validate_silver_data(valid_data)
        assert result is True

        # Invalid data (negative points)
        invalid_data = {
            "player_stats": [
                {
                    "player_id": "test_player",
                    "points": -5,  # Invalid negative points
                    "rebounds": 10,
                    "assists": 5,
                    "steals": 2,
                    "blocks": 1,
                    "turnovers": 3,
                }
            ],
            "team_stats": [],
            "game_stats": [],
        }

        result = processor.validate_silver_data(invalid_data)
        assert result is False
