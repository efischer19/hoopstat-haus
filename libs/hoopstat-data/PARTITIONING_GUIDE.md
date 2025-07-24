# Gold Layer Data Partitioning Strategy

This document explains how to use the Gold layer data partitioning utilities implemented as part of ADR-020.

## Overview

The Gold layer partitioning strategy provides:
- **Hierarchical S3 key structure**: `season/player_id/date` for optimal query performance
- **File size optimization**: Tools for Lambda memory efficiency
- **Query pattern optimization**: Pre-configured patterns for common MCP server queries
- **Health monitoring**: Validation and monitoring utilities

## Quick Start

```python
from hoopstat_data.partitioning import (
    create_player_daily_partition,
    create_player_season_partition,
    QueryPatternOptimizer,
)

# Create partition key for player daily stats
partition_key = create_player_daily_partition(
    season="2023-24",
    player_id="2544",  # LeBron James
    date="2024-01-15"
)

print(partition_key.s3_path)
# Output: s3://hoopstat-haus-gold/player_daily_stats/season=2023-24/player_id=2544/date=2024-01-15/stats.parquet

# Use query pattern optimizer for MCP server queries
partition_key = QueryPatternOptimizer.get_optimal_partition_key(
    "player_recent_stats",
    season="2023-24",
    entity_id="2544",
    date="2024-01-15"
)
```

## Gold Layer Models

### GoldPlayerDailyStats
Extends Silver layer player stats with computed metrics:

```python
from hoopstat_data import GoldPlayerDailyStats

stats = GoldPlayerDailyStats(
    player_id="2544",
    player_name="LeBron James",
    points=28,
    rebounds=8,
    assists=7,
    # Gold-specific fields
    efficiency_rating=1.15,
    true_shooting_percentage=0.625,
    usage_rate=0.28,
    season="2023-24",
    partition_key="season=2023-24/player_id=2544/date=2024-01-15"
)
```

### GoldPlayerSeasonSummary
Pre-computed season aggregations:

```python
from hoopstat_data import GoldPlayerSeasonSummary

summary = GoldPlayerSeasonSummary(
    player_id="2544",
    season="2023-24",
    total_games=70,
    points_per_game=27.8,
    efficiency_rating=1.25,
    scoring_trend=0.05,  # 5% increase over season
)
```

## S3 Key Structure

The partitioning strategy uses a hierarchical structure optimized for common query patterns:

```
s3://hoopstat-haus-gold/
├── player_daily_stats/
│   ├── season=2023-24/
│   │   ├── player_id=2544/      # LeBron James
│   │   │   ├── date=2024-01-15/stats.parquet
│   │   │   ├── date=2024-01-18/stats.parquet
│   │   │   └── season_summary.parquet
│   │   └── player_id=1628983/   # Jayson Tatum
├── team_daily_stats/
│   └── season=2023-24/
│       ├── team_id=1610612747/  # Lakers
│       └── team_id=1610612738/  # Celtics
└── game_summaries/
    └── season=2023-24/
        └── date=2024-01-15/
```

## Query Pattern Optimization

### Common MCP Server Query Patterns

1. **Player Recent Stats**: `"Show me LeBron's recent performance"`
```python
partition_key = QueryPatternOptimizer.get_optimal_partition_key(
    "player_recent_stats",
    season="2023-24",
    entity_id="2544"
)
```

2. **Player Season Summary**: `"Show me LeBron's season stats"`
```python
partition_key = QueryPatternOptimizer.get_optimal_partition_key(
    "player_season_summary",
    season="2023-24",
    entity_id="2544"
)
```

3. **League Comparison**: `"Compare all players this season"`
```python
partition_key = QueryPatternOptimizer.get_optimal_partition_key(
    "league_comparison",
    season="2023-24"
)
```

## File Size Optimization

### Estimate and Optimize File Sizes

