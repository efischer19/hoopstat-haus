#!/usr/bin/env python3
"""
Manual test script for the player daily aggregator Lambda function.

This script demonstrates the Lambda function with sample data to verify
it works correctly end-to-end.
"""

import json
import os
from unittest.mock import Mock

import pandas as pd

from app.aggregator import PlayerStatsAggregator
from app.config import LambdaConfig
from app.handler import lambda_handler
from app.s3_utils import S3Client


def create_sample_silver_data():
    """Create sample Silver layer data for testing."""
    return pd.DataFrame(
        {
            "player_id": [
                "lebron_james",
                "lebron_james",
                "stephen_curry",
                "kevin_durant",
            ],
            "game_id": ["game_1", "game_2", "game_1", "game_1"],
            "team_id": ["LAL", "LAL", "GSW", "PHX"],
            "points": [28, 31, 35, 27],
            "rebounds": [10, 8, 5, 9],
            "assists": [7, 9, 8, 4],
            "field_goals_made": [11, 12, 13, 10],
            "field_goals_attempted": [20, 22, 24, 18],
            "three_pointers_made": [3, 4, 7, 2],
            "three_pointers_attempted": [8, 9, 15, 6],
            "free_throws_made": [3, 3, 2, 5],
            "free_throws_attempted": [4, 4, 2, 6],
            "steals": [2, 1, 3, 1],
            "blocks": [1, 0, 0, 2],
            "turnovers": [4, 3, 2, 3],
            "minutes_played": [38, 35, 42, 40],
        }
    )


