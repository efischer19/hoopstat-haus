# Static NBA Metadata

This directory contains static JSON metadata files for NBA teams and players.

## Files

### teams_v1.json
Contains metadata for all NBA teams.

**Fields:**
- `id`: NBA team ID
- `name`: Full team name (e.g., "Los Angeles Lakers")
- `abbreviation`: Team abbreviation (e.g., "LAL")
- `city`: Team city (e.g., "Los Angeles")
- `conference`: Team conference ("Eastern" or "Western")

**Note:** Conference assignments are manually maintained for the current season (2024-25). While conferences change rarely, this mapping should be verified annually.

### players_v1.json
Contains metadata for active NBA players only.

**Fields:**
- `id`: NBA player ID
- `name`: Full player name (e.g., "LeBron James")
- `active`: Boolean indicating active status (always `true` in this file)

**Note:** The `team_id` and `position` fields are not available in the nba_api static data. To add this information would require:
1. Additional API calls to fetch current roster information
2. Regular updates as players change teams and roles

## Data Source

All data is extracted from the `nba_api` Python package's static data module:
- `nba_api.stats.static.teams` for team data
- `nba_api.stats.static.players` for player data (filtered to active players only)

Reference: https://github.com/swar/nba_api/blob/master/src/nba_api/stats/library/data.py

## Generating/Updating

To regenerate the metadata files with the latest data from nba_api:

```bash
cd libs/hoopstat-nba_api
poetry run python generate_metadata.py
```

## Size

- `teams_v1.json`: ~4KB (30 teams)
- `players_v1.json`: ~49KB (572 active players)

Both files are well under typical size limits for static metadata files.

## Schema Version

Both files use `schema_version: "v1"` to support future schema evolution. If fields are added or changed in a breaking way, a new version (v2, etc.) should be created.

## Future Enhancements

To fully meet the original requirements, consider:

1. **Team assignments for players**: Use the `CommonPlayerInfo` endpoint to fetch current team for each player
2. **Position data for players**: Use the `CommonPlayerInfo` endpoint to fetch player positions
3. **Automated conference updates**: Monitor for conference realignment and update mappings
4. **Automated updates**: Schedule periodic regeneration of these files to keep player data fresh
5. **Validation**: Expand tests to verify data against live API for accuracy