```python
from hoopstat_data.partitioning import FileSizeOptimizer

# Estimate file size
estimated_size = FileSizeOptimizer.estimate_parquet_size(
    row_count=1000,
    avg_row_size_bytes=500
)

# Check if file should be split
should_split = FileSizeOptimizer.should_split_file(row_count=100000)

# Get split recommendations
recommendations = FileSizeOptimizer.recommend_split_strategy(
    row_count=100000,
    avg_row_size_bytes=500
)

if recommendations["should_split"]:
    print(f"Recommended splits: {recommendations['recommended_splits']}")
    print(f"Rows per split: {recommendations['rows_per_split']}")
```

## Health Monitoring

### Validate Partition Structure

```python
from hoopstat_data.partitioning import PartitionHealthChecker

# Validate partition follows ADR-020 standards
validation_result = PartitionHealthChecker.validate_partition_structure(partition_key)

if not validation_result["is_valid"]:
    print("Warnings:", validation_result["warnings"])

if validation_result["recommendations"]:
    print("Recommendations:", validation_result["recommendations"])

# Calculate partition hash for change detection
partition_hash = PartitionHealthChecker.calculate_partition_hash(partition_key)
```

## Integration with ETL Jobs

### Example ETL Job Integration

```python
from hoopstat_data import GoldPlayerDailyStats
from hoopstat_data.partitioning import create_player_daily_partition

def process_player_daily_stats(silver_data: dict, season: str, date: str):
    """Transform Silver data to Gold layer with partitioning."""
    
    # Create Gold layer model with computed metrics
    gold_stats = GoldPlayerDailyStats(
        **silver_data,
        efficiency_rating=calculate_efficiency(silver_data),
        true_shooting_percentage=calculate_ts_percentage(silver_data),
        season=season,
    )
    
    # Generate optimal partition key
    partition_key = create_player_daily_partition(
        season=season,
        player_id=gold_stats.player_id,
        date=date
    )
    
    gold_stats.partition_key = partition_key.s3_prefix
    
    return gold_stats, partition_key.s3_path
```

## Performance Considerations

### Target File Sizes
- **Minimum**: 5MB (avoid many small files)
- **Target**: 25MB (optimal for Lambda performance)
- **Maximum**: 50MB (Lambda memory limits)

### Query Optimization
- Use season partitioning for temporal queries
- Use player_id partitioning for individual player analysis
- Use date partitioning for time-series analysis
- Pre-compute season summaries for cross-player comparisons

## Backward Compatibility

The Gold layer models extend existing Silver layer models without breaking changes:

```python
# Existing Silver layer code continues to work
from hoopstat_data import PlayerStats

silver_stats = PlayerStats(
    player_id="2544",
    points=25,
    rebounds=10,
    assists=5,
    steals=2,
    blocks=1,
    turnovers=3
)

# Gold layer adds optional computed fields
from hoopstat_data import GoldPlayerDailyStats

# Can create Gold model with just Silver fields
gold_stats = GoldPlayerDailyStats(
    player_id="2544",
    points=25,
    rebounds=10,
    assists=5,
    steals=2,
    blocks=1,
    turnovers=3
    # Gold fields are optional and will be None
)
```

## Error Handling

### Common Validation Errors

```python
from pydantic import ValidationError

try:
    partition_key = S3PartitionKey(
        bucket="test-bucket",
        partition_type=PartitionType.PLAYER_DAILY,
        season="2023",  # Invalid format
        entity_id="2544"
    )
except ValidationError as e:
    print(f"Validation error: {e}")
```

### Query Pattern Errors

```python
try:
    partition_key = QueryPatternOptimizer.get_optimal_partition_key(
        "unknown_pattern",
        season="2023-24"
    )
except ValueError as e:
    print(f"Unknown query pattern: {e}")
    
    # List available patterns
    patterns = QueryPatternOptimizer.list_query_patterns()
    print("Available patterns:", list(patterns.keys()))
```