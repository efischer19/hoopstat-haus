# Gold Layer Analytics Strategy

**Last Updated:** September 13, 2025  
**Status:** Draft - Design Document for Gold Layer Implementation

## Purpose

Define the specific analytics, aggregations, and data products that our Gold layer should provide to maximize value for AI assistant interactions through the MCP server, while keeping implementation realistic for a hobby project.

## Core Design Philosophy

**AI-First Analytics:** Every Gold layer data product should answer questions that AI assistants would naturally ask about basketball. Optimize for **common basketball questions**, not just statistical completeness.

**Box Score Foundation:** Build on data we can reliably calculate from NBA box scores, providing 80% of analytical value with 20% of the complexity. Advanced metrics requiring play-by-play data will be added as future enhancements.

## Target MCP Use Cases

### Primary Use Cases (Must Support)
1. **Player Performance Queries**
   - "How has LeBron James been playing this season?"
   - "Who are the top scorers in the league right now?"
   - "Show me Steph Curry's shooting stats from his last 10 games"

2. **Team Analysis**
   - "How are the Lakers performing this season?"
   - "Which teams have the best defense?" → Rank by defensive rating (estimated possessions)
   - "Compare the Celtics and Warriors offensive efficiency" → Compare offensive ratings
   - "How many points per 100 possessions are the Celtics allowing?" → Defensive rating calculation
   - "What's Boston's net rating over their last 10 games?" → OffRtg - DefRtg

3. **League-Wide Insights**
   - "Who are the most improved players this season?"
   - "What are the league averages for three-point shooting?"
   - "Which rookies are having the best seasons?"
   - "Rank teams by defensive performance" (estimated)

### Secondary Use Cases (Enhanced with Play-by-Play)
4. **Advanced Team Defense**
   - "Points allowed per 100 possessions" (accurate defensive rating)
   - "How does Boston's defense perform vs different pace teams?"
   - "Celtics defensive rating when their starting lineup plays"

5. **Trend Analysis**
   - "Is Giannis shooting better from three this year compared to last year?"
   - "How has the pace of play changed in the NBA over time?"

5. **Comparative Analysis**
   - "Compare Luka's current season to his MVP-caliber seasons"
   - "Which player has the most similar style to Kobe Bryant?"

## Gold Layer Data Products

### 1. Player Analytics (`GoldPlayerDailyStats`)

**Purpose:** Daily player performance with box score-derived advanced metrics for trend analysis

**Key Metrics:**
- **Fantasy Categories:** Points, rebounds, assists, steals, blocks (core fantasy roto stats)
- **Shooting Efficiency:** 
  - Field Goal %, 3-Point %, Free Throw % (basic percentages)
  - True Shooting Percentage (advanced efficiency metric using TS% = Points / (2 * (FGA + 0.44 * FTA)))
- **Overall Efficiency:** 
  - Player Efficiency Rating (PER-like): (PTS + REB + AST + STL + BLK - TOV) / MIN
- **Context:** Minutes played, turnovers, game situation

**Calculation Requirements:** ✅ All calculable from box score data only

**Future Enhancements (Requires Play-by-Play Data):**
- Usage Rate (needs team totals while player on court)
- Plus/Minus (needs possession-level tracking)
- Defensive Rating (needs opponent tracking)

**Partitioning:** `season=YYYY-YY/player_id=X/date=YYYY-MM-DD/stats.json`

**File Size:** ~1-5KB per player per game (targeting 1-10MB aggregate files)

### 2. Player Season Summaries (`GoldPlayerSeasonSummary`)

**Purpose:** Pre-computed season aggregations for fast AI queries

**Key Metrics:**
- **Per-Game Averages:** All major statistical categories
- **Shooting Efficiency:** Season FG%, 3P%, FT%, True Shooting %
- **Advanced Analytics:** Season efficiency rating, shooting trends
- **League Context:** League rank in major categories, percentile rankings
- **Performance Trends:** Month-over-month improvements in key areas

**Calculation Requirements:** ✅ All calculable from aggregated box score data

**Future Enhancements (Requires Play-by-Play Data):**
- Usage Rate trends
- Plus/Minus impact metrics
- Clutch performance (performance in close games, final 5 minutes)

**Partitioning:** `season=YYYY-YY/player_summaries/player_id=X/summary.json`

**Update Frequency:** Weekly during season, final after season ends

### 3. Team Analytics (`GoldTeamDailyStats`)

