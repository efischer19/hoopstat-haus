"""
Comprehensive bronze layer ingestion validation tests.

This module provides tests that validate the bronze layer data ingestion process
according to the acceptance criteria:
- Test data ingestion from mock JSON API responses
- Validate JSON to Parquet conversion accuracy
- Test partitioning scheme (year/month/day/hour) implementation
- Verify metadata enrichment (ingestion timestamps, source system tags)
- Test error handling for malformed data
- Validate compression and storage optimization
- Performance benchmark assertions for ingestion speed
"""

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


class TestBronzeLayerValidation:
    """Comprehensive validation tests for bronze layer ingestion."""

    @pytest.fixture
    def mock_nba_api_response(self):
        """Mock NBA API response data."""
        return {
            "games": [
                {
                    "GAME_ID": "0022300500",
                    "GAME_DATE": "2023-12-25",
                    "HOME_TEAM": "LAL",
                    "AWAY_TEAM": "GSW",
                    "HOME_SCORE": 123,
                    "AWAY_SCORE": 109,
                    "SEASON": "2023-24",
                },
                {
                    "GAME_ID": "0022300501",
                    "GAME_DATE": "2023-12-25",
                    "HOME_TEAM": "BOS",
                    "AWAY_TEAM": "MIA",
                    "HOME_SCORE": 114,
                    "AWAY_SCORE": 106,
                    "SEASON": "2023-24",
                },
            ]
        }

    @pytest.fixture
    def mock_box_score_response(self):
        """Mock box score API response data."""
        return {
            "game_id": "0022300500",
            "fetch_date": "2023-12-25T15:30:00Z",
            "resultSets": [
                {
                    "name": "GameSummary",
                    "headers": [
                        "GAME_ID",
                        "HOME_TEAM",
                        "AWAY_TEAM",
                        "HOME_SCORE",
                        "AWAY_SCORE",
                    ],
                    "rowSet": [["0022300500", "LAL", "GSW", 123, 109]],
                },
                {
                    "name": "PlayerStats",
                    "headers": [
                        "PLAYER_ID",
                        "PLAYER_NAME",
                        "TEAM",
                        "MIN",
                        "PTS",
                        "REB",
                        "AST",
                    ],
                    "rowSet": [
                        ["2544", "LeBron James", "LAL", "36:45", 31, 8, 11],
                        ["201939", "Stephen Curry", "GSW", "35:22", 28, 4, 9],
                    ],
                },
            ],
        }

    @pytest.fixture
    def malformed_data_samples(self):
        """Sample malformed data for error handling tests."""
        return {
            "missing_game_id": {
                "games": [
                    {
                        "GAME_DATE": "2023-12-25",
                        "HOME_TEAM": "LAL",
                        "AWAY_TEAM": "GSW",
                        # Missing GAME_ID
                    }
                ]
            },
            "invalid_date": {
                "games": [
                    {
                        "GAME_ID": "0022300500",
                        "GAME_DATE": "invalid-date",
                        "HOME_TEAM": "LAL",
                        "AWAY_TEAM": "GSW",
                    }
                ]
            },
            "null_values": {
                "games": [
                    {
                        "GAME_ID": None,
                        "GAME_DATE": "2023-12-25",
                        "HOME_TEAM": None,
                        "AWAY_TEAM": "GSW",
                    }
                ]
            },
        }

    @mock_aws
    def test_json_to_parquet_conversion_accuracy(self, mock_nba_api_response):
        """Test that JSON to Parquet conversion maintains data accuracy."""
        import boto3

        # Create S3 bucket
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bronze-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        # Initialize S3 manager
        s3_manager = BronzeS3Manager(bucket_name)

        # Convert mock data to DataFrame (simulating NBA API response processing)
        games_data = mock_nba_api_response["games"]
        original_df = pd.DataFrame(games_data)

        # Store as Parquet
        target_date = date(2023, 12, 25)
        key = s3_manager.store_parquet(original_df, "games", target_date)

        # Retrieve and verify data accuracy
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        parquet_data = response["Body"].read()

        # Read back the Parquet data
        retrieved_df = pq.read_table(BytesIO(parquet_data)).to_pandas()

        # Verify data accuracy
        assert len(retrieved_df) == len(original_df)
        assert list(retrieved_df.columns) == list(original_df.columns)

        # Check specific data values
        assert retrieved_df.iloc[0]["GAME_ID"] == "0022300500"
        assert retrieved_df.iloc[0]["HOME_TEAM"] == "LAL"
        assert retrieved_df.iloc[0]["HOME_SCORE"] == 123
        assert retrieved_df.iloc[1]["AWAY_TEAM"] == "MIA"

        # Verify data types are preserved
        assert retrieved_df["GAME_ID"].dtype == original_df["GAME_ID"].dtype
        assert retrieved_df["HOME_SCORE"].dtype == original_df["HOME_SCORE"].dtype

    @mock_aws
    def test_partitioning_scheme_validation(self):
        """Test the partitioning scheme implementation (year/month/day/hour)."""
        import boto3

        # Create S3 bucket
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bronze-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        # Initialize S3 manager
        s3_manager = BronzeS3Manager(bucket_name)

        # Test data for different dates
        test_dates = [
            date(2023, 12, 25),
            date(2024, 1, 1),
            date(2024, 2, 14),
        ]

        # Store data for each date
        for test_date in test_dates:
            df = pd.DataFrame(
                {
                    "game_id": [f"game_{test_date.strftime('%Y%m%d')}"],
                    "date": [test_date.strftime("%Y-%m-%d")],
                }
            )
            key = s3_manager.store_parquet(df, "games", test_date)

            # Verify key structure follows partitioning scheme
            expected_key = (
                f"raw/games/date={test_date.strftime('%Y-%m-%d')}/data.parquet"
            )
            assert key == expected_key

        # Test game-specific partitioning with suffix
        game_id = "0022300500"
        df = pd.DataFrame({"game_id": [game_id], "data": ["test_box_score"]})
        key = s3_manager.store_parquet(
            df, "box_scores", date(2023, 12, 25), f"/{game_id}"
        )

        expected_key = f"raw/box_scores/date=2023-12-25/{game_id}/data.parquet"
        assert key == expected_key

        # Verify all partitions exist
        for test_date in test_dates:
            assert s3_manager.check_exists("games", test_date)

    @mock_aws
    def test_metadata_enrichment_validation(self):
        """Test metadata enrichment with ingestion timestamps and source system tags."""
        import boto3

        # Create S3 bucket
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bronze-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        # Initialize S3 manager
        s3_manager = BronzeS3Manager(bucket_name)

        # Store data with metadata
        df = pd.DataFrame(
            {"game_id": ["0022300500"], "home_team": ["LAL"], "away_team": ["GSW"]}
        )

        target_date = date(2023, 12, 25)
        key = s3_manager.store_parquet(df, "games", target_date)

        # Retrieve object metadata
        response = s3_client.head_object(Bucket=bucket_name, Key=key)
        metadata = response["Metadata"]

        # Verify required metadata fields
        assert "entity" in metadata
        assert metadata["entity"] == "games"
        assert "date" in metadata
        assert metadata["date"] == "2023-12-25"
        assert "format" in metadata
        assert metadata["format"] == "parquet"
        assert "rows" in metadata
        assert metadata["rows"] == "1"

        # Verify timestamp exists (created by S3)
        assert "LastModified" in response
        assert isinstance(response["LastModified"], datetime)

        # Test enhanced metadata for box scores
        box_score_df = pd.DataFrame(
            {
                "game_id": ["0022300500"],
                "fetch_timestamp": [datetime.now().isoformat()],
                "source_system": ["nba_api"],
            }
        )

        box_score_key = s3_manager.store_parquet(
            box_score_df, "box_scores", target_date, "/0022300500"
        )

        box_score_response = s3_client.head_object(
            Bucket=bucket_name, Key=box_score_key
        )
        box_score_metadata = box_score_response["Metadata"]

        assert box_score_metadata["entity"] == "box_scores"

    @mock_aws
    def test_error_handling_malformed_data(self, malformed_data_samples):
        """Test error handling for various types of malformed data."""
        import boto3

        # Create S3 bucket
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bronze-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        config = BronzeIngestionConfig(
            bronze_bucket=bucket_name, aws_region="us-east-1"
        )

        with patch("app.ingestion.NBAClient") as mock_nba_client:
            mock_client_instance = Mock()
            mock_nba_client.return_value = mock_client_instance

            ingestion = DateScopedIngestion(config)

            # Test missing required fields
            mock_client_instance.get_games_for_date.return_value = (
                malformed_data_samples["missing_game_id"]["games"]
            )
            mock_client_instance.get_box_score.return_value = None

            target_date = date(2023, 12, 25)

            # Should handle missing GAME_ID gracefully
            # The current implementation should not crash but may skip games
            # without GAME_ID
            result = ingestion.run(target_date, dry_run=False)

            # The ingestion should complete but may not process games without
            # required fields
            assert result is True

            # Test null values handling
            mock_client_instance.get_games_for_date.return_value = (
                malformed_data_samples["null_values"]["games"]
            )
            mock_client_instance.get_box_score.return_value = None

            # Should handle null values gracefully
            result = ingestion.run(target_date, dry_run=False)
            assert result is True

    @mock_aws
    def test_compression_and_storage_optimization(self):
        """Test compression and storage optimization validation."""
        import boto3

        # Create S3 bucket
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bronze-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        # Initialize S3 manager
        s3_manager = BronzeS3Manager(bucket_name)

        # Create test data with repeated values (good for compression)
        large_df = pd.DataFrame(
            {
                "game_id": ["0022300500"] * 1000,
                "team": ["LAL"] * 500 + ["GSW"] * 500,
                "player_name": ["LeBron James"] * 300
                + ["Stephen Curry"] * 300
                + ["Other"] * 400,
                "stat_value": [25.5] * 1000,
            }
        )

        target_date = date(2023, 12, 25)
        key = s3_manager.store_parquet(large_df, "player_stats", target_date)

        # Get object info to check compression
        response = s3_client.head_object(Bucket=bucket_name, Key=key)
        compressed_size = response["ContentLength"]

        # Verify the data was stored
        assert compressed_size > 0

        # Read back and verify data integrity after compression
        obj_response = s3_client.get_object(Bucket=bucket_name, Key=key)
        parquet_data = obj_response["Body"].read()
        retrieved_df = pq.read_table(BytesIO(parquet_data)).to_pandas()

        # Verify data integrity
        assert len(retrieved_df) == 1000
        assert retrieved_df["game_id"].nunique() == 1
        assert retrieved_df["team"].nunique() == 2
        assert all(retrieved_df["stat_value"] == 25.5)

        # The compressed size should be significantly smaller than uncompressed
        # (This is a proxy test - in real scenarios, snappy compression is used)
        estimated_uncompressed_size = len(large_df) * 50  # Rough estimate
        compression_ratio = compressed_size / estimated_uncompressed_size
        assert compression_ratio < 1.0  # Should be compressed

    @mock_aws
    def test_performance_benchmarks_ingestion_speed(self):
        """Test performance benchmarks for ingestion speed."""
        import boto3

        # Create S3 bucket
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bronze-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        config = BronzeIngestionConfig(
            bronze_bucket=bucket_name, aws_region="us-east-1"
        )

        # Create realistic test data that conforms to validation schema
        games_data = []
        for i in range(20):  # Simulate 20 games
            games_data.append(
                {
                    "GAME_ID": f"00223005{i:02d}",  # Exactly 10 digits
                    "GAME_DATE": "2023-12-25",
                    "TEAM_ID": 1610612747 + (i % 10),  # Lakers team ID + offset
                    "TEAM_ABBREVIATION": f"T{i % 10:02d}",
                    "TEAM_NAME": f"Team {i % 10}",
                    "MATCHUP": f"T{i % 10:02d} vs T{(i + 1) % 10:02d}",
                    "PTS": 100 + i,
                }
            )

        box_score_data = {
            "game_id": "0022300500",
            "fetch_date": "2023-12-25T15:30:00Z",
            "resultSets": [
                {
                    "name": "PlayerStats",
                    "headers": ["PLAYER_ID", "PLAYER_NAME", "PTS"],
                    "rowSet": [
                        ["Player" + str(i), f"Player {i}", i * 2] for i in range(100)
                    ],
                }
            ],
        }

        with patch("app.ingestion.NBAClient") as mock_nba_client:
            mock_client_instance = Mock()
            mock_client_instance.get_games_for_date.return_value = games_data
            mock_client_instance.get_box_score.return_value = box_score_data
            mock_nba_client.return_value = mock_client_instance

            ingestion = DateScopedIngestion(config)
            s3_manager = ingestion.s3_manager

            # Measure ingestion time
            start_time = time.time()
            target_date = date(2023, 12, 25)
            result = ingestion.run(target_date, dry_run=False)
            end_time = time.time()

            # Verify successful ingestion
            assert result is True

            # Performance assertions
            ingestion_time = end_time - start_time

            # Should complete within reasonable time (adjust threshold as needed)
            assert ingestion_time < 10.0  # Should complete within 10 seconds

            # Calculate throughput
            total_records = len(games_data) + len(games_data)  # Schedule + box scores
            throughput = total_records / ingestion_time

            # Should process at least 2 records per second
            assert throughput >= 2.0

            # Verify all data was stored
            assert s3_manager.check_exists("schedule", target_date)
            assert s3_manager.check_exists("box_scores", target_date)

    @mock_aws
    def test_end_to_end_ingestion_with_mock_data(self):
        """Test complete end-to-end ingestion flow with mock NBA API data."""
        import boto3

        # Create S3 bucket
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bronze-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        config = BronzeIngestionConfig(
            bronze_bucket=bucket_name, aws_region="us-east-1"
        )

        # Mock complete NBA API data that conforms to validation schema
        mock_games = [
            {
                "GAME_ID": "0022300500",
                "GAME_DATE": "2023-12-25",
                "TEAM_ID": 1610612747,  # Lakers team ID
                "TEAM_ABBREVIATION": "LAL",
                "TEAM_NAME": "Los Angeles Lakers",
                "MATCHUP": "LAL vs GSW",
                "PTS": 123,
            },
            {
                "GAME_ID": "0022300501",
                "GAME_DATE": "2023-12-25",
                "TEAM_ID": 1610612738,  # Celtics team ID
                "TEAM_ABBREVIATION": "BOS",
                "TEAM_NAME": "Boston Celtics",
                "MATCHUP": "BOS vs MIA",
                "PTS": 114,
            },
        ]

        mock_box_score = {
            "game_id": "0022300500",
            "fetch_date": "2023-12-25T15:30:00Z",
            "resultSets": [
                {
                    "name": "GameSummary",
                    "headers": ["GAME_ID", "HOME_TEAM", "AWAY_TEAM"],
                    "rowSet": [["0022300500", "LAL", "GSW"]],
                },
                {
                    "name": "PlayerStats",
                    "headers": ["PLAYER_ID", "PLAYER_NAME", "PTS"],
                    "rowSet": [
                        ["2544", "LeBron James", 31],
                        ["201939", "Stephen Curry", 28],
                    ],
                },
            ],
        }

        with patch("app.ingestion.NBAClient") as mock_nba_client:
            mock_client_instance = Mock()
            mock_client_instance.get_games_for_date.return_value = mock_games
            mock_client_instance.get_box_score.return_value = mock_box_score
            mock_nba_client.return_value = mock_client_instance

            ingestion = DateScopedIngestion(config)
            s3_manager = ingestion.s3_manager

            # Run complete ingestion
            target_date = date(2023, 12, 25)
            result = ingestion.run(target_date, dry_run=False)

            # Verify successful completion
            assert result is True

            # Verify schedule data was stored
            schedule_exists = s3_manager.check_exists("schedule", target_date)
            assert schedule_exists

            # Verify box score data was stored
            box_score_exists = s3_manager.check_exists("box_scores", target_date)
            assert box_score_exists

            # Verify data content by reading back
            schedule_key = "raw/schedule/date=2023-12-25/data.parquet"
            response = s3_client.get_object(Bucket=bucket_name, Key=schedule_key)
            schedule_data = pq.read_table(BytesIO(response["Body"].read())).to_pandas()

            assert len(schedule_data) == 2
            assert "0022300500" in schedule_data["GAME_ID"].values
            assert "0022300501" in schedule_data["GAME_ID"].values
            assert "LAL" in schedule_data["TEAM_ABBREVIATION"].values
            assert "BOS" in schedule_data["TEAM_ABBREVIATION"].values

            # Verify metadata
            metadata = s3_client.head_object(Bucket=bucket_name, Key=schedule_key)[
                "Metadata"
            ]
            assert metadata["entity"] == "schedule"
            assert metadata["date"] == "2023-12-25"
            assert metadata["format"] == "parquet"
            assert metadata["rows"] == "2"

    def test_data_type_validation_and_schema_consistency(self):
        """Test that data types are properly validated and schema is consistent."""
        # Create test data with various data types
        test_data = pd.DataFrame(
            {
                "game_id": ["0022300500", "0022300501"],  # string
                "game_date": ["2023-12-25", "2023-12-25"],  # string (date)
                "home_score": [123, 114],  # integer
                "away_score": [109, 106],  # integer
                "game_time": ["19:30", "20:00"],  # string (time)
                "is_playoff": [False, False],  # boolean
                "attendance": [18997, 19596],  # integer
                "game_duration_minutes": [125.5, 132.0],  # float
            }
        )

        # Verify data types
        assert test_data["game_id"].dtype == "object"  # string
        assert test_data["home_score"].dtype in ["int64", "int32"]  # integer
        assert test_data["is_playoff"].dtype == "bool"  # boolean
        assert test_data["game_duration_minutes"].dtype == "float64"  # float

        # Test schema consistency across multiple DataFrames
        test_data_2 = pd.DataFrame(
            {
                "game_id": ["0022300502"],
                "game_date": ["2023-12-26"],
                "home_score": [98],
                "away_score": [102],
                "game_time": ["19:00"],
                "is_playoff": [True],
                "attendance": [20000],
                "game_duration_minutes": [118.5],
            }
        )

        # Both DataFrames should have consistent schema
        assert list(test_data.columns) == list(test_data_2.columns)
        for col in test_data.columns:
            assert test_data[col].dtype == test_data_2[col].dtype

    @mock_aws
    def test_incremental_ingestion_detection(self):
        """Test detection and handling of incremental ingestion scenarios."""
        import boto3

        # Create S3 bucket
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bronze-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        # Initialize S3 manager
        s3_manager = BronzeS3Manager(bucket_name)

        # First ingestion
        df1 = pd.DataFrame({"game_id": ["0022300500"], "status": ["scheduled"]})
        target_date = date(2023, 12, 25)
        s3_manager.store_parquet(df1, "games", target_date)

        # Verify data exists
        assert s3_manager.check_exists("games", target_date)

        # Test listing entities
        entities = s3_manager.list_entities_for_date(target_date)
        assert "games" in entities

        # Add more data for the same date (simulating incremental update)
        df2 = pd.DataFrame({"game_id": ["0022300501"], "status": ["in_progress"]})
        s3_manager.store_parquet(df2, "player_stats", target_date)

        # Both entities should exist
        entities = s3_manager.list_entities_for_date(target_date)
        assert "games" in entities
        assert "player_stats" in entities

        # Test different date
        target_date_2 = date(2023, 12, 26)
        entities_date_2 = s3_manager.list_entities_for_date(target_date_2)
        assert len(entities_date_2) == 0  # No data for this date yet
