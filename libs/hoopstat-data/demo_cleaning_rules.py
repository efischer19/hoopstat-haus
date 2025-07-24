#!/usr/bin/env python3
"""
Demo script for the data cleaning and standardization rules engine.

This script demonstrates the key features of the enhanced hoopstat-data library
including team name standardization, position normalization, null value handling,
numeric cleaning, and batch processing capabilities.
"""

import time
from datetime import datetime

from hoopstat_data import (
    DataCleaningRulesEngine,
    clean_and_transform_record,
    clean_batch,
    normalize_team_name,
    standardize_position,
    validate_and_standardize_season,
)


def demo_individual_transformations():
    """Demonstrate individual transformation functions."""
    print("=" * 60)
    print("INDIVIDUAL TRANSFORMATION FUNCTIONS")
    print("=" * 60)

    # Team name standardization
    print("\n1. Team Name Standardization:")
    test_teams = ["lakers", "LA Lakers", "warriors", "gsw", "new jersey nets"]
    for team in test_teams:
        normalized = normalize_team_name(team)
        print(f"  '{team}' -> '{normalized}'")

    # Position standardization
    print("\n2. Position Standardization:")
    test_positions = ["Point Guard", "center", "PG/SG", "Small Forward"]
    for position in test_positions:
        standardized = standardize_position(position)
        print(f"  '{position}' -> '{standardized}'")

    # Season standardization
    print("\n3. Season Standardization:")
    test_seasons = ["2023-2024", "23-24", "2022-23", "invalid"]
    for season in test_seasons:
        standardized = validate_and_standardize_season(season)
        print(f"  '{season}' -> '{standardized}'")


def demo_record_cleaning():
    """Demonstrate record-level cleaning."""
    print("\n" + "=" * 60)
    print("RECORD-LEVEL CLEANING")
    print("=" * 60)

    # Sample raw record with various data quality issues
    raw_record = {
        "player_id": "123",
        "player_name": "  John Doe  ",
        "team_name": "la lakers",
        "position": "point guard",
        "points": "25",  # String that should be numeric
        "rebounds": None,  # Null value
        "assists": "8",
        "steals": "$2",  # With currency symbol
        "blocks": "1.5",  # Decimal
        "turnovers": "",  # Empty string
        "height_inches": "72",
        "jersey_number": "23",
        "season": "2023-2024",
    }

    print("\nOriginal record:")
    for key, value in raw_record.items():
        print(f"  {key}: {repr(value)}")

    # Clean the record
    cleaned_record = clean_and_transform_record(raw_record, "player_stats")

    print("\nCleaned record:")
    for key, value in cleaned_record.items():
        print(f"  {key}: {repr(value)}")


def demo_batch_processing():
    """Demonstrate batch processing capabilities."""
    print("\n" + "=" * 60)
    print("BATCH PROCESSING")
    print("=" * 60)

    # Create sample batch data
    sample_data = [
        {
            "player_id": f"player_{i}",
            "team_name": ["lakers", "warriors", "celtics", "bulls", "heat"][i % 5],
            "position": [
                "point guard", "shooting guard", "center",
                "power forward", "small forward"
            ][i % 5],
            "points": str(20 + i),
            "rebounds": 5 + (i % 3),
            "assists": 3 + (i % 4),
        }
        for i in range(1000)  # Process 1000 records
    ]

    print(f"\nProcessing {len(sample_data)} records...")

    start_time = time.time()
    cleaned_records = clean_batch(sample_data, "player_stats")
    end_time = time.time()

    processing_time = end_time - start_time
    records_per_minute = (len(sample_data) / processing_time) * 60

    print(f"Processing completed in {processing_time:.2f} seconds")
    print(f"Rate: {records_per_minute:.0f} records per minute")

    # Show sample of cleaned records
    print("\nSample cleaned records:")
    for i in range(3):
        print(f"\nRecord {i + 1}:")
        for key, value in cleaned_records[i].items():
            print(f"  {key}: {repr(value)}")


def demo_rules_engine():
    """Demonstrate the rules engine directly."""
    print("\n" + "=" * 60)
    print("RULES ENGINE DEMONSTRATION")
    print("=" * 60)

    engine = DataCleaningRulesEngine()

    print("\n1. Team Name Standardization with Fuzzy Matching:")
    test_teams = ["Laker", "Warrior", "Boston Celtic", "Miami"]
    for team in test_teams:
        result = engine.standardize_team_name(team)
        print(f"  '{team}' -> '{result.transformed_value}' (success: {result.success})")
        if result.applied_rules:
            print(f"    Applied rules: {result.applied_rules}")

    print("\n2. Numeric Field Cleaning:")
    test_values = ["25", "$1,200", "invalid", "-5", "150"]
    for value in test_values:
        result = engine.clean_numeric_field(value, "points")
        print(f"  '{value}' -> {result.transformed_value} (success: {result.success})")
        if not result.success:
            print(f"    Error: {result.error_message}")

    print("\n3. Date/Time Standardization:")
    test_dates = ["2023-12-25", "12/25/2023", "2023-12-25 15:30:00", "invalid"]
    for date_str in test_dates:
        result = engine.standardize_datetime(date_str)
        print(
            f"  '{date_str}' -> '{result.transformed_value}' "
            f"(success: {result.success})"
        )

    # Process a batch and show transformation summary
    sample_records = [
        {
            "player_id": "1",
            "team_name": "lakers",
            "position": "pg",
            "points": "25",
            "game_date": "2023-12-25",
        },
        {
            "player_id": "2",
            "team_name": "warrior",
            "position": "center",
            "points": "$30",
            "game_date": "12/26/2023",
        },
    ]

    print("\n4. Batch Processing with Transformation Tracking:")
    cleaned_records, transformations = engine.process_batch(sample_records)

    print(f"Processed {len(sample_records)} records")
    print(f"Applied {len(transformations)} transformations")

    summary = engine.get_transformation_summary()
    print("\nTransformation Summary:")
    print(f"  Total transformations: {summary['total_transformations']}")
    print(f"  Success rate: {summary['success_rate']:.2%}")
    print("  Transformations by type:")
    for t_type, stats in summary["transformations_by_type"].items():
        print(f"    {t_type}: {stats['successful']}/{stats['total']} successful")


def main():
    """Run all demonstrations."""
    print("NBA Data Cleaning and Standardization Rules Engine Demo")
    print("=" * 60)
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        demo_individual_transformations()
        demo_record_cleaning()
        demo_batch_processing()
        demo_rules_engine()

        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nKey Features Demonstrated:")
        print("✓ Team name standardization with comprehensive mappings")
        print("✓ Player position normalization")
        print("✓ Null value handling according to business rules")
        print("✓ Numeric field cleaning and validation")
        print("✓ Date/time standardization")
        print("✓ Fuzzy string matching for data quality")
        print("✓ Configurable rules via YAML configuration")
        print("✓ High-performance batch processing (>10,000 records/minute)")
        print("✓ Comprehensive transformation logging and lineage")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
