"""
Integration tests using hoopstat-mock-data for realistic bronze layer validation.

This module demonstrates integration between the bronze layer ingestion and
the mock data generation framework, providing realistic test scenarios.
"""

import json
import time
from datetime import date, datetime
from io import BytesIO
from unittest.mock import Mock, patch

import pandas as pd
import pyarrow.parquet as pq
import pytest
from moto import mock_aws

from app.config import BronzeIngestionConfig
from app.ingestion import DateScopedIngestion
from app.s3_manager import BronzeS3Manager


class TestBronzeLayerMockDataIntegration:
    """Integration tests using mock NBA data for bronze layer validation."""
    
    def _convert_mock_games_to_nba_api_format(self, mock_games):
        """Convert mock data format to NBA API format for testing."""
        nba_format_games = []
        for game in mock_games:
            # Convert mock data format to NBA API expected format
            nba_game = {
                "GAME_ID": str(game.id),
                "GAME_DATE": game.game_date.strftime("%Y-%m-%d"),
                "HOME_TEAM": f"TEAM_{game.home_team_id}",
                "AWAY_TEAM": f"TEAM_{game.away_team_id}",
                "HOME_SCORE": game.home_score,
                "AWAY_SCORE": game.away_score,
                "SEASON": "2023-24",
                "GAME_STATUS_TEXT": "Final",
            }
            nba_format_games.append(nba_game)
        return nba_format_games

    def _create_mock_box_score(self, game_id, mock_player_stats=None):
        """Create a mock box score in NBA API format."""
        return {
            "game_id": str(game_id),
            "fetch_date": datetime.now().isoformat(),
            "resultSets": [
                {
                    "name": "GameSummary",
                    "headers": ["GAME_ID", "HOME_TEAM", "AWAY_TEAM"],
                    "rowSet": [[str(game_id), "HOME", "AWAY"]],
                },
                {
                    "name": "PlayerStats",
                    "headers": ["PLAYER_ID", "PLAYER_NAME", "PTS", "REB", "AST"],
                    "rowSet": [
                        ["2544", "Mock Player 1", 25, 8, 6],
                        ["201939", "Mock Player 2", 30, 5, 12],
                    ],
                },
            ],
        }

    @mock_aws
    def test_mock_data_integration_flow(self):
        """Test complete flow using mock data generation."""
        # Try to import mock data (may not be available in CI)
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs', 'hoopstat-mock-data'))
            from hoopstat_mock_data.generators.mock_data_generator import MockDataGenerator
            
            # Generate test data
            generator = MockDataGenerator(seed=42)
            dataset = generator.generate_small_test_dataset()
            
            # Convert to NBA API format
            nba_games = self._convert_mock_games_to_nba_api_format(dataset["games"])
            
        except ImportError:
            # Fallback to manual mock data if library not available
            class MockGame:
                def __init__(self, id, home_team_id, away_team_id, home_score, away_score, game_date):
                    self.id = id
                    self.home_team_id = home_team_id
                    self.away_team_id = away_team_id
                    self.home_score = home_score
                    self.away_score = away_score
                    self.game_date = game_date
            
            mock_games = [
                MockGame(1, 1, 2, 110, 105, date(2023, 12, 25)),
                MockGame(2, 3, 4, 98, 102, date(2023, 12, 25)),
            ]
            nba_games = self._convert_mock_games_to_nba_api_format(mock_games)

        # Set up S3 and ingestion
        import boto3
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bronze-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        config = BronzeIngestionConfig(
            bronze_bucket=bucket_name, aws_region="us-east-1"
        )

        with patch("app.ingestion.NBAClient") as mock_nba_client:
            mock_client_instance = Mock()
            mock_client_instance.get_games_for_date.return_value = nba_games
            mock_client_instance.get_box_score.side_effect = (
                lambda game_id: self._create_mock_box_score(game_id)
            )
            mock_nba_client.return_value = mock_client_instance

            ingestion = DateScopedIngestion(config)
            s3_manager = ingestion.s3_manager

            # Run ingestion
            target_date = date(2023, 12, 25)
            start_time = time.time()
            result = ingestion.run(target_date, dry_run=False)
            end_time = time.time()

            # Validate results
            assert result is True
            assert s3_manager.check_exists("schedule", target_date)
            assert s3_manager.check_exists("box_scores", target_date)

            # Performance validation
            ingestion_time = end_time - start_time
            assert ingestion_time < 5.0  # Should complete quickly

            # Validate data content
            schedule_key = f"raw/schedule/date=2023-12-25/data.parquet"
            response = s3_client.get_object(Bucket=bucket_name, Key=schedule_key)
            schedule_data = pq.read_table(BytesIO(response["Body"].read())).to_pandas()

            assert len(schedule_data) == len(nba_games)
            assert "GAME_ID" in schedule_data.columns
            assert "HOME_TEAM" in schedule_data.columns
            assert "AWAY_TEAM" in schedule_data.columns

    @mock_aws
    def test_large_dataset_performance_validation(self):
        """Test performance with larger mock dataset."""
        # Create larger mock dataset for performance testing
        class MockGame:
            def __init__(self, id, home_team_id, away_team_id, home_score, away_score, game_date):
                self.id = id
                self.home_team_id = home_team_id
                self.away_team_id = away_team_id
                self.home_score = home_score
                self.away_score = away_score
                self.game_date = game_date

        # Generate 50 games for performance testing
        mock_games = []
        for i in range(50):
            mock_games.append(MockGame(
                i + 1,
                (i % 15) + 1,  # Home team ID
                ((i + 1) % 15) + 1,  # Away team ID
                100 + (i % 30),  # Home score
                95 + (i % 25),   # Away score
                date(2023, 12, 25)
            ))

        nba_games = self._convert_mock_games_to_nba_api_format(mock_games)

        # Set up S3 and ingestion
        import boto3
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bronze-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        config = BronzeIngestionConfig(
            bronze_bucket=bucket_name, aws_region="us-east-1"
        )

        with patch("app.ingestion.NBAClient") as mock_nba_client:
            mock_client_instance = Mock()
            mock_client_instance.get_games_for_date.return_value = nba_games
            mock_client_instance.get_box_score.side_effect = (
                lambda game_id: self._create_mock_box_score(game_id)
            )
            mock_nba_client.return_value = mock_client_instance

            ingestion = DateScopedIngestion(config)

            # Performance test
            target_date = date(2023, 12, 25)
            start_time = time.time()
            result = ingestion.run(target_date, dry_run=False)
            end_time = time.time()

            # Validate performance
            assert result is True
            ingestion_time = end_time - start_time
            
            # Performance assertions for larger dataset
            total_operations = len(nba_games) * 2  # Schedule + box scores
            throughput = total_operations / ingestion_time
            
            # Should handle at least 10 operations per second
            assert throughput >= 10.0
            
            # Should complete within 15 seconds even for 100 operations
            assert ingestion_time < 15.0

    @mock_aws
    def test_realistic_data_validation(self):
        """Test with realistic data shapes and types."""
        # Create realistic NBA game data
        realistic_games = [
            {
                "GAME_ID": "0022300500",
                "GAME_DATE": "2023-12-25",
                "HOME_TEAM": "LAL",
                "AWAY_TEAM": "GSW",
                "HOME_SCORE": 123,
                "AWAY_SCORE": 109,
                "SEASON": "2023-24",
                "GAME_STATUS_TEXT": "Final",
                "HOME_TEAM_ID": 1610612747,
                "AWAY_TEAM_ID": 1610612744,
                "WL_HOME": "W",
                "WL_AWAY": "L",
            },
            {
                "GAME_ID": "0022300501",
                "GAME_DATE": "2023-12-25",
                "HOME_TEAM": "BOS",
                "AWAY_TEAM": "MIA",
                "HOME_SCORE": 114,
                "AWAY_SCORE": 106,
                "SEASON": "2023-24",
                "GAME_STATUS_TEXT": "Final",
                "HOME_TEAM_ID": 1610612738,
                "AWAY_TEAM_ID": 1610612748,
                "WL_HOME": "W",
                "WL_AWAY": "L",
            },
        ]

        realistic_box_score = {
            "game_id": "0022300500",
            "fetch_date": "2023-12-25T15:30:00Z",
            "resultSets": [
                {
                    "name": "GameSummary",
                    "headers": [
                        "GAME_DATE_EST", "GAME_ID", "GAME_STATUS_TEXT",
                        "HOME_TEAM_ID", "VISITOR_TEAM_ID", "SEASON",
                        "LIVE_PERIOD", "LIVE_PC_TIME", "NATL_TV_BROADCASTER_ABBREVIATION",
                        "HOME_TV_BROADCASTER_ABBREVIATION", "AWAY_TV_BROADCASTER_ABBREVIATION",
                        "LIVE_PERIOD_TIME_BCAST", "WH_STATUS"
                    ],
                    "rowSet": [[
                        "2023-12-25T00:00:00", "0022300500", "Final",
                        1610612747, 1610612744, "2023-24",
                        4, "", "ABC", "SPNLA", "NBCSBA", "Final", 1
                    ]],
                },
                {
                    "name": "LineScore",
                    "headers": [
                        "GAME_DATE_EST", "GAME_ID", "TEAM_ID", "TEAM_ABBREVIATION",
                        "TEAM_CITY_NAME", "TEAM_WINS_LOSSES", "PTS_QTR1", "PTS_QTR2",
                        "PTS_QTR3", "PTS_QTR4", "PTS_OT1", "PTS_OT2", "PTS_OT3",
                        "PTS_OT4", "PTS_OT5", "PTS", "FG_PCT", "FT_PCT", "FG3_PCT",
                        "AST", "REB", "TOV"
                    ],
                    "rowSet": [
                        [
                            "2023-12-25T00:00:00", "0022300500", 1610612747, "LAL",
                            "Los Angeles", "17-15", 31, 29, 32, 31, 0, 0, 0, 0, 0,
                            123, 0.489, 0.778, 0.385, 30, 50, 12
                        ],
                        [
                            "2023-12-25T00:00:00", "0022300500", 1610612744, "GSW",
                            "Golden State", "15-17", 25, 27, 28, 29, 0, 0, 0, 0, 0,
                            109, 0.451, 0.739, 0.324, 28, 45, 15
                        ]
                    ],
                },
            ],
        }

        # Set up S3 and ingestion
        import boto3
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bronze-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        config = BronzeIngestionConfig(
            bronze_bucket=bucket_name, aws_region="us-east-1"
        )

        with patch("app.ingestion.NBAClient") as mock_nba_client:
            mock_client_instance = Mock()
            mock_client_instance.get_games_for_date.return_value = realistic_games
            mock_client_instance.get_box_score.return_value = realistic_box_score
            mock_nba_client.return_value = mock_client_instance

            ingestion = DateScopedIngestion(config)
            s3_manager = ingestion.s3_manager

            # Run ingestion
            target_date = date(2023, 12, 25)
            result = ingestion.run(target_date, dry_run=False)

            # Validate results
            assert result is True

            # Validate realistic data preservation
            schedule_key = f"raw/schedule/date=2023-12-25/data.parquet"
            response = s3_client.get_object(Bucket=bucket_name, Key=schedule_key)
            schedule_data = pq.read_table(BytesIO(response["Body"].read())).to_pandas()

            # Check that all expected columns are preserved
            expected_columns = [
                "GAME_ID", "GAME_DATE", "HOME_TEAM", "AWAY_TEAM",
                "HOME_SCORE", "AWAY_SCORE", "SEASON", "GAME_STATUS_TEXT",
                "HOME_TEAM_ID", "AWAY_TEAM_ID", "WL_HOME", "WL_AWAY"
            ]
            
            for col in expected_columns:
                assert col in schedule_data.columns

            # Validate data types
            assert schedule_data["GAME_ID"].dtype == "object"  # String
            assert schedule_data["HOME_SCORE"].dtype in ["int64", "int32"]  # Integer
            assert schedule_data["AWAY_SCORE"].dtype in ["int64", "int32"]  # Integer
            assert schedule_data["HOME_TEAM_ID"].dtype in ["int64", "int32"]  # Integer

            # Validate specific values
            assert schedule_data.iloc[0]["GAME_ID"] == "0022300500"
            assert schedule_data.iloc[0]["HOME_TEAM"] == "LAL"
            assert schedule_data.iloc[0]["HOME_SCORE"] == 123

    @mock_aws
    def test_error_resilience_with_partial_failures(self):
        """Test error handling when some games succeed and others fail."""
        # Mix of good and problematic games
        mixed_games = [
            {
                "GAME_ID": "0022300500",
                "GAME_DATE": "2023-12-25",
                "HOME_TEAM": "LAL",
                "AWAY_TEAM": "GSW",
                "HOME_SCORE": 123,
                "AWAY_SCORE": 109,
            },
            {
                "GAME_ID": "0022300501",
                "GAME_DATE": "2023-12-25",
                "HOME_TEAM": "BOS",
                "AWAY_TEAM": "MIA",
                "HOME_SCORE": 114,
                "AWAY_SCORE": 106,
            },
            {
                # Problematic game - will cause box score fetch to fail
                "GAME_ID": "INVALID_GAME",
                "GAME_DATE": "2023-12-25",
                "HOME_TEAM": "UNK",
                "AWAY_TEAM": "UNK",
                "HOME_SCORE": 0,
                "AWAY_SCORE": 0,
            },
        ]

        good_box_score = {
            "game_id": "0022300500",
            "fetch_date": "2023-12-25T15:30:00Z",
            "resultSets": [{"name": "GameSummary", "rowSet": [["data"]]}],
        }

        # Set up S3 and ingestion
        import boto3
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bronze-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        config = BronzeIngestionConfig(
            bronze_bucket=bucket_name, aws_region="us-east-1"
        )

        with patch("app.ingestion.NBAClient") as mock_nba_client:
            mock_client_instance = Mock()
            mock_client_instance.get_games_for_date.return_value = mixed_games
            
            # Mock box score to return good data for valid games, None for invalid
            def mock_get_box_score(game_id):
                if game_id == "INVALID_GAME":
                    return None
                return good_box_score

            mock_client_instance.get_box_score.side_effect = mock_get_box_score
            mock_nba_client.return_value = mock_client_instance

            ingestion = DateScopedIngestion(config)
            s3_manager = ingestion.s3_manager

            # Run ingestion - should complete despite partial failures
            target_date = date(2023, 12, 25)
            result = ingestion.run(target_date, dry_run=False)

            # Should still succeed overall
            assert result is True

            # Schedule should be stored even if some box scores fail
            assert s3_manager.check_exists("schedule", target_date)

            # Validate that schedule contains all games, even problematic ones
            schedule_key = f"raw/schedule/date=2023-12-25/data.parquet"
            response = s3_client.get_object(Bucket=bucket_name, Key=schedule_key)
            schedule_data = pq.read_table(BytesIO(response["Body"].read())).to_pandas()

            assert len(schedule_data) == 3  # All games should be in schedule
            assert "0022300500" in schedule_data["GAME_ID"].values
            assert "INVALID_GAME" in schedule_data["GAME_ID"].values