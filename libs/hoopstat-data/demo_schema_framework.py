#!/usr/bin/env python3
"""
Demo script showcasing the Pydantic schema validation framework features.

This script demonstrates:
1. Schema validation with different strictness levels
2. Data lineage tracking
3. NBA-specific business rule validation
4. JSON schema generation
5. Schema evolution capabilities
"""

import json

from hoopstat_data.models import (
    DataLineage,
    GameStats,
    PlayerStats,
    SchemaEvolution,
    TeamStats,
    ValidationMode,
    generate_json_schema,
    get_schema_version,
)


def main():
    print("🏀 Hoopstat Haus Pydantic Schema Validation Framework Demo")
    print("=" * 60)

    # 1. Demonstrate Data Lineage Tracking
    print("\n1. Data Lineage Tracking")
    print("-" * 30)

    nba_api_lineage = DataLineage(
        source_system="nba_api",
        schema_version=get_schema_version(),
        transformation_stage="silver",
        validation_mode=ValidationMode.STRICT,
    )

    print(
        f"✅ Created lineage: {nba_api_lineage.source_system} v{nba_api_lineage.schema_version}"
    )
    print(f"   Ingested at: {nba_api_lineage.ingestion_timestamp}")
    print(f"   Stage: {nba_api_lineage.transformation_stage}")
    print(f"   Validation: {nba_api_lineage.validation_mode}")

    # 2. Demonstrate Strict vs Lenient Validation
    print("\n2. Validation Strictness Levels")
    print("-" * 30)

    # Strict mode example
    try:
        strict_lineage = DataLineage(
            source_system="test_api",
            schema_version=get_schema_version(),
            transformation_stage="silver",
            validation_mode=ValidationMode.STRICT,
        )

        player = PlayerStats(
            lineage=strict_lineage,
            player_id="player_001",
            player_name="LeBron James",
            points=150,  # Unreasonably high
            rebounds=8,
            assists=7,
            steals=2,
            blocks=1,
            turnovers=3,
        )
        print("❌ Strict mode should have rejected high points")
    except ValueError as e:
        print(f"✅ Strict mode rejected: {e}")

    # Lenient mode example
    lenient_lineage = DataLineage(
        source_system="test_api",
        schema_version=get_schema_version(),
        transformation_stage="silver",
        validation_mode=ValidationMode.LENIENT,
    )

    player = PlayerStats(
        lineage=lenient_lineage,
        player_id="player_001",
        player_name="LeBron James",
        points=150,  # High but allowed in lenient mode
        rebounds=8,
        assists=7,
        steals=2,
        blocks=1,
        turnovers=3,
    )
    print(f"✅ Lenient mode allowed high points: {player.points}")

    # 3. Demonstrate NBA-Specific Validators
    print("\n3. NBA-Specific Business Rules")
    print("-" * 30)

    # Valid NBA game
    game = GameStats(
        lineage=nba_api_lineage,
        game_id="game_20241215_lal_bos",
        home_team_id="lakers",
        away_team_id="celtics",
        home_score=112,
        away_score=108,
        season="2024-25",
        game_date="2024-12-15T20:00:00Z",
        quarters=4,
    )
    print(
        f"✅ Valid NBA game: {game.home_team_id} {game.home_score} - {game.away_team_id} {game.away_score}"
    )

    # Test business rule: teams can't play themselves
    try:
        GameStats(
            lineage=nba_api_lineage,
            game_id="invalid_game",
            home_team_id="lakers",
            away_team_id="lakers",  # Same team!
            home_score=100,
            away_score=95,
        )
        print("❌ Should have rejected same team matchup")
    except ValueError as e:
        print(f"✅ NBA rule enforced: {e}")

    # 4. Demonstrate JSON Schema Generation
    print("\n4. JSON Schema Generation")
    print("-" * 30)

    player_schema = generate_json_schema(PlayerStats)
    print(
        f"✅ Generated PlayerStats schema with {len(player_schema['properties'])} properties"
    )
    print(f"   Required fields: {player_schema['required']}")

    team_schema = generate_json_schema(TeamStats)
    print(
        f"✅ Generated TeamStats schema with {len(team_schema['properties'])} properties"
    )

    game_schema = generate_json_schema(GameStats)
    print(
        f"✅ Generated GameStats schema with {len(game_schema['properties'])} properties"
    )

    # Save schema to file for external validation
    with open("/tmp/player_stats_schema.json", "w") as f:
        json.dump(player_schema, f, indent=2)
    print("📄 Saved PlayerStats schema to /tmp/player_stats_schema.json")

    # 5. Demonstrate Schema Evolution
    print("\n5. Schema Evolution")
    print("-" * 30)

    # Simulate old data format
    old_data = {
        "player_id": "legacy_player_123",
        "points": 25,
        "rebounds": 8,
        "assists": 5,
        "steals": 2,
        "blocks": 1,
        "turnovers": 3,
    }

    # Migrate from old version
    migrated_data = SchemaEvolution.migrate_from_version(
        old_data, from_version="0.1.0", to_version="1.0.0"
    )

    print("✅ Migrated data from v0.1.0 to v1.0.0")
    print(f"   Added lineage tracking: {migrated_data['lineage']['source_system']}")

    # Create player with migrated data
    migrated_player = PlayerStats(**migrated_data)
    print(f"✅ Created player from migrated data: {migrated_player.player_id}")

    # 6. Demonstrate Backward Compatibility
    print("\n6. Backward Compatibility")
    print("-" * 30)

    # Old-style creation without lineage (should auto-generate)
    legacy_player = PlayerStats(
        player_id="legacy_player_456",
        player_name="Michael Jordan",
        points=35,
        rebounds=6,
        assists=5,
        steals=3,
        blocks=1,
        turnovers=2,
    )

    print("✅ Created legacy player without explicit lineage")
    print(f"   Auto-generated lineage: {legacy_player.lineage.source_system}")
    print(f"   Schema version: {legacy_player.lineage.schema_version}")

    # 7. Performance Demonstration
    print("\n7. Performance & Error Messaging")
    print("-" * 30)

    try:
        # Test comprehensive error messages
        PlayerStats(
            player_id="test_player",
            player_name="",  # Empty name
            points=25,
            rebounds=8,
            assists=7,
            steals=2,
            blocks=1,
            turnovers=3,
            field_goals_made=15,
            field_goals_attempted=10,  # Inconsistent with made
            unknown_field="should_fail",  # Extra field
        )
    except ValueError as e:
        print(f"✅ Comprehensive error message: {str(e)[:100]}...")

    # Test string stripping
    clean_player = PlayerStats(
        player_id="  spaced_player  ",
        player_name="  Stephen Curry  ",
        points=30,
        rebounds=5,
        assists=8,
        steals=2,
        blocks=0,
        turnovers=4,
    )

    print(
        f"✅ String stripping works: '{clean_player.player_id}' and '{clean_player.player_name}'"
    )

    print("\n🎉 Schema validation framework demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
