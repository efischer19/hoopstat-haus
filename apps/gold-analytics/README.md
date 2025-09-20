# Gold Analytics

Gold layer analytics processing for NBA statistics using S3 Tables and Apache Iceberg format.

## Overview

This application processes Silver layer NBA data and transforms it into advanced analytics metrics stored in S3 Tables using Apache Iceberg format. It implements the Gold layer strategy from [ADR-026](../../meta/adr/ADR-026-s3_tables_gold_layer.md).

## Features

### Analytics Metrics
- **Player Analytics**: True Shooting %, Player Efficiency Rating, Usage Rate, Effective FG%
- **Team Analytics**: Offensive/Defensive Rating, Pace, Net Rating, Four Factors
- **Season Aggregations**: Full season summaries for players and teams
- **S3 Tables Integration**: Optimized storage using Apache Iceberg format

### Apache Iceberg Integration
- **PyIceberg Library**: Full Apache Iceberg support for Lambda environment
- **Optimized Partitioning**: Season/month/team partitioning per ADR-026
- **File Size Optimization**: Target 64-128MB files for query performance 
- **Schema Evolution**: Support for future analytics additions
- **Transaction Support**: Data consistency through Iceberg transactions
- **Automatic Compaction**: S3 Tables handles long-term efficiency
- **Error Handling**: Comprehensive logging for debugging

### Performance Features
- **Memory-Optimized Writes**: Streaming writes for Lambda constraints
- **Chunked Processing**: Large datasets split for optimal file sizes
- **Query Optimization**: Partition pruning for sub-second responses
- **Decimal Precision**: Proper data types for analytics percentages

### Data Flow
```
Silver S3 (JSON) → Gold Lambda → Gold S3 Tables (Iceberg) → MCP Clients
```

## Development

### Prerequisites
- Python 3.12+
- Poetry
- AWS CLI configured

### Setup
```bash
# Install dependencies
poetry install

# Run linting and formatting
poetry run ruff format .
poetry run ruff check .

# Run tests
poetry run pytest
```

### Local Testing
```bash
# Process a specific date (dry run)
poetry run start process --date 2024-01-15 --dry-run

# Process player season aggregation
poetry run start season-players --season 2023-24 --dry-run

# Process team season aggregation
poetry run start season-teams --season 2023-24 --dry-run

# Process specific player or team
poetry run start season-players --season 2023-24 --player-id 2544 --dry-run
poetry run start season-teams --season 2023-24 --team-id 1610612747 --dry-run

# Check status
poetry run start status
```

### Configuration

Environment variables:
- `SILVER_BUCKET`: S3 bucket containing Silver layer data
- `GOLD_BUCKET`: S3 bucket for Gold layer S3 Tables

## Architecture

### S3 Tables Partitioning
Following the strategy from ADR-026:
```
s3://bucket/gold_tables/
├── player_analytics/
│   └── date=YYYY-MM-DD/player_id=*/analytics.parquet
├── player_season_summaries/
│   └── season=YYYY-YY/player_id=*/season_stats.parquet
├── team_analytics/
│   └── date=YYYY-MM-DD/team_id=*/analytics.parquet
└── team_season_summaries/
    └── season=YYYY-YY/team_id=*/season_stats.parquet
```

### Lambda Deployment
```bash
# Build Docker image (from repo root)
docker build -f apps/gold-analytics/Dockerfile -t gold-analytics:dev .

# Deploy via Terraform (see infrastructure/)
```

## MCP Integration

Users can query the Gold analytics data using MCP clients with **no AWS credentials required**:

```json
{
  "mcpServers": {
    "hoopstat-haus-analytics": {
      "command": "uvx",
      "args": ["awslabs.s3-tables-mcp-server@latest", "--allow-read"],
      "env": {
        "AWS_REGION": "us-east-1",
        "S3_TABLES_BUCKET": "hoopstat-haus-gold-tables"
      }
    }
  }
}
```

### Public Access Features
- **Anonymous Read Access**: No AWS credentials needed
- **Real-time Analytics**: Data available 2-4 hours after games
- **Advanced Metrics**: Player efficiency, team ratings, and more
- **Optimized Performance**: Date-partitioned for fast queries

### Example Queries
- "Show me LeBron's efficiency this week"
- "What's the Lakers defensive rating this month?"
- "Top 10 players by True Shooting % yesterday"
- "Compare team offensive ratings for the 2023-24 season"
- "Show home vs away splits for the Warriors"
- "Display Four Factors for playoff teams"

**Setup Guide**: [MCP Client Configuration](../../docs-src/MCP_CLIENT_SETUP.md)

## Related

- [ADR-026: S3 Tables for Gold Layer Analytics](../../meta/adr/ADR-026-s3_tables_gold_layer.md)
- [Silver Processing App](../silver-processing/)