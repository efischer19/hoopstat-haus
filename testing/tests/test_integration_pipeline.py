"""
Integration tests for the complete pipeline using Localstack.

This test suite demonstrates the bronze → silver → gold data flow
in an isolated Docker environment with Localstack S3 simulation.
"""

import os
import sys
import pytest
import logging

# Add the libraries to the path
sys.path.insert(0, "/app/libs/hoopstat-e2e-testing")
sys.path.insert(0, "/app/libs/hoopstat-mock-data")
sys.path.insert(0, "/app/libs/hoopstat-data")

from hoopstat_e2e_testing import S3TestUtils, PipelineTestRunner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def s3_utils():
    """Create S3 utilities instance for testing."""
    endpoint_url = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
    return S3TestUtils(endpoint_url=endpoint_url)


@pytest.fixture(scope="session")
def pipeline_runner(s3_utils):
    """Create pipeline runner for integration testing."""
    return PipelineTestRunner(s3_utils, project_name="integration-test")


class TestFullPipelineIntegration:
    """Integration tests for the complete data pipeline."""

    def test_environment_connectivity(self, s3_utils):
        """Test that we can connect to Localstack S3."""
        # Create a test bucket to verify connectivity
        test_bucket = "connectivity-test"

        assert s3_utils.create_bucket(test_bucket), "Failed to create test bucket"
        assert s3_utils.bucket_exists(test_bucket), "Test bucket does not exist"

        # Clean up
        s3_utils.delete_bucket(test_bucket)
        logger.info("✅ Successfully connected to Localstack S3")

    def test_s3_operations(self, s3_utils):
        """Test basic S3 operations work correctly."""
        bucket_name = "s3-operations-test"

        # Create bucket
        assert s3_utils.create_bucket(bucket_name)

        # Test string object
        s3_utils.put_object(bucket_name, "test/string.txt", "Hello, World!")
        retrieved = s3_utils.get_object(bucket_name, "test/string.txt", "string")
        assert retrieved == "Hello, World!"

        # Test JSON object
        test_json = {"message": "Hello from JSON", "count": 42}
        s3_utils.put_object(bucket_name, "test/data.json", test_json)
        retrieved_json = s3_utils.get_object(bucket_name, "test/data.json", "json")
        assert retrieved_json == test_json

        # Clean up
        s3_utils.delete_bucket(bucket_name, delete_objects=True)
        logger.info("✅ S3 operations working correctly")

    def test_medallion_architecture_setup(self, pipeline_runner):
        """Test that medallion architecture buckets can be set up."""
        # Setup environment
        assert pipeline_runner.setup_environment(), (
            "Failed to setup pipeline environment"
        )

        # Verify all three layers exist
        assert len(pipeline_runner.buckets) == 3
        for layer in ["bronze", "silver", "gold"]:
            assert layer in pipeline_runner.buckets
            bucket_name = pipeline_runner.buckets[layer]
            assert pipeline_runner.s3_utils.bucket_exists(bucket_name), (
                f"{layer} bucket does not exist"
            )

        logger.info("✅ Medallion architecture buckets set up successfully")

        # Clean up
        pipeline_runner.cleanup_environment()

    def test_bronze_layer_ingestion(self, pipeline_runner):
        """Test bronze layer data ingestion with mock NBA data."""
        # Setup environment
        pipeline_runner.setup_environment()

        # Ingest mock data
        num_teams = 4
        num_players_per_team = 5
        assert pipeline_runner.ingest_bronze_data(num_teams, num_players_per_team), (
            "Bronze ingestion failed"
        )

        # Verify data was ingested
        bronze_bucket = pipeline_runner.buckets["bronze"]

        # Check teams data
        teams_data = pipeline_runner.s3_utils.get_object(
            bronze_bucket, "raw/teams/teams.json", "json"
        )
        assert teams_data is not None, "Teams data not found"
        assert len(teams_data["teams"]) == num_teams, f"Expected {num_teams} teams"
        assert "ingestion_metadata" in teams_data, "Missing ingestion metadata"

        # Check players data
        players_data = pipeline_runner.s3_utils.get_object(
            bronze_bucket, "raw/players/players.json", "json"
        )
        assert players_data is not None, "Players data not found"
        assert len(players_data["players"]) == num_teams * num_players_per_team, (
            "Incorrect number of players"
        )

        # Check games data
        games_data = pipeline_runner.s3_utils.get_object(
            bronze_bucket, "raw/games/games.json", "json"
        )
        assert games_data is not None, "Games data not found"
        assert len(games_data["games"]) > 0, "No games data found"

        logger.info(
            f"✅ Bronze layer ingestion successful: {len(teams_data['teams'])} teams, "
            f"{len(players_data['players'])} players, {len(games_data['games'])} games"
        )

        # Clean up
        pipeline_runner.cleanup_environment()

    def test_silver_layer_transformation(self, pipeline_runner):
        """Test silver layer data transformation and cleaning."""
        # Setup and populate bronze layer
        pipeline_runner.setup_environment()
        pipeline_runner.ingest_bronze_data(3, 4)  # 3 teams, 4 players each

        # Transform to silver layer
        assert pipeline_runner.transform_silver_data(), "Silver transformation failed"

        # Verify transformed data
        silver_bucket = pipeline_runner.buckets["silver"]

        # Check teams data
        teams_df = pipeline_runner.s3_utils.get_object(
            silver_bucket, "cleaned/teams/teams.parquet", "dataframe"
        )
        assert teams_df is not None, "Teams DataFrame not found"
        assert len(teams_df) == 3, "Incorrect number of teams in silver layer"
        assert "full_name" in teams_df.columns, "Missing full_name column in teams"
        assert "created_at" in teams_df.columns, "Missing created_at timestamp"

        # Check players data
        players_df = pipeline_runner.s3_utils.get_object(
            silver_bucket, "cleaned/players/players.parquet", "dataframe"
        )
        assert players_df is not None, "Players DataFrame not found"
        assert len(players_df) == 12, (
            "Incorrect number of players in silver layer"
        )  # 3 * 4
        assert "full_name" in players_df.columns, "Missing full_name column in players"
        assert "bmi" in players_df.columns, "Missing BMI calculation"

        # Check games data
        games_df = pipeline_runner.s3_utils.get_object(
            silver_bucket, "cleaned/games/games.parquet", "dataframe"
        )
        assert games_df is not None, "Games DataFrame not found"
        assert "total_score" in games_df.columns, "Missing total_score calculation"
        assert "game_date" in games_df.columns, "Missing formatted game_date"

        logger.info(
            f"✅ Silver layer transformation successful: {len(teams_df)} teams, "
            f"{len(players_df)} players, {len(games_df)} games cleaned and normalized"
        )

        # Clean up
        pipeline_runner.cleanup_environment()

    def test_gold_layer_aggregation(self, pipeline_runner):
        """Test gold layer business metrics aggregation."""
        # Setup, populate bronze, and transform silver
        pipeline_runner.setup_environment()
        pipeline_runner.ingest_bronze_data(2, 3)  # 2 teams, 3 players each
        pipeline_runner.transform_silver_data()

        # Aggregate to gold layer
        assert pipeline_runner.aggregate_gold_data(), "Gold aggregation failed"

        # Verify aggregated data
        gold_bucket = pipeline_runner.buckets["gold"]

        # Check team statistics
        team_stats_df = pipeline_runner.s3_utils.get_object(
            gold_bucket, "metrics/team_stats.parquet", "dataframe"
        )
        assert team_stats_df is not None, "Team stats DataFrame not found"
        assert len(team_stats_df) == 2, "Incorrect number of teams in gold layer"

        required_team_cols = [
            "team_name",
            "games_played",
            "wins",
            "losses",
            "win_percentage",
            "avg_points_per_game",
        ]
        for col in required_team_cols:
            assert col in team_stats_df.columns, f"Missing {col} in team stats"

        # Check player statistics
        player_stats_df = pipeline_runner.s3_utils.get_object(
            gold_bucket, "metrics/player_stats.parquet", "dataframe"
        )
        assert player_stats_df is not None, "Player stats DataFrame not found"
        assert len(player_stats_df) == 6, (
            "Incorrect number of players in gold layer"
        )  # 2 * 3

        required_player_cols = [
            "player_name",
            "team_id",
            "position",
            "height_cm",
            "weight_kg",
            "bmi",
        ]
        for col in required_player_cols:
            assert col in player_stats_df.columns, f"Missing {col} in player stats"

        # Check league summary
        league_summary = pipeline_runner.s3_utils.get_object(
            gold_bucket, "metrics/league_summary.json", "json"
        )
        assert league_summary is not None, "League summary not found"
        assert league_summary["total_teams"] == 2, "Incorrect total teams in summary"
        assert league_summary["total_players"] == 6, (
            "Incorrect total players in summary"
        )
        assert "avg_points_per_game" in league_summary, (
            "Missing average points per game"
        )

        logger.info(
            f"✅ Gold layer aggregation successful: {len(team_stats_df)} team stats, "
            f"{len(player_stats_df)} player stats, league summary created"
        )

        # Clean up
        pipeline_runner.cleanup_environment()

    def test_complete_pipeline_flow(self, pipeline_runner):
        """Test the complete bronze → silver → gold pipeline flow."""
        logger.info("🚀 Starting complete pipeline integration test...")

        # Run the full pipeline
        num_teams = 3
        num_players_per_team = 4
        assert pipeline_runner.run_full_pipeline(num_teams, num_players_per_team), (
            "Full pipeline execution failed"
        )

        # Verify the complete pipeline output
        verification_results = pipeline_runner.verify_pipeline_output()

        # Check that all layers are valid
        for layer in ["bronze_layer", "silver_layer", "gold_layer"]:
            assert verification_results[layer]["status"] == "valid", (
                f"{layer} validation failed"
            )
            logger.info(f"✅ {layer} validation passed")

        # Log detailed verification results
        logger.info("Pipeline verification details:")
        for layer, results in verification_results.items():
            logger.info(f"  {layer}: {results['status']}")
            for obj, exists in results["details"].items():
                status = "✅" if exists else "❌"
                logger.info(f"    {status} {obj}")

        logger.info("🎉 Complete pipeline integration test passed!")

        # Clean up
        pipeline_runner.cleanup_environment()

    def test_pipeline_data_quality(self, pipeline_runner):
        """Test data quality and consistency across pipeline layers."""
        # Run the pipeline
        pipeline_runner.setup_environment()
        assert pipeline_runner.run_full_pipeline(2, 5)  # 2 teams, 5 players each

        # Get data from each layer for quality checks
        bronze_bucket = pipeline_runner.buckets["bronze"]
        silver_bucket = pipeline_runner.buckets["silver"]
        gold_bucket = pipeline_runner.buckets["gold"]

        # Bronze layer data
        bronze_teams = pipeline_runner.s3_utils.get_object(
            bronze_bucket, "raw/teams/teams.json", "json"
        )
        bronze_players = pipeline_runner.s3_utils.get_object(
            bronze_bucket, "raw/players/players.json", "json"
        )

        # Silver layer data
        silver_teams_df = pipeline_runner.s3_utils.get_object(
            silver_bucket, "cleaned/teams/teams.parquet", "dataframe"
        )
        silver_players_df = pipeline_runner.s3_utils.get_object(
            silver_bucket, "cleaned/players/players.parquet", "dataframe"
        )

        # Gold layer data
        gold_team_stats_df = pipeline_runner.s3_utils.get_object(
            gold_bucket, "metrics/team_stats.parquet", "dataframe"
        )
        gold_player_stats_df = pipeline_runner.s3_utils.get_object(
            gold_bucket, "metrics/player_stats.parquet", "dataframe"
        )

        # Data consistency checks
        assert len(bronze_teams["teams"]) == len(silver_teams_df), (
            "Team count mismatch between bronze and silver"
        )
        assert len(bronze_players["players"]) == len(silver_players_df), (
            "Player count mismatch between bronze and silver"
        )
        assert len(silver_teams_df) == len(gold_team_stats_df), (
            "Team count mismatch between silver and gold"
        )
        assert len(silver_players_df) == len(gold_player_stats_df), (
            "Player count mismatch between silver and gold"
        )

        # Data quality checks
        # Check that all teams have valid statistics
        assert gold_team_stats_df["games_played"].min() >= 0, (
            "Invalid games played count"
        )
        assert gold_team_stats_df["win_percentage"].min() >= 0, "Invalid win percentage"
        assert gold_team_stats_df["win_percentage"].max() <= 1, "Invalid win percentage"

        # Check that all players have valid BMI calculations
        assert gold_player_stats_df["bmi"].min() > 0, "Invalid BMI values"
        assert gold_player_stats_df["height_cm"].min() > 0, "Invalid height values"
        assert gold_player_stats_df["weight_kg"].min() > 0, "Invalid weight values"

        logger.info("✅ Data quality and consistency checks passed")

        # Clean up
        pipeline_runner.cleanup_environment()

    @pytest.mark.performance
    def test_pipeline_performance(self, pipeline_runner):
        """Test pipeline performance with larger dataset."""
        import time

        logger.info("🔄 Starting pipeline performance test...")

        # Test with larger dataset
        num_teams = 10
        num_players_per_team = 15

        start_time = time.time()
        assert pipeline_runner.run_full_pipeline(num_teams, num_players_per_team)
        end_time = time.time()

        execution_time = end_time - start_time
        logger.info(f"⏱️  Pipeline execution time: {execution_time:.2f} seconds")

        # Performance assertions (adjust thresholds as needed)
        assert execution_time < 60, f"Pipeline took too long: {execution_time:.2f}s"

        # Verify data volumes
        verification = pipeline_runner.verify_pipeline_output()
        assert verification["bronze_layer"]["status"] == "valid"
        assert verification["silver_layer"]["status"] == "valid"
        assert verification["gold_layer"]["status"] == "valid"

        logger.info(
            f"✅ Performance test passed with {num_teams} teams and {num_teams * num_players_per_team} players"
        )

        # Clean up
        pipeline_runner.cleanup_environment()
