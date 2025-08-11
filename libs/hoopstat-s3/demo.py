#!/usr/bin/env python3
"""
Demo script showing usage of the hoopstat-s3 library.

This script demonstrates how to use the S3 uploader and Parquet converter
for NBA data storage and processing.
"""

import os

from hoopstat_s3 import ParquetConverter, S3Uploader


def main():
    """Demonstrate S3 and Parquet functionality."""
    print("📦 S3 & Parquet Demo")
    print("=" * 40)

    # Initialize Parquet converter
    print("1. Creating Parquet converter...")
    converter = ParquetConverter(compression="snappy")
    print("   ✅ Converter created successfully")

    # Demo data conversion
    print("\n2. Converting sample NBA data to Parquet...")
    sample_data = {
        "games": [
            {
                "game_id": "001",
                "home_team": "Lakers",
                "away_team": "Warriors",
                "score_home": 108,
                "score_away": 112,
            },
            {
                "game_id": "002",
                "home_team": "Bulls",
                "away_team": "Heat",
                "score_home": 95,
                "score_away": 103,
            },
        ]
    }

    try:
        parquet_bytes = converter.convert_games(sample_data["games"])
        print(f"   ✅ Converted to Parquet ({len(parquet_bytes)} bytes)")
    except Exception as e:
        print(f"   ❌ Conversion failed: {e}")
        return

    # S3 uploader demo (without actual AWS credentials)
    print("\n3. S3 Uploader configuration demo...")
    try:
        # This will work without credentials for demo purposes
        S3Uploader(bucket_name="my-nba-data-bucket", region_name="us-east-1")
        print("   ✅ Uploader configured (credentials needed for actual upload)")
    except Exception as e:
        print(f"   ⚠️  Uploader configuration: {e}")

    # Show partitioning strategy
    print("\n4. S3 Partitioning Strategy:")
    print(
        "   📁 s3://bucket/nba-api/{data_type}/year={year}/month={month}/day={day}/hour={hour}/"
    )
    print("   Examples:")
    print(
        "   📄 s3://bucket/nba-api/games/year=2024/month=01/day=15/hour=14/games_001_20240115_141530.parquet"
    )
    print(
        "   📄 s3://bucket/nba-api/players/year=2024/month=01/day=15/hour=14/players_001_20240115_141530.parquet"
    )

    # Show Parquet features
    print("\n5. Parquet Features:")
    print("   🗜️  Compression: Snappy (default), Gzip, Brotli, LZ4")
    print("   📊 Columnar storage for analytics")
    print("   🔍 Schema evolution support")
    print("   📈 Optimal for data science workflows")

    print("\n📝 Example usage:")
    print("   # Convert JSON data to Parquet")
    print("   parquet_data = converter.convert_games(games_json)")
    print()
    print("   # Upload to S3 with date partitioning")
    print("   uploader.upload_games(parquet_data, date(2024, 1, 15))")
    print()
    print("   # Upload player data")
    print("   uploader.upload_players(player_parquet, date(2024, 1, 15))")

    # Environment check
    print("\n6. Environment Setup:")
    aws_configured = any(
        [
            os.getenv("AWS_ACCESS_KEY_ID"),
            os.getenv("AWS_PROFILE"),
            os.path.exists(os.path.expanduser("~/.aws/credentials")),
        ]
    )

    if aws_configured:
        print("   ✅ AWS credentials configured")
    else:
        print("   ⚠️  AWS credentials not found")
        print("   💡 Configure AWS CLI or set environment variables:")
        print("      export AWS_ACCESS_KEY_ID=your_key")
        print("      export AWS_SECRET_ACCESS_KEY=your_secret")

    print("\n🚀 Ready to process NBA data efficiently!")


if __name__ == "__main__":
    main()
