---
title: "ADR-020: Gold Layer Data Partitioning for MCP Performance"
status: "Superseded"
date: "2025-07-24"
superseded_by: "ADR-026"
superseded_date: "2025-09-13"
tags:
  - "data-pipeline"
  - "partitioning"
  - "performance"
  - "mcp-server"
---

## Context

* **Problem:** The Gold layer needs an optimal partitioning strategy to support fast MCP server queries while minimizing storage costs and Lambda memory usage. Current Silver layer data requires transformation into business-ready aggregations with efficient query patterns for AI agent interactions.
* **Constraints:** Must leverage AWS S3 per ADR-009, use Parquet format per ADR-014, integrate with CloudWatch observability per ADR-018, support Lambda function memory limits (128MB-3GB), enable sub-100ms MCP server response times, maintain backward compatibility with existing data, and align with project's static-first design philosophy.

## Decision

We will implement a **hierarchical partitioning strategy for Gold layer data** using S3 key structures optimized for common MCP server query patterns: `season/player_id/date` hierarchy with file size optimization for Lambda performance.

## Considered Options

1. **Hierarchical Season/Player/Date Partitioning (The Chosen One):** Multi-level partitioning with season as primary, player_id as secondary, and date as tertiary partition keys.
   * *Pros:* Optimal for player-focused queries ("Show me LeBron's season stats"), enables efficient season-level aggregations, supports time-series analysis, allows Lambda to read only relevant partitions, excellent query pruning capabilities, aligns with NBA data natural hierarchy
   * *Cons:* More complex directory structure, potential for many small files with low-activity players, requires careful file size management

2. **Date-Only Partitioning:** Simple partitioning by game date only.
   * *Pros:* Simple directory structure, predictable file sizes, easy to implement and maintain
   * *Cons:* Poor performance for player-specific queries, requires scanning multiple partitions for player analytics, no optimization for common MCP query patterns

3. **Team-Based Partitioning:** Primary partitioning by team with secondary date partitioning.
   * *Pros:* Good for team-level analytics, manageable number of partitions (30 NBA teams)
   * *Cons:* Poor performance for individual player queries, players change teams during seasons, doesn't align with expected MCP query patterns focused on individual players

4. **Hash-Based Partitioning:** Distribute data using hash functions on player_id.
   * *Pros:* Even data distribution, predictable partition sizes, good for parallel processing
   * *Cons:* No query optimization benefits, requires scanning multiple partitions for any meaningful query, no natural data locality

## Partitioning Strategy Details

### S3 Key Structure
```
s3://hoopstat-haus-gold/
├── player_daily_stats/
│   ├── season=2023-24/
│   │   ├── player_id=2544/      # LeBron James
│   │   │   ├── date=2024-01-15/stats.parquet
│   │   │   ├── date=2024-01-18/stats.parquet
│   │   │   └── season_summary.parquet
│   │   └── player_id=1628983/   # Jayson Tatum
│   │       ├── date=2024-01-15/stats.parquet
│   │       └── season_summary.parquet
│   └── season=2024-25/
├── team_daily_stats/
│   ├── season=2023-24/
│   │   ├── team_id=1610612747/  # Lakers
│   │   └── team_id=1610612738/  # Celtics
└── game_summaries/
    ├── season=2023-24/
    └── date=2024-01-15/
```

### File Size Optimization
- **Target Size:** 10-50MB per Parquet file for optimal Lambda performance
- **Daily Files:** Individual game stats (typically 1-5KB per player per game)
- **Aggregated Files:** Weekly/monthly rollups when daily files become too numerous
- **Season Summaries:** Pre-computed season aggregations (5-20MB per player)

### Query Pattern Optimization

#### Common MCP Server Queries and Optimizations:
1. **"Show me LeBron James' recent performance"**
   - Direct path: `s3://bucket/gold/player_daily_stats/season=2023-24/player_id=2544/`
   - Lambda reads only relevant partition, sub-10ms S3 access

2. **"Compare team offensive ratings this season"**
   - Path: `s3://bucket/gold/team_daily_stats/season=2023-24/*/season_summary.parquet`
   - Parallel reads across team partitions

3. **"Find players with similar performance profiles"**
   - Path: `s3://bucket/gold/player_daily_stats/season=2023-24/*/season_summary.parquet`
   - Pre-computed efficiency metrics in season summaries

4. **"Analyze scoring trends over time"**
   - Time-series access through date partitions within player directories
   - Chronological file organization enables efficient range queries

### Data Models and Compatibility

#### Gold Layer Extensions
```python
class GoldPlayerDailyStats(BaseSilverModel):
    """Gold layer player daily statistics with pre-computed metrics."""
    # Inherit all Silver layer fields
    # Add Gold-specific computed fields
    efficiency_rating: float
    usage_rate: float | None
    true_shooting_percentage: float | None
    partition_key: str  # "season=2023-24/player_id=2544/date=2024-01-15"

class GoldSeasonSummary(BaseSilverModel):
    """Pre-computed season-level aggregations."""
    total_games: int
    averages: dict[str, float]  # Points, rebounds, assists per game
    totals: dict[str, int]      # Season totals
    percentiles: dict[str, float]  # Performance percentiles
    trends: dict[str, float]    # Month-over-month changes
```

#### Backward Compatibility Strategy
- Gold models extend existing Silver models (no breaking changes)
- Maintain Silver layer data formats and schemas
- Gold layer adds computed fields and optimization metadata
- Legacy systems continue reading Silver layer unchanged

## Implementation Strategy

### Phase 1: Core Partitioning Infrastructure
- Partition key generation utilities
- S3 path management classes
- File size monitoring and optimization
- Basic Gold layer data models

### Phase 2: Query Optimization
- Pre-computed aggregation tables
- Season summary generation
- Performance metric calculations
- MCP server integration points

### Phase 3: Monitoring and Optimization
- CloudWatch metrics for partition performance
- Query timing analysis
- File size optimization recommendations
- Cost monitoring for storage and compute

## Consequences

* **Positive:** Significant improvement in MCP server query performance (target sub-100ms), optimal S3 storage costs through intelligent partitioning, Lambda memory efficiency through focused data reads, excellent support for common basketball analytics queries, natural data organization matching NBA season structure, easy debugging and data exploration through intuitive directory structure.
* **Negative:** Increased complexity in ETL jobs requiring partition-aware writes, potential for numerous small files with inactive players, higher operational overhead for partition management, learning curve for developers unfamiliar with hierarchical partitioning strategies.
* **Future Implications:** All Gold layer ETL jobs must implement partition-aware data writing, MCP server must be optimized for partitioned data access patterns, monitoring systems need partition-level observability, storage cost optimization requires ongoing partition size management, schema evolution must consider partition key compatibility.