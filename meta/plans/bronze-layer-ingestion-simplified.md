# Bronze Layer Ingestion - Simplified MVP

**Last Updated:** September 7, 2025  
**Status:** Updated for Simplified Roadmap  
**Supersedes:** Previous bronze-layer-ingestion.md

## Overview

Simplified bronze layer implementation focused on daily NBA box score ingestion using JSON storage for maximum development velocity and debugging ease during MVP phase.

Building on our established architectural decisions (ADR-013 NBA API data source, ADR-025 JSON storage format), this implementation focuses on the minimal viable bronze layer for the simplified roadmap.

## Simplified Architecture

```
NBA API → Raw JSON → Basic Validation → JSON Storage → S3 Bronze Layer
```

**Key Simplifications:**
- Box scores only (no play-by-play)
- JSON storage (no Parquet conversion)
- Daily batch processing (no real-time)
- Basic error handling (no complex retry logic)

## MVP Requirements

### Core Functionality
1. **Daily Box Score Retrieval**
   - Fetch previous day's completed games
   - Get box score data for each game
   - Basic JSON schema validation

2. **Data Storage**
   - Store raw JSON responses to S3
   - Simple date-based partitioning: `bronze/box-scores/YYYY-MM-DD/game-{id}.json`
   - Basic error logging

3. **Automation**
   - GitHub Actions daily workflow
   - Simple success/failure notifications

### MVP User Stories

#### Story 1: Daily Box Score Collection
**As a** data consumer  
**I want** yesterday's NBA box scores automatically collected  
**So that** I have fresh data available each morning

**Acceptance Criteria:**
- [ ] Automated daily collection of previous day's box scores
- [ ] JSON files stored in S3 with consistent naming
- [ ] Basic validation ensures data completeness
- [ ] Failed runs are logged and reported

#### Story 2: Data Accessibility
**As a** developer  
**I want** to easily inspect collected data  
**So that** I can debug issues and understand data structure

**Acceptance Criteria:**
- [ ] JSON files are human-readable in S3 console
- [ ] Clear file organization by date
- [ ] Data structure is consistent across games
- [ ] Easy local development setup for testing

## Implementation Plan

### Phase 1: Core Collection (Week 1-2)
- [ ] Create bronze-ingestion app with nba-api integration
- [ ] Implement box score fetching for single date
- [ ] Add JSON schema validation with Pydantic
- [ ] Set up S3 storage with proper partitioning
- [ ] Create basic error handling and logging

### Phase 2: Automation (Week 3-4)
- [ ] GitHub Actions workflow for daily execution
- [ ] Environment variable management for AWS credentials
- [ ] Basic monitoring and alerting for failures
- [ ] Local development and testing procedures

## Data Format

### Input: NBA API Box Scores
Using nba-api library to fetch standard box score data including:
- Game metadata (date, teams, final score)
- Player statistics (points, rebounds, assists, etc.)
- Team statistics (shooting percentages, turnovers)

### Output: S3 JSON Files
```
s3://hoopstat-bronze/box-scores/2025-09-07/
├── game-0022500001.json
├── game-0022500002.json
└── ...
```

**File Format:**
```json
{
  "game_id": "0022500001",
  "game_date": "2025-09-07",
  "away_team": {...},
  "home_team": {...},
  "player_stats": [...],
  "team_stats": {...},
  "metadata": {
    "ingestion_timestamp": "2025-09-08T06:00:00Z",
    "api_source": "nba-api",
    "schema_version": "1.0"
  }
}
```

## Technology Stack

- **Data Source:** nba-api Python library
- **Storage:** AWS S3 (JSON files)
- **Validation:** Pydantic models
- **Orchestration:** GitHub Actions
- **Language:** Python 3.11
- **Dependencies:** Minimal (nba-api, boto3, pydantic)

## Success Metrics

1. **Reliability:** 95%+ successful daily runs
2. **Completeness:** Collect 95%+ of scheduled games
3. **Performance:** Complete daily ingestion in < 15 minutes
4. **Cost:** Bronze layer storage < $10/month

## Future Considerations

After MVP validation:
- Migrate to Parquet for better analytics performance
- Add play-by-play data for advanced metrics
- Implement real-time ingestion for live games
- Add data quality monitoring and alerting
