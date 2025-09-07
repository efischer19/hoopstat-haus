# Fantasy Basketball Roto Scoring Engine

**Status:** Hackathon Idea  
**Created:** September 7, 2025  
**Build Complexity:** Medium (leverages existing hoopstat-haus infrastructure)

## Concept Overview

A backend service that calculates rotisserie (roto) fantasy basketball league standings. Given roster data, returns calculated league state with rankings and scores across multiple statistical categories.

## Fantasy Basketball Rules

### Scoring System: Rotisserie
- **Categories:** Points, Rebounds, Assists, Steals+Blocks (4 total)
- **Scoring:** 1st place in category = N points, 2nd = N-1, etc. (where N = number of teams)
- **Periods:** Monthly scoring periods during regular season
- **Roster Management:** Not our concern - injuries/changes handled by updating next period's rosters

### Data Requirements
- Daily NBA player statistics (✅ already available via our bronze layer)
- Team roster assignments per scoring period
- League configuration (number of teams, team names)

## Technical Architecture

### Leverages Existing Hoopstat-Haus Infrastructure

```
Existing: Bronze → Silver → Gold (player stats)
                     ↓
New:        Fantasy Engine → Roto Calculations → League Standings
```

**Data Flow:**
1. **Input:** League roster JSON (team assignments per period)
2. **Process:** Aggregate player stats from Gold layer by team/period
3. **Calculate:** Roto scores across 4 categories
4. **Output:** League standings JSON with rankings and scores

### API Design

**Endpoint:** `POST /calculate-league`

**Input JSON:**
```json
{
  "league_id": "my-league-2025",
  "scoring_period": "2025-01",
  "teams": [
    {
      "team_name": "Team Alpha",
      "roster": ["LeBron James", "Stephen Curry", "Giannis Antetokounmpo"]
    },
    {
      "team_name": "Team Beta", 
      "roster": ["Jayson Tatum", "Luka Doncic", "Nikola Jokic"]
    }
  ]
}
```

**Output JSON:**
```json
{
  "league_id": "my-league-2025",
  "scoring_period": "2025-01",
  "category_standings": {
    "points": [
      {"team": "Team Alpha", "total": 2847, "rank": 1, "roto_points": 2},
      {"team": "Team Beta", "total": 2654, "rank": 2, "roto_points": 1}
    ],
    "rebounds": [...],
    "assists": [...],
    "steals_blocks": [...]
  },
  "overall_standings": [
    {"team": "Team Alpha", "total_roto_points": 7, "rank": 1},
    {"team": "Team Beta", "total_roto_points": 5, "rank": 2}
  ],
  "period_summary": {
    "games_included": 45,
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
  }
}
```

## Implementation Plan

### Phase 1: Core Engine (2-3 days)
- [ ] Create new `fantasy-roto` app in monorepo
- [ ] Implement player stat aggregation from Gold layer
- [ ] Build roto scoring calculation logic
- [ ] Create basic API endpoint structure

### Phase 2: API Service (1-2 days)
- [ ] FastAPI or Flask web service
- [ ] JSON schema validation for inputs
- [ ] Error handling for missing players/invalid rosters
- [ ] Basic testing suite

### Phase 3: Enhancement (1 day)
- [ ] Multiple league support
- [ ] Historical period calculations
- [ ] Performance optimization for large leagues
- [ ] Containerization for deployment

## Technical Considerations

### Data Dependencies
- **Player Name Matching:** Need robust player name → NBA stats mapping
- **Period Boundaries:** Handle months that span multiple calendar months
- **Missing Data:** Handle games not played, injured players, etc.

### Performance
- **Caching:** Cache monthly aggregations to avoid recalculation
- **Async Processing:** For large leagues with many teams
- **Database:** Store league configurations and historical results

### Error Handling
- **Unknown Players:** Return clear errors for players not found in NBA data
- **Invalid Periods:** Validate scoring period exists in our data
- **Empty Rosters:** Handle teams with insufficient players

## Integration with Existing Stack

### Shared Libraries to Use
- **hoopstat-data:** Player stat aggregation utilities
- **hoopstat-config:** Configuration management
- **hoopstat-observability:** Logging and monitoring

### Gold Layer Extensions
Might need to enhance Gold layer with:
- Monthly player stat aggregations (if not already available)
- Player name normalization/matching tables
- Combined steals+blocks calculations

## Example Use Cases

### Hackathon Demo
```bash
# 1. Set up a 4-team league for January 2025
curl -X POST http://localhost:8000/calculate-league \
  -H "Content-Type: application/json" \
  -d @demo-league.json

# 2. Get results showing team standings and category rankings
# 3. Demonstrate how different roster combinations affect rankings
```

### Production Scenarios
- **Fantasy League Websites:** Integrate as backend scoring engine
- **Mobile Apps:** Daily league updates via API
- **Analytics Tools:** Historical league performance analysis
- **Social Platforms:** Automated league result sharing

## Success Metrics

- **Accuracy:** Calculations match manual verification
- **Performance:** Handle 12-team league calculation in < 2 seconds
- **Reliability:** Handle edge cases (missing players, incomplete data)
- **Usability:** Clear error messages and intuitive API design

## Future Extensions (Post-Hackathon)

- **Playoffs Support:** Tournament-style elimination scoring
- **Custom Categories:** User-defined stat categories and weights
- **Live Updates:** Real-time scoring during games
- **Head-to-Head Mode:** Alternative to roto scoring
- **Trade Analysis:** Impact analysis for roster changes
- **Mobile App:** Simple frontend for league management

## Why This Works as a Hackathon Project

✅ **Builds on existing infrastructure** - Leverages your Bronze→Silver→Gold pipeline  
✅ **Focused scope** - Clear deliverable with defined boundaries  
✅ **Practical value** - Solves real fantasy basketball need  
✅ **Extensible** - Natural progression from MVP to full product  
✅ **Demonstrable** - Easy to show working calculations and rankings  
✅ **Time-boxed** - Can build MVP in 2-3 days, polish in 1-2 more
