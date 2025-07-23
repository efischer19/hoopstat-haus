#!/usr/bin/env python3
"""
Demo script showing NBA ingestion library usage.

This script demonstrates how to use the NBA ingestion library components
without making actual API calls or uploading to S3.
"""

from datetime import date

from hoopstat_nba_ingestion import NBAClient, ParquetConverter, RateLimiter


def demo_basic_usage():
    """Demonstrate basic library usage."""
    print("🏀 NBA Data Ingestion Library Demo")
    print("=" * 40)

    # 1. Rate Limiter Demo
    print("\n1. Rate Limiter Configuration")
    rate_limiter = RateLimiter(min_delay=2.0, max_delay=30.0)
    print(f"   Min delay: {rate_limiter.min_delay}s")
    print(f"   Max delay: {rate_limiter.max_delay}s")
    print(f"   Current delay: {rate_limiter.current_delay}s")

    # 2. NBA Client Setup
    print("\n2. NBA Client Setup")
    client = NBAClient(rate_limiter=rate_limiter)
    print("   ✅ NBA client initialized with custom rate limiting")

    # 3. Parquet Converter Demo
    print("\n3. Parquet Converter Demo")
    converter = ParquetConverter(compression="snappy")
    print(f"   Compression: {converter.compression}")

    # Demo with sample data
    sample_games_data = [
        {
            "GAME_ID": "0022300001",
            "HOME_TEAM": "Lakers",
            "AWAY_TEAM": "Warriors",
            "GAME_DATE": "2024-01-15",
            "fetch_date": "2024-01-16T10:00:00",
        },
        {
            "GAME_ID": "0022300002",
            "HOME_TEAM": "Bulls",
            "AWAY_TEAM": "Heat",
            "GAME_DATE": "2024-01-15",
            "fetch_date": "2024-01-16T10:00:00",
        },
    ]

    # Convert to Parquet
    parquet_data = converter.convert_games(sample_games_data)
    print(f"   ✅ Converted {len(sample_games_data)} games to Parquet")
    print(f"   📦 Parquet size: {len(parquet_data)} bytes")

    # 4. S3 Uploader Demo (without actual upload)
    print("\n4. S3 Upload Configuration")
    print("   🔧 S3Uploader would be initialized like:")
    print("   uploader = S3Uploader(bucket_name='your-bronze-bucket')")
    print("   📍 Upload path would be:")
    target_date = date(2024, 1, 15)
    expected_path = f"nba-api/games/year={target_date.year}/month={target_date.month:02d}/day={target_date.day:02d}/hour=XX/"
    print(f"   {expected_path}")

    print("\n✅ Demo completed successfully!")
    print("\n💡 Next steps:")
    print("   - Configure AWS credentials for S3 uploads")
    print("   - Set up proper NBA API rate limiting")
    print("   - Integrate into bronze ingestion applications")


if __name__ == "__main__":
    demo_basic_usage()