**Purpose:** Team-level metrics for organizational performance analysis

**Box Score Metrics (Phase 1 - Available Now):**
- **Offensive Performance:** Points scored, offensive rating (estimated), shooting percentages
- **Defensive Performance:** Defensive rating (estimated from possessions), opponent shooting %
- **Four Factors:** Effective FG%, Turnover Rate, Rebounding %, Free Throw Rate  
- **Pace Estimation:** Possessions per 48 minutes (estimated from box score)
- **Traditional Stats:** Team totals for points, rebounds, assists, steals, blocks
- **Recent Form:** Rolling 10-game averages for all efficiency metrics
- **Game Situational:** Home/away performance, margin of victory/defeat

**Estimated Advanced Metrics (Phase 1 - Good Accuracy):**
- **Defensive Rating:** Points allowed per 100 possessions (using estimated possessions)
- **Net Rating:** Offensive Rating - Defensive Rating
- **Pace:** Estimated possessions per 48 minutes
- **Team Efficiency Rankings:** League standings for offensive/defensive/net rating

**Calculation Requirements:** ✅ All calculable from team box score data with possession estimation

**Future Enhancements (Requires Play-by-Play Data):**
- **Lineup-Specific Ratings:** 5-man unit offensive/defensive efficiency
- **Player Defensive Impact:** Individual defensive ratings and opponent FG% when guarded  
- **Situational Performance:** Performance vs different offensive sets, pace scenarios
- **Clutch Team Performance:** Team efficiency in final 5 minutes of close games
- **Precise Pace:** Exact possessions per 48 minutes (vs estimated)

**Partitioning:** `season=YYYY-YY/team_id=X/date=YYYY-MM-DD/stats.json`

### 4. League Analytics & Team Rankings (Enhanced)

**Purpose:** League-wide context and team comparative analysis for AI queries

**Key Metrics:**
- **Team Rankings:** Offensive rating, defensive rating (estimated), net rating
- **League Averages:** By team performance tier, positional averages
- **Defensive Leaderboards:** Points allowed per game, opponent FG% (basic defensive proxies)
- **Team Efficiency Trends:** 10-game rolling averages for all teams
- **Head-to-Head Records:** Team vs team historical performance
- **Historical Context:** "Best defensive team since..." comparisons

**Target Queries:**
- "Which teams have the best defense this season?" (estimated from opponent performance)
- "How do the Celtics rank defensively over their last 10 games?"
- "What's the league average for points allowed per game?"
- "Which teams are trending up/down defensively?"

**Calculation Requirements:** ✅ All calculable from aggregated team box score data

**Future Enhancements (Requires Play-by-Play Data):**
- Accurate defensive efficiency rankings
- Pace-adjusted team comparisons
- Lineup-based team analysis

**Partitioning:** `season=YYYY-YY/league_analytics/date=YYYY-MM-DD/team_rankings.json`

## Architecture Decision: S3 Tables + AWS MCP Server

**Strategic Choice: Industry Standard Analytics with AWS-Native MCP Integration**

After cost analysis and migration evaluation (documented in ADR-026), we chose S3 Tables for optimal learning and performance:

**Cost Analysis:**
- **S3 Tables**: ~$2.28/year (manageable within $20-50 hobby budget)
- **Regular S3**: ~$1.68/year  
- **Cost difference**: Only $0.60/year - negligible for learning benefits

**Architecture Flow:**
```
Bronze S3 (JSON) → Silver Lambda → Gold S3 Tables (Iceberg) → AWS MCP Server → Direct Client Access
```

**Key Benefits:**
1. **Industry standard learning**: Apache Iceberg experience valuable for data engineering
2. **Zero infrastructure maintenance**: No custom MCP server deployment or scaling
3. **AWS-native performance**: 3x faster queries via automatic compaction and optimization
4. **Future flexibility**: Easy migration to custom MCP server reading Iceberg if needed
5. **Professional development**: Learn analytics table formats used in production systems

**Implementation Strategy:**
- Lambda writes: Silver → Gold analytics using Apache Iceberg format via S3 Tables
- AWS MCP Server: Handle natural language queries, schema discovery, direct S3 Tables access  
- S3 Tables optimization: Query-friendly partitioning with automatic performance tuning
- Client setup: Point MCP clients to our S3 Tables bucket for basketball analytics

