# Silver to Gold ETL Jobs Implementation Plan

**Status:** Planning  
**Date:** 2025-01-18  
**Author:** AI Contributor  
**Scope:** Define a simple, focused ETL implementation for transforming Silver layer data into basic Gold layer aggregations

## Executive Summary

This plan defines a **minimal viable implementation** for Silver to Gold ETL jobs that transform cleaned Silver layer NBA data into basic business-ready aggregations for public consumption via stateless JSON artifacts (per ADR-027). Following the project's "favor simplicity & static-first design" philosophy, this plan focuses on establishing one foundational pattern that can be incrementally extended.

The implementation starts with **player daily statistics aggregation** as the single core use case, using simple AWS Lambda functions triggered by S3 events. This approach prioritizes getting a working, maintainable system operational quickly rather than building comprehensive infrastructure upfront.

Additional complexity (orchestration, advanced metrics, team analytics) will be added iteratively based on actual usage patterns and requirements.

## Implementation Strategy - Start Simple

### Core Principle: One Pattern, Done Well

Rather than building complex orchestration systems upfront, we'll implement a single, well-tested ETL pattern that can be replicated and extended:

**Pattern: Daily Player Statistics Aggregation**
- **Input:** Silver layer player game logs (Parquet or JSON depending on Silver impl)
- **Output:** Gold-served JSON artifacts under `s3://.../gold/served/` (≤100KB each)
- **Infrastructure:** Batch job or Lambda; emit JSON alongside any internal formats
- **Success Criteria:** Valid JSON artifacts with correct schema; size limits enforced

### Minimal ETL Architecture (Stateless JSON)

```
Silver Layer: s3://bucket/silver/player_games/season=2023/date=2024-01-15/
    ↓ [Batch/Lambda]
Transform: aggregate daily and compute metrics
    ↓
Gold-served (Public): s3://bucket/gold/served/
  ├── player_daily/{date}/{player_id}.json
  ├── team_daily/{date}/{team_id}.json
  ├── top_lists/{date}/{metric}.json
  └── index/latest.json
    ↓
Logs + Size Validation (per ADR-018)
```

### Processing Logic (Keep It Simple)

The ETL job will:
1. **Extract:** Read yesterday's player game data from Silver layer
2. **Transform:** Calculate basic daily aggregations:
   - Points, rebounds, assists per game
   - Season-to-date cumulative stats
   - Simple shooting percentages (FG%, 3P%, FT%)
3. **Load:** Write versioned JSON artifacts to Gold-served (≤100KB per file)
4. **Validate:** Basic row count and null checks only

**No complex metrics initially:** No PER, Win Shares, or advanced analytics until the foundation is solid.
**Rationale:** Aligns with project's Python-first approach while providing flexibility

#### Orchestration Approach
**Primary:** AWS Step Functions for complex, multi-stage workflows
**Secondary:** EventBridge for simple event-driven processing
**Rationale:** Serverless, cost-effective, integrates with existing AWS infrastructure

#### Data Quality Integration
**Validation Framework:** Custom validation library with configurable rules
**Quality Metrics:** Completeness, consistency, timeliness tracking
**Error Handling:** Quarantine invalid results, alert on quality degradation

### Public Serving Notes

- Emit human-readable fields (player_name, team_abbr) to reduce client lookups
- Maintain a lightweight `latest.json` index for easy discovery
- Keep payloads small; split or paginate if necessary

## Implementation Example: Player Daily Statistics

### Input (Silver Layer)
```
s3://hoopstat-haus-silver/game_statistics/season=2023-24/date=2024-01-15/
├── player_game_stats.parquet  # Clean, validated game stats from Bronze-to-Silver ETL
```

### Simple Lambda Function Logic
```python
import pandas as pd
import boto3

def lambda_handler(event, context):
    # 1. Extract: Read yesterday's player game data
    df = pd.read_parquet(f"s3://bucket/silver/game_statistics/season={season}/date={yesterday}/")
    
    # 2. Transform: Basic aggregations only
    daily_stats = df.groupby('player_id').agg({
        'points': 'sum',
        'rebounds': 'sum', 
        'assists': 'sum',
        'field_goals_made': 'sum',
        'field_goals_attempted': 'sum'
    })
    
    # 3. Calculate simple percentages
    daily_stats['fg_percentage'] = daily_stats['field_goals_made'] / daily_stats['field_goals_attempted']
    
    # 4. Load: Write to Gold layer (one file per player)
    for player_id, stats in daily_stats.iterrows():
        stats.to_parquet(f"s3://bucket/gold/player_daily_stats/season={season}/player_id={player_id}/daily_stats.parquet")
    
    return {"status": "success", "players_processed": len(daily_stats)}
```

### Output (Gold Layer)
```
s3://hoopstat-haus-gold/player_daily_stats/
├── season=2023-24/player_id=123/daily_stats.parquet
└── season=2023-24/player_id=456/daily_stats.parquet
```

## Required ADRs (Minimal Set)

We need only **2 new ADRs** to get started:

### ADR-019: Basic ETL Error Handling and Monitoring Strategy
- **Decision Scope:** How ETL jobs handle failures and report status
- **Key Areas:** CloudWatch integration, basic retry logic, alerting
- **Impact:** Operational reliability for daily processing
- **Dependencies:** ADR-018 (CloudWatch observability)

### ADR-020: Gold Layer Data Partitioning for MCP Performance
- **Decision Scope:** How to partition Gold layer data for fast MCP server queries
- **Key Areas:** S3 key structure, file sizing, query patterns
- **Impact:** MCP server response times and storage costs
- **Dependencies:** ADR-014 (Parquet format), MCP server requirements

**Deferred ADRs:** Processing frameworks, advanced libraries, orchestration, real-time processing - all can be addressed later when we have usage data.

## Implementation Roadmap (Iterative)

### Phase 1: Foundation (2 weeks)
- [ ] Implement basic Lambda function for player daily stats
- [ ] Set up S3 event trigger for Silver layer updates
- [ ] Create CloudWatch monitoring and basic alerting
- [ ] Write ADR-019 and ADR-020

### Phase 2: Validation (1 week)  
- [ ] Add data quality checks to Lambda function
- [ ] Test with sample Silver layer data
- [ ] Verify MCP server can read Gold layer format
- [ ] Document any performance issues

### Phase 3: Extension (As Needed)
- [ ] Add more aggregation types based on MCP server usage
- [ ] Consider team-level aggregations if needed
- [ ] Evaluate performance and consider optimizations

**Total Timeline:** 3-4 weeks for functional system vs. 12 weeks in complex approach

## Success Criteria (Keep It Simple)

### Technical Success
- [ ] Daily ETL job runs successfully 95% of the time
- [ ] Processing completes within 2 hours of Silver layer data availability
- [ ] MCP server can query Gold layer with sub-500ms response times
- [ ] CloudWatch provides visibility into job status and errors

### Business Success
- [ ] Player statistics available for MCP server queries
- [ ] Data freshness meets user expectations (same-day availability)
- [ ] System operates under $10/month in AWS costs

**No complex metrics initially:** Advanced analytics, sophisticated monitoring, and performance optimization can be added incrementally as usage grows.

## Next Steps

1. **Start with the Bronze-to-Silver ETL (already planned)** - need clean Silver data first
2. **Implement this simple Silver-to-Gold pattern** - get basic aggregations working
3. **Integrate with MCP server** - validate the end-to-end flow
4. **Iterate based on actual usage** - add complexity only when justified by real requirements

This approach follows the project philosophy: start simple, validate assumptions, add complexity incrementally based on real needs rather than speculative requirements.