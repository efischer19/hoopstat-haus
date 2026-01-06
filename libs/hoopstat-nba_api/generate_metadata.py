#!/usr/bin/env python3
"""
Generate static metadata JSON files for teams and players.

This script extracts data from the nba_api library and creates versioned
JSON files containing team and player metadata for use across the application.
"""

import json
from pathlib import Path

from nba_api.stats.static import players, teams

# Constants
JSON_INDENT = 2  # Consistent indentation for all JSON files

# Manual conference mapping (as of 2024-25 season)
# This is relatively stable but should be updated if teams change conferences
TEAM_CONFERENCES = {
    1610612737: "Eastern",  # Atlanta Hawks
    1610612738: "Eastern",  # Boston Celtics
    1610612751: "Eastern",  # Brooklyn Nets
    1610612766: "Eastern",  # Charlotte Hornets
    1610612741: "Eastern",  # Chicago Bulls
    1610612739: "Eastern",  # Cleveland Cavaliers
    1610612742: "Western",  # Dallas Mavericks
    1610612743: "Western",  # Denver Nuggets
    1610612765: "Eastern",  # Detroit Pistons
    1610612744: "Western",  # Golden State Warriors
    1610612745: "Western",  # Houston Rockets
    1610612754: "Eastern",  # Indiana Pacers
    1610612746: "Western",  # LA Clippers
    1610612747: "Western",  # Los Angeles Lakers
    1610612763: "Western",  # Memphis Grizzlies
    1610612748: "Eastern",  # Miami Heat
    1610612749: "Eastern",  # Milwaukee Bucks
    1610612750: "Western",  # Minnesota Timberwolves
    1610612740: "Western",  # New Orleans Pelicans
    1610612752: "Eastern",  # New York Knicks
    1610612760: "Western",  # Oklahoma City Thunder
    1610612753: "Eastern",  # Orlando Magic
    1610612755: "Eastern",  # Philadelphia 76ers
    1610612756: "Western",  # Phoenix Suns
    1610612757: "Western",  # Portland Trail Blazers
    1610612758: "Western",  # Sacramento Kings
    1610612759: "Western",  # San Antonio Spurs
    1610612761: "Eastern",  # Toronto Raptors
    1610612762: "Western",  # Utah Jazz
    1610612764: "Eastern",  # Washington Wizards
}


def generate_teams_metadata():
    """Generate teams_v1.json with team metadata."""
    all_teams = teams.get_teams()

    # Transform to desired format
    teams_metadata = []
    for team in all_teams:
        team_id = team["id"]

        # Ensure we have conference mapping for all teams
        if team_id not in TEAM_CONFERENCES:
            raise ValueError(
                f"Missing conference mapping for team {team['full_name']} "
                f"(ID: {team_id}). Please update TEAM_CONFERENCES."
            )

        teams_metadata.append(
            {
                "id": team_id,
                "name": team["full_name"],
                "abbreviation": team["abbreviation"],
                "city": team["city"],
                "conference": TEAM_CONFERENCES[team_id],
            }
        )

    # Sort by name for consistency
    teams_metadata.sort(key=lambda x: x["name"])

    return {
        "schema_version": "v1",
        "generated_from": "nba_api.stats.static.teams",
        "note": "Conference mapping manually maintained for 2024-25 season",
        "teams": teams_metadata,
    }


def generate_players_metadata():
    """Generate players_v1.json with active player metadata."""
    all_players = players.get_players()

    # Filter to active players only
    # Validate that is_active field exists for all players
    active_players = []
    for p in all_players:
        if "is_active" not in p:
            raise ValueError(
                f"Missing is_active field for player {p.get('full_name', 'Unknown')} "
                f"(ID: {p.get('id', 'Unknown')})"
            )
        if p["is_active"]:
            active_players.append(p)

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
        json.dump(teams_data, f, indent=JSON_INDENT, ensure_ascii=False)
    print(f"✓ Generated {teams_file}")
    print(f"  Total teams: {len(teams_data['teams'])}")

    # Generate players metadata
    players_data = generate_players_metadata()
    players_file = output_dir / "players_v1.json"
    with open(players_file, "w", encoding="utf-8") as f:
        json.dump(players_data, f, indent=JSON_INDENT, ensure_ascii=False)
    print(f"✓ Generated {players_file}")
    print(f"  Total active players: {len(players_data['players'])}")

    print("\n✅ Metadata generation complete!")


if __name__ == "__main__":
    main()