**Data Format Transition:**
- **Breaking change from ADR-020**: Move from JSON to Apache Iceberg (Parquet + metadata)
- **Justification**: Industry standard for analytics, better query performance, AWS-native MCP integration
- **Migration impact**: Minimal changes to existing Gold data models

## Analytics Prioritization

### Phase 1: Box Score Analytics (Build First - Current Focus)
1. **Player daily stats** with True Shooting %, Efficiency Rating, shooting percentages
2. **Player season summaries** with per-game averages and league rankings  
3. **Team offensive metrics** and traditional defensive proxies (points allowed, opponent FG%)
4. **League averages and team rankings** for comparative analysis
5. **Team defensive proxies** (opponent performance, rebounding rates)

**Data Source:** NBA box score data only ✅  
**Implementation:** Straightforward calculations, reliable data quality
**Team Query Support:** ✅ Basic team defense, offensive efficiency, league rankings

### Phase 2: Enhanced Box Score Analytics (Near Term)
1. **Shooting location analysis** (if we get shot chart data from box scores)
2. **Home/Away splits** and situational performance
3. **Head-to-head matchup** history and trends
4. **Injury impact** tracking through roster changes

**Data Source:** Enhanced box score data and roster information

### Phase 3: Play-by-Play Analytics (Future - Requires Bronze Layer Expansion)
1. **Usage Rate** (accurate team context calculations)
2. **Plus/Minus impact** metrics 
3. **Defensive Rating** (opponent performance when guarded)
4. **Clutch performance** (final 5 minutes of close games)
5. **Pace calculation** (accurate possessions per 48 minutes)
6. **Lineup analysis** (5-man unit performance)

**Data Source:** NBA play-by-play data ❌ (requires future Bronze layer enhancement)

### Phase 4: Advanced Analytics (Long Term)
1. **Predictive metrics** (likely performance based on trends)
2. **Player similarity** algorithms  
3. **Trade value** assessments
4. **Draft prospect** comparisons

## Storage Strategy Optimization

### Revised from ADR-020 for JSON Storage

**S3 Structure:**
```
s3://hoopstat-haus-gold/
├── player_daily_stats/
│   └── season=2024-25/
│       ├── player_id=2544/          # LeBron James
│       │   ├── 2024-10-15.json      # Individual game
│       │   ├── 2024-10-18.json
│       │   └── recent_10_games.json # Rolling aggregation
│       └── player_id=1628983/       # Jayson Tatum
├── player_season_summaries/
│   └── season=2024-25/
│       ├── all_players_summary.json # Full league for fast queries
│       └── by_player/
│           ├── 2544.json            # Individual player details
│           └── 1628983.json
├── team_daily_stats/
│   └── season=2024-25/
│       └── team_id=1610612747/      # Lakers
├── league_analytics/
│   └── season=2024-25/
│       ├── current_averages.json
│       ├── standings.json
│       └── leader_boards.json
```

### File Size Targets
- **Daily player files:** 1-5KB each
- **Season summaries:** 10-50KB per player  
- **League aggregations:** 100KB-1MB total
- **Lambda memory usage:** Target <256MB for Gold processing

## Calculation Specifications

### Box Score Advanced Metrics Formulas

**True Shooting Percentage:**
```python
# Formula: Points / (2 * (FGA + 0.44 * FTA))
# Data Required: Points, Field Goal Attempts, Free Throw Attempts ✅
def calculate_true_shooting_percentage(points: int, fga: int, fta: int) -> float:
    return points / (2 * (fga + 0.44 * fta)) if (fga + 0.44 * fta) > 0 else 0.0
```

**Player Efficiency Rating (Simplified):**
```python
# Formula: (PTS + REB + AST + STL + BLK - TOV) / MIN
# Data Required: All basic box score stats ✅
# Implementation: Already exists in hoopstat_data.transforms.calculate_efficiency_rating()
```

**Basic Shooting Percentages:**
```python
# FG% = FGM / FGA, 3P% = 3PM / 3PA, FT% = FTM / FTA
# Data Required: Made/Attempted for each shot type ✅
```

**Team Offensive/Defensive Rating (Estimated):**
```python
# Possession Estimation: FGA - OREB + TOV + 0.44 * FTA
team_possessions = team_fga - team_oreb + team_tov + 0.44 * team_fta

# Offensive Rating: 100 * (Points Scored / Team Possessions)
offensive_rating = 100 * (team_points / team_possessions)

# Defensive Rating: 100 * (Opponent Points / Estimated Game Possessions)  
game_possessions = (team_possessions + opponent_possessions) / 2
defensive_rating = 100 * (opponent_points / game_possessions)

# Data Required: Team and opponent box score totals ✅
# Accuracy: Very good for team-level analysis, estimated possessions ~95% accurate
```

