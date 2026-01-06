#!/usr/bin/env python3
"""
Generate static metadata JSON files for teams and players.

This script extracts data from the nba_api library and creates versioned
JSON files containing team and player metadata for use across the application.
"""

import json
from pathlib import Path

from nba_api.stats.static import players, teams


def generate_teams_metadata():
    """Generate teams_v1.json with team metadata."""
    all_teams = teams.get_teams()

    # Transform to desired format
    teams_metadata = []
    for team in all_teams:
        teams_metadata.append(
            {
                "id": team["id"],
                "name": team["full_name"],
                "abbreviation": team["abbreviation"],
                "city": team["city"],
                # Note: conference is not available in nba_api static data
                # This would require additional API calls or manual mapping
            }
        )

    # Sort by name for consistency
    teams_metadata.sort(key=lambda x: x["name"])

    return {
        "schema_version": "v1",
        "generated_from": "nba_api.stats.static.teams",
        "note": "Conference field not available in nba_api static data",
        "teams": teams_metadata,
    }


def generate_players_metadata():
    """Generate players_v1.json with active player metadata."""
    all_players = players.get_players()

    # Filter to active players only
    active_players = [p for p in all_players if p.get("is_active", False)]

    # Transform to desired format
    players_metadata = []
    for player in active_players:
        players_metadata.append(
            {
                "id": player["id"],
                "name": player["full_name"],
                # Note: team_id and position are not available in nba_api static data
                # These would require additional API calls or manual mapping
                "active": player["is_active"],
            }
        )

    # Sort by name for consistency
    players_metadata.sort(key=lambda x: x["name"])

    return {
        "schema_version": "v1",
        "generated_from": "nba_api.stats.static.players (active only)",
        "note": "team_id and position fields not available in nba_api static data",
        "players": players_metadata,
    }


def main():
    """Generate both metadata files."""
    # Determine output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir / "hoopstat_nba_api" / "static"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate teams metadata
    teams_data = generate_teams_metadata()
    teams_file = output_dir / "teams_v1.json"
    with open(teams_file, "w", encoding="utf-8") as f:
        json.dump(teams_data, f, indent=2, ensure_ascii=False)
    print(f"✓ Generated {teams_file}")
    print(f"  Total teams: {len(teams_data['teams'])}")

    # Generate players metadata
    players_data = generate_players_metadata()
    players_file = output_dir / "players_v1.json"
    with open(players_file, "w", encoding="utf-8") as f:
        json.dump(players_data, f, indent=2, ensure_ascii=False)
    print(f"✓ Generated {players_file}")
    print(f"  Total active players: {len(players_data['players'])}")

    print("\n✅ Metadata generation complete!")


if __name__ == "__main__":
    main()
