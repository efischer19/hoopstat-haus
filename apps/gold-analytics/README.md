# Gold Analytics

Gold layer analytics processing for NBA statistics using S3 Tables and Apache Iceberg format.

## Overview

This application processes Silver layer NBA data and transforms it into advanced analytics metrics stored in S3 Tables using Apache Iceberg format. It implements the Gold layer strategy from [ADR-026](../../meta/adr/ADR-026-s3_tables_gold_layer.md).

## Features

### Analytics Metrics
- **Player Analytics**: True Shooting %, Player Efficiency Rating, Usage Rate
- **Team Analytics**: Offensive/Defensive Rating, Pace, Net Rating
- **S3 Tables Integration**: Optimized storage using Apache Iceberg format

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
└── team_analytics/
    └── date=YYYY-MM-DD/team_id=*/analytics.parquet
```

### Lambda Deployment
```bash
# Build Docker image (from repo root)
docker build -f apps/gold-analytics/Dockerfile -t gold-analytics:dev .

# Deploy via Terraform (see infrastructure/)
```

## MCP Integration

Users can query the Gold analytics data using MCP clients:

```json
{
  "mcpServers": {
    "hoopstat-haus-gold": {
      "command": "uvx",
      "args": ["awslabs.s3-tables-mcp-server@latest", "--allow-read"],
      "env": {
        "AWS_PROFILE": "hoopstat-profile",
        "AWS_REGION": "us-east-1",
        "S3_TABLES_BUCKET": "hoopstat-haus-gold-tables"
      }
    }
  }
}
```

### Example Queries
- "Show me LeBron's efficiency this week"
- "What's the Lakers defensive rating this month?"
- "Top 10 players by True Shooting % yesterday"

## Related

- [ADR-026: S3 Tables for Gold Layer Analytics](../../meta/adr/ADR-026-s3_tables_gold_layer.md)
- [Silver Processing App](../silver-processing/)