**Team Pace (Estimated):**
```python
# Pace: Possessions per 48 minutes
pace = (game_possessions * 48) / total_minutes_played
# Data Required: Box score totals + game length ✅
# Accuracy: Good estimation, within 2-3 possessions of actual
```

**Net Rating:**
```python
# Net Rating: Offensive Rating - Defensive Rating
net_rating = offensive_rating - defensive_rating
# Positive = team outscores opponents per 100 possessions
# Data Required: Calculated from above metrics ✅
```

### Future Play-by-Play Metrics (Phase 3)

**Usage Rate (Accurate):**
```python
# Formula: ((FGA + 0.44 * FTA + TOV) * (Team MP / 5)) / (MP * (Team FGA + 0.44 * Team FTA + Team TOV))
# Data Required: Team totals WHILE PLAYER WAS ON COURT ❌
# Requires: Play-by-play tracking of player on/off court
```

**Plus/Minus:**
```python
# Formula: Team points scored - Team points allowed while player on court
# Data Required: Possession-by-possession scoring with player tracking ❌
# Requires: Play-by-play data with lineup tracking
```

**Defensive Rating (Accurate):**
```python
# Formula: 100 * (Opponent points scored / Possessions while player on court)
# Data Required: Opponent performance when defended by specific player ❌
# Requires: Play-by-play defensive assignment tracking
```

### Data Quality Thresholds
- **Minimum minutes for player inclusion:** 10 minutes per game
- **Sample size for percentages:** Minimum 5 attempts
- **Missing data handling:** Default to league average when appropriate
- **Outlier detection:** Flag performances >3 standard deviations from player mean

## MCP Server Query Optimization

### Pre-computed Query Responses
1. **"Top performers today"** → Daily leader boards JSON
2. **"League standings"** → Current standings with recent form
3. **"Player season stats"** → Direct file access by player_id
4. **"Team comparison"** → Aggregate comparison metrics

### Response Time Targets
- **Simple player lookup:** <200ms
- **League-wide aggregations:** <500ms  
- **Complex comparisons:** <1000ms
- **Historical trends:** <2000ms

## Implementation Notes

### Data Source Strategy
- **Phase 1:** Box score data only (current Bronze layer capability)
- **Phase 3:** Play-by-play data (requires Bronze layer expansion)
- **Quality:** Prefer reliable box score calculations over estimated play-by-play metrics

### Data Lineage
- Track transformation from Silver → Gold with timestamps
- Include data quality scores and validation results
- Maintain backward compatibility with schema evolution
- Document which metrics require play-by-play data vs box score only

### Error Handling
- Graceful degradation when advanced metrics can't be calculated
- Clear distinction between "no data", "insufficient data", and "requires play-by-play data"
- Fallback to simpler metrics when complex calculations fail
- Explicit flags for metrics that need enhanced data sources

### Testing Strategy
- Unit tests for all metric calculations
- Integration tests with known NBA statistical outcomes
- Performance benchmarks for query response times
- Data quality validation against external NBA data sources

## Questions for Discussion

1. **Box Score Focus:** Does this box score-first approach provide sufficient value for fantasy basketball and basic AI queries?

2. **Implementation Priority:** Should we build the simplified Gold layer first, then enhance Silver-to-Gold processing with play-by-play metrics later?

3. **Fantasy Integration:** Are True Shooting % and Efficiency Rating sufficient advanced metrics for initial fantasy basketball analysis?

4. **Data Quality:** How should we handle the transition from estimated metrics (box score) to accurate metrics (play-by-play)?

5. **Storage Strategy:** Continue with JSON for consistency, or optimize larger aggregations with different formats?

## Next Steps

1. **Validate approach** with this updated box score-focused strategy
2. **Simplify Gold models** to match Phase 1 analytics scope
3. **Implement calculation functions** for TS% and other box score metrics
4. **Create focused GitHub issues** for Phase 1 Gold layer development
5. **Plan Bronze layer expansion** roadmap for future play-by-play ingestion

---

*This updated strategy focuses on delivering immediate value through reliable box score analytics while maintaining a clear path for future enhancement with play-by-play data. The goal is 80% of analytical value with 20% of the complexity.*
