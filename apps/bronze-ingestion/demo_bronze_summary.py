#!/usr/bin/env python3
"""
Example script demonstrating bronze layer summary functionality.

This script shows how the bronze summary JSON file provides at-a-glance
insights into the bronze layer data.
"""

import json
from datetime import date
from unittest.mock import MagicMock, patch

from app.bronze_summary import BronzeSummaryManager
from app.s3_manager import BronzeS3Manager


def demo_bronze_summary():
    """Demonstrate bronze summary generation with example data."""
    print("=== Bronze Layer Summary Demo ===\n")

    # Create mock S3 manager for demo
    mock_s3_manager = MagicMock(spec=BronzeS3Manager)
    mock_s3_manager.bucket_name = "hoopstat-haus-bronze"

    # Create summary manager
    summary_manager = BronzeSummaryManager(mock_s3_manager)

    # Mock the bronze statistics to simulate real data
    mock_bronze_stats = {
        "entities": {
            "schedule": {
                "last_updated": "2024-01-15T14:30:22Z",
                "file_count": 1,
                "estimated_size_mb": 0.5,
                "last_processed_date": "2024-01-15",
            },
            "box_scores": {
                "last_updated": "2024-01-15T14:30:22Z",
                "file_count": 12,
                "estimated_size_mb": 24.7,
                "last_processed_date": "2024-01-15",
            },
            "players": {
                "last_updated": "2024-01-14T18:45:10Z",
                "file_count": 1,
                "estimated_size_mb": 2.1,
                "last_processed_date": "2024-01-14",
            },
        },
        "storage_info": {"total_files": 14, "estimated_size_mb": 27.3},
    }

    # Simulate ingestion of January 15, 2024 with 12 games and 12 successful box scores
    target_date = date(2024, 1, 15)
    games_count = 12
    successful_box_scores = 12

    with patch.object(
        summary_manager, "_collect_bronze_statistics", return_value=mock_bronze_stats
    ):
        # Generate the summary
        summary = summary_manager.generate_summary(
            target_date, games_count, successful_box_scores
        )

    # Display the summary in a readable format
    print("Generated Bronze Layer Summary:")
    print(json.dumps(summary, indent=2, default=str))

    print("\n=== Key Insights from Summary ===")

    bronze_stats = summary["bronze_layer_stats"]

    print(f"📅 Last Ingestion Date: {bronze_stats['last_ingestion_date']}")
    print(f"⏰ Last Successful Run: {bronze_stats['last_successful_run']}")
    print(f"📊 Total Entities: {bronze_stats['total_entities']}")
    print(f"📁 Total Files: {bronze_stats['storage_info']['total_files']}")
    print(f"💾 Estimated Size: {bronze_stats['storage_info']['estimated_size_mb']} MB")

    print("\n=== Data Quality Metrics ===")
    data_quality = bronze_stats["data_quality"]
    print(f"🎯 Last Run Success Rate: {data_quality['last_run_success_rate'] * 100}%")
    print(f"🏀 Games Processed: {data_quality['last_run_games_count']}")
    print(f"📈 Box Scores Successful: {data_quality['last_run_successful_box_scores']}")

    print("\n=== Entity Breakdown ===")
    for entity_name, entity_stats in bronze_stats["entities"].items():
        print(f"  • {entity_name.replace('_', ' ').title()}:")
        print(f"    - Files: {entity_stats['file_count']}")
        print(f"    - Size: {entity_stats['estimated_size_mb']} MB")
        print(f"    - Last Updated: {entity_stats['last_updated']}")
        if entity_stats.get("last_processed_date"):
            print(f"    - Last Processed: {entity_stats['last_processed_date']}")

    print("\n=== Summary File Location ===")
    print(f"📍 S3 Location: s3://{mock_s3_manager.bucket_name}/_metadata/summary.json")

    print("\nThis summary provides all the requested insights:")
    print("✅ How much data is in the bronze layer (files, sizes, records)")
    print("✅ Which date was last fetched (last_ingestion_date)")
    print("✅ When data was last refreshed (last_successful_run)")
    print("✅ Data quality metrics and success rates")
    print("✅ Per-entity breakdown for detailed analysis")


if __name__ == "__main__":
    demo_bronze_summary()