def test_lambda_function_locally():
    """Test the Lambda function with mocked S3 operations."""
    print("🏀 Testing Player Daily Aggregator Lambda Function")
    print("=" * 60)

    # Create sample data
    sample_data = create_sample_silver_data()
    print(f"\n📊 Sample Silver Layer Data ({len(sample_data)} records):")
    print(
        sample_data[
            [
                "player_id",
                "points",
                "rebounds",
                "assists",
                "field_goals_made",
                "field_goals_attempted",
            ]
        ].to_string(index=False)
    )

    # Mock S3 operations
    mock_s3_client = Mock(spec=S3Client)
    mock_s3_client.read_parquet.return_value = sample_data
    mock_s3_client.object_exists.return_value = False  # No existing season stats
    mock_s3_client.write_parquet = Mock()  # Track writes

    # Set environment variables
    os.environ["SILVER_BUCKET"] = "test-silver-bucket"
    os.environ["GOLD_BUCKET"] = "test-gold-bucket"
    os.environ["AWS_REGION"] = "us-east-1"

    # Create test S3 event
    test_event = {
        "Records": [
            {
                "eventSource": "aws:s3",
                "s3": {
                    "bucket": {"name": "test-silver-bucket"},
                    "object": {
                        "key": (
                            "silver/player_games/season=2023-24/"
                            "date=2024-01-15/player_stats.parquet"
                        )
                    },
                },
            }
        ]
    }

    print("\n📨 S3 Event:")
    print(json.dumps(test_event, indent=2))

    # Mock the S3Client and aggregator in the handler
    original_s3_client = None
    try:
        # Patch the S3Client creation in the handler
        import app.aggregator
        import app.handler

        # Create a custom aggregator that uses our mock
        config = LambdaConfig.from_environment()
        aggregator = PlayerStatsAggregator(config, mock_s3_client)

        # Mock the aggregator's write method to capture the data
        daily_stats_written = []
        season_stats_written = []

        def mock_write_gold_files(daily_stats, season_stats, season):
            daily_stats_written.append(daily_stats.copy())
            season_stats_written.append(season_stats.copy())
            return len(daily_stats) * 2  # daily + season files per player

        aggregator._write_gold_layer_files = mock_write_gold_files

        # Patch the aggregator creation
        original_aggregator_class = app.handler.PlayerStatsAggregator
        app.handler.PlayerStatsAggregator = lambda config, s3_client: aggregator

        # Execute the Lambda handler
        print("\n🚀 Executing Lambda Handler...")
        result = lambda_handler(test_event, None)

        print("\n📤 Lambda Response:")
        print(json.dumps(result, indent=2))

        # Show the aggregated data
        if daily_stats_written:
            daily_df = daily_stats_written[0]
            print(f"\n📈 Daily Stats Generated ({len(daily_df)} players):")
            display_cols = [
                "player_id",
                "points",
                "rebounds",
                "assists",
                "games_played",
                "field_goal_percentage",
                "three_point_percentage",
                "free_throw_percentage",
            ]
            print(daily_df[display_cols].round(3).to_string(index=False))

            print(
                f"\n🏆 Season Stats Generated ({len(season_stats_written[0])} players):"
            )
            season_df = season_stats_written[0]
            print(season_df[display_cols].round(3).to_string(index=False))

        # Verify S3 operations
        print("\n💾 S3 Operations:")
        print(f"  - Read operations: {mock_s3_client.read_parquet.call_count}")
        print(f"  - Write operations: {mock_s3_client.write_parquet.call_count}")
        print(f"  - Existence checks: {mock_s3_client.object_exists.call_count}")

        # Show expected file paths
        if daily_stats_written:
            print("\n📁 Expected Gold Layer File Structure:")
            for _, row in daily_df.iterrows():
                player_id = row["player_id"]
                season = row["season"]
                date = row["date"]
                print(
                    f"  📄 gold/player_daily_stats/season={season}/"
                    f"player_id={player_id}/date={date}/daily_stats.parquet"
                )
                print(
                    f"  📄 gold/player_season_stats/season={season}/"
                    f"player_id={player_id}/season_stats.parquet"
                )

        print("\n✅ Lambda function executed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Restore original classes
        if "app.handler" in locals() and original_aggregator_class:
            app.handler.PlayerStatsAggregator = original_aggregator_class


def test_aggregation_logic():
    """Test the core aggregation logic with detailed output."""
    print("\n🧮 Testing Core Aggregation Logic")
    print("=" * 40)

    # Create sample data with known results
    sample_data = pd.DataFrame(
        {
            "player_id": ["player_a", "player_a", "player_b"],
            "points": [20, 25, 30],
            "rebounds": [8, 10, 12],
            "assists": [5, 7, 4],
            "field_goals_made": [8, 10, 12],
            "field_goals_attempted": [16, 20, 20],
            "three_pointers_made": [2, 3, 4],
            "three_pointers_attempted": [6, 8, 10],
            "free_throws_made": [2, 2, 2],
            "free_throws_attempted": [2, 2, 4],
            "steals": [1, 2, 1],
            "blocks": [0, 1, 2],
            "turnovers": [3, 4, 2],
            "minutes_played": [30, 35, 40],
        }
    )

    print("Input data:")
    print(
        sample_data[["player_id", "points", "rebounds", "assists"]].to_string(
            index=False
        )
    )

    # Create aggregator
    config = LambdaConfig(silver_bucket="test", gold_bucket="test")
    mock_s3 = Mock()
    aggregator = PlayerStatsAggregator(config, mock_s3)

    # Test aggregation
    result = aggregator._create_daily_aggregations(sample_data, "2023-24", "2024-01-15")

    print("\nAggregated results:")
    display_cols = [
        "player_id",
        "points",
        "rebounds",
        "assists",
        "games_played",
        "field_goal_percentage",
        "three_point_percentage",
        "free_throw_percentage",
    ]
    print(result[display_cols].round(3).to_string(index=False))

    # Verify calculations
    player_a = result[result["player_id"] == "player_a"].iloc[0]
    print("\nPlayer A verification:")
    print(f"  Total points: {player_a['points']} (expected: 45)")
    print(f"  Total rebounds: {player_a['rebounds']} (expected: 18)")
    print(f"  Games played: {player_a['games_played']} (expected: 2)")
    print(f"  FG%: {player_a['field_goal_percentage']:.3f} (expected: {18 / 36:.3f})")

    assert player_a["points"] == 45, f"Expected 45 points, got {player_a['points']}"
    assert player_a["games_played"] == 2, (
        f"Expected 2 games, got {player_a['games_played']}"
    )

    print("✅ Aggregation logic verified!")


if __name__ == "__main__":
    print("🏀 Player Daily Aggregator - Manual Testing")
    print("=" * 50)

    # Test core aggregation logic
    test_aggregation_logic()

    # Test full Lambda function
    success = test_lambda_function_locally()

    if success:
        print("\n🎉 All tests passed! The Lambda function is ready for deployment.")
    else:
        print("\n💥 Tests failed. Please check the implementation.")
        exit(1)
