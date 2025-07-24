"""
Tests for pipeline runner.
"""

import pytest
from moto import mock_aws

from hoopstat_e2e_testing.pipeline_runner import PipelineTestRunner
from hoopstat_e2e_testing.s3_utils import S3TestUtils


class TestPipelineTestRunner:
    """Test cases for PipelineTestRunner class."""

    @pytest.fixture
    def s3_utils(self):
        """Create S3TestUtils instance for testing with moto."""
        with mock_aws():
            yield S3TestUtils(endpoint_url=None)  # moto doesn't need endpoint_url

    @pytest.fixture
    def pipeline_runner(self, s3_utils):
        """Create PipelineTestRunner instance for testing."""
        return PipelineTestRunner(s3_utils, "test-pipeline")

    def test_setup_environment(self, pipeline_runner):
        """Test pipeline environment setup."""
        # Setup environment
        assert pipeline_runner.setup_environment()

        # Verify buckets exist
        assert len(pipeline_runner.buckets) == 3
        for layer in ["bronze", "silver", "gold"]:
            assert layer in pipeline_runner.buckets
            assert pipeline_runner.s3_utils.bucket_exists(
                pipeline_runner.buckets[layer]
            )

        # Clean up
        pipeline_runner.cleanup_environment()

    def test_cleanup_environment(self, pipeline_runner):
        """Test pipeline environment cleanup."""
        # Setup first
        pipeline_runner.setup_environment()

        # Verify buckets exist
        for bucket_name in pipeline_runner.buckets.values():
            assert pipeline_runner.s3_utils.bucket_exists(bucket_name)

        # Cleanup
        assert pipeline_runner.cleanup_environment()

        # Verify buckets are gone
        for bucket_name in pipeline_runner.buckets.values():
            assert not pipeline_runner.s3_utils.bucket_exists(bucket_name)

    def test_ingest_bronze_data(self, pipeline_runner):
        """Test bronze layer data ingestion."""
        # Setup environment
        pipeline_runner.setup_environment()

        # Ingest data
        assert pipeline_runner.ingest_bronze_data(num_teams=2, num_players_per_team=3)

        # Verify data exists
        bronze_bucket = pipeline_runner.buckets["bronze"]
        expected_objects = [
            "raw/teams/teams.json",
            "raw/players/players.json",
            "raw/games/games.json",
        ]

        for obj_key in expected_objects:
            data = pipeline_runner.s3_utils.get_object(bronze_bucket, obj_key, "json")
            assert data is not None
            assert "ingestion_metadata" in data
            assert data["ingestion_metadata"]["layer"] == "bronze"

        # Verify data content
        teams_data = pipeline_runner.s3_utils.get_object(
            bronze_bucket, "raw/teams/teams.json", "json"
        )
        assert len(teams_data["teams"]) == 2

        players_data = pipeline_runner.s3_utils.get_object(
            bronze_bucket, "raw/players/players.json", "json"
        )
        assert len(players_data["players"]) == 6  # 2 teams * 3 players each

        # Clean up
        pipeline_runner.cleanup_environment()

    def test_transform_silver_data(self, pipeline_runner):
        """Test silver layer data transformation."""
        # Setup and ingest bronze data
        pipeline_runner.setup_environment()
        pipeline_runner.ingest_bronze_data(num_teams=2, num_players_per_team=3)

        # Transform to silver
        assert pipeline_runner.transform_silver_data()

        # Verify silver data exists
        silver_bucket = pipeline_runner.buckets["silver"]
        expected_objects = [
            "cleaned/teams/teams.parquet",
            "cleaned/players/players.parquet",
            "cleaned/games/games.parquet",
        ]

        for obj_key in expected_objects:
            df = pipeline_runner.s3_utils.get_object(
                silver_bucket, obj_key, "dataframe"
            )
            assert df is not None
            assert len(df) > 0
            assert "created_at" in df.columns

        # Verify transformations
        teams_df = pipeline_runner.s3_utils.get_object(
            silver_bucket, "cleaned/teams/teams.parquet", "dataframe"
        )
        assert "full_name" in teams_df.columns

        players_df = pipeline_runner.s3_utils.get_object(
            silver_bucket, "cleaned/players/players.parquet", "dataframe"
        )
        assert "full_name" in players_df.columns
        assert "bmi" in players_df.columns

        # Clean up
        pipeline_runner.cleanup_environment()

    def test_aggregate_gold_data(self, pipeline_runner):
        """Test gold layer data aggregation."""
        # Setup, ingest bronze, and transform silver
        pipeline_runner.setup_environment()
        pipeline_runner.ingest_bronze_data(num_teams=2, num_players_per_team=3)
        pipeline_runner.transform_silver_data()

        # Aggregate to gold
        assert pipeline_runner.aggregate_gold_data()

        # Verify gold data exists
        gold_bucket = pipeline_runner.buckets["gold"]

        # Check team stats
        team_stats_df = pipeline_runner.s3_utils.get_object(
            gold_bucket, "metrics/team_stats.parquet", "dataframe"
        )
        assert team_stats_df is not None
        assert len(team_stats_df) == 2  # 2 teams
        assert all(
            col in team_stats_df.columns
            for col in ["team_name", "wins", "losses", "win_percentage"]
        )

        # Check player stats
        player_stats_df = pipeline_runner.s3_utils.get_object(
            gold_bucket, "metrics/player_stats.parquet", "dataframe"
        )
        assert player_stats_df is not None
        assert len(player_stats_df) == 6  # 6 players

        # Check league summary
        league_summary = pipeline_runner.s3_utils.get_object(
            gold_bucket, "metrics/league_summary.json", "json"
        )
        assert league_summary is not None
        assert "total_teams" in league_summary
        assert league_summary["total_teams"] == 2

        # Clean up
        pipeline_runner.cleanup_environment()

    def test_run_full_pipeline(self, pipeline_runner):
        """Test complete pipeline execution."""
        # Run full pipeline
        assert pipeline_runner.run_full_pipeline(num_teams=2, num_players_per_team=3)

        # Verify all layers have data
        verification = pipeline_runner.verify_pipeline_output()

        assert verification["bronze_layer"]["status"] == "valid"
        assert verification["silver_layer"]["status"] == "valid"
        assert verification["gold_layer"]["status"] == "valid"

        # Clean up
        pipeline_runner.cleanup_environment()

    def test_verify_pipeline_output(self, pipeline_runner):
        """Test pipeline output verification."""
        # Run pipeline
        pipeline_runner.run_full_pipeline(num_teams=2, num_players_per_team=2)

        # Verify output
        results = pipeline_runner.verify_pipeline_output()

        # Check structure
        assert "bronze_layer" in results
        assert "silver_layer" in results
        assert "gold_layer" in results

        # Check bronze layer
        assert results["bronze_layer"]["status"] == "valid"
        bronze_details = results["bronze_layer"]["details"]
        assert bronze_details["raw/teams/teams.json"] is True
        assert bronze_details["raw/players/players.json"] is True
        assert bronze_details["raw/games/games.json"] is True

        # Check silver layer
        assert results["silver_layer"]["status"] == "valid"
        silver_details = results["silver_layer"]["details"]
        assert silver_details["cleaned/teams/teams.parquet"] is True
        assert silver_details["cleaned/players/players.parquet"] is True
        assert silver_details["cleaned/games/games.parquet"] is True

        # Check gold layer
        assert results["gold_layer"]["status"] == "valid"
        gold_details = results["gold_layer"]["details"]
        assert gold_details["metrics/team_stats.parquet"] is True
        assert gold_details["metrics/player_stats.parquet"] is True
        assert gold_details["metrics/league_summary.json"] is True

        # Clean up
        pipeline_runner.cleanup_environment()
