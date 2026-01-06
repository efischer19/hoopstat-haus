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

**Note:** The `conference` field is not available in the nba_api static data. To add conference information would require either:
1. Additional API calls to fetch current team conference assignments
2. Manual mapping/hardcoding of conference data (which may become stale)

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

1. **Conference data for teams**: Add API calls to fetch current standings/conference data, or maintain a manual mapping
2. **Team assignments for players**: Use the `CommonPlayerInfo` endpoint to fetch current team for each player
3. **Position data for players**: Use the `CommonPlayerInfo` endpoint to fetch player positions
4. **Automated updates**: Schedule periodic regeneration of these files to keep data fresh
5. **Validation**: Add tests to ensure data completeness and correctness
