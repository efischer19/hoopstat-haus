# ADR-026: S3 Tables for Gold Layer Analytics

## Status
Superseded

superseded_by: "ADR-027"

supersedes: "ADR-025"

We need to implement a Gold layer analytics system that serves both fantasy basketball use cases and general NBA analysis. This decision originally superseded ADR-025 (JSON Storage for MVP) after evaluating S3 Tables vs Regular S3 + Custom MCP Server approaches. As of ADR-027, this decision has been superseded in favor of a stateless, JSON-artifact serving approach optimized for public, low-cost consumption.

### Current State
- Bronze layer: Raw NBA data stored in S3 JSON format
- Silver layer: Cleaned/validated data with Lambda processing
- Gold layer: Planned analytics storage requiring MCP integration

### Key Requirements
- Fantasy basketball metrics: True Shooting %, Player Efficiency Rating, Usage Rate
- Team analytics: Offensive/Defensive Rating, Pace, Net Rating  
- Natural language query support for MCP clients
- Cost-effective architecture for hobby project scale ($20-50/year budget)
- High query performance for interactive analysis

### Cost Analysis (With Actual S3 Tables Pricing)

**S3 Tables Cost for Basketball Analytics Scale (5GB, ~3K requests/month):**
- Storage (5GB): $0.13/month
- Object monitoring: $0.01/month  
- PUT requests: $0.02/month
- GET requests: $0.002/month
- Compaction: $0.03/month
- **Total: ~$0.19/month = $2.28/year**

**Regular S3 Cost:**
- Storage + requests: ~$0.14/month = $1.68/year

**Cost difference: Only $0.60/year** - negligible for hobby project budget

## Decision

**Use S3 Tables with Apache Iceberg format for Gold layer analytics**

### Architecture Components:
1. **Gold Processing**: Lambda function processes Silver → Gold analytics calculations
2. **Gold Storage**: S3 Tables using Apache Iceberg format with MCP-optimized partitioning
3. **Query Interface**: AWS MCP Server provides direct S3 Tables access to MCP clients
4. **Client Registration**: MCP clients configure our S3 Tables bucket as data source

### Data Flow:
```
Bronze S3 (JSON) → Silver Lambda → Gold S3 Tables (Iceberg) → AWS MCP Server → MCP Clients
```

### Partitioning Strategy:
```
s3://bucket/gold_tables/
├── player_analytics/
│   └── date=YYYY-MM-DD/player_id=*/analytics.parquet
└── team_analytics/
    └── date=YYYY-MM-DD/team_id=*/analytics.parquet
```

## Rationale

### Primary Benefits:
1. **Learning opportunity**: Apache Iceberg is industry standard for analytics workloads
2. **Zero infrastructure maintenance**: No custom MCP server deployment or scaling
3. **AWS-native performance**: Leverage optimized S3 Tables + PyIceberg query engine  
4. **Future migration flexibility**: Can easily add custom MCP server reading Iceberg later
5. **Professional skill development**: Iceberg experience valuable for data engineering

### Cost Justification:
- **Minimal cost difference**: $0.60/year vs Regular S3 (within hobby project budget)
- **Performance benefits**: 3x faster queries via automatic compaction
- **Reduced development time**: No custom server code to write, test, and maintain

### Migration Strategy:
- **Two-way door decision**: Can migrate back to custom MCP server reading Iceberg tables
- **Future custom MCP**: Simpler than JSON-based approach (direct PyIceberg queries)
- **Data preservation**: All analytics data remains in optimized Iceberg format

## Consequences

### Positive
- **Zero server maintenance**: No custom MCP server deployment, scaling, or monitoring
- **AWS-native performance**: Leverage optimized S3 Tables query engine (PyIceberg/Daft)
- **Industry standard format**: Learn Apache Iceberg for analytics workloads
- **Natural language queries**: Users can ask "Lakers defensive rating this month?" directly
- **Automatic optimization**: S3 Tables handles compaction, schema evolution, performance tuning
- **Future flexibility**: Easy to add custom MCP server later if needed

### Negative
- **New technology learning curve**: Team needs to understand Apache Iceberg format
- **AWS service dependency**: More tightly coupled to AWS S3 Tables service
- **Data format shift**: Move from JSON to Parquet+metadata (breaking ADR-020)

### Neutral
- **Data model adaptation**: Minimal changes needed to existing Gold models
- **Client configuration**: MCP clients need to configure S3 Tables bucket access
- **Backup strategy**: S3 Tables backup patterns differ from standard S3 objects

## Implementation Notes

### Data Model Changes
Existing Gold models need minimal adaptation:
```python
class GoldPlayerDailyStats(BaseGoldModel):
    # Same fields as before
    def to_iceberg_record(self) -> dict:
        return self.model_dump()
```

### MCP Client Registration
```json
{
  "mcpServers": {
    "hoopstat-haus-analytics": {
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

### Query Examples
- "Show me LeBron's efficiency this week" → filters by player_id + date range
- "What's the Lakers defensive rating this month?" → filters by team_id + date range
- "Top 10 players by TS% yesterday" → scans single date partition with ranking

## References
- [AWS Blog: Implementing conversational AI for S3 Tables using MCP](https://aws.amazon.com/blogs/storage/implementing-conversational-ai-for-s3-tables-using-model-context-protocol-mcp/)
- [AWS S3 Tables Pricing](https://aws.amazon.com/s3/pricing/#S3_Tables)
- [Apache Iceberg Documentation](https://iceberg.apache.org/docs/latest/)
- [PyIceberg Documentation](https://py.iceberg.apache.org/)

## Implementation Notes

### MCP Client Registration
Clients register our Gold S3 Tables bucket using configuration:
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

### Query Examples
- "Show me LeBron's efficiency this week" → filters by player_id + date range
- "What's the Lakers defensive rating this month?" → filters by team_id + date range
- "Top 10 players by TS% yesterday" → scans single date partition with ranking

### Migration Strategy
1. Implement Gold Lambda processor for analytics calculations
2. Create S3 Tables bucket with optimized partitioning
3. Update infrastructure to support S3 Tables IAM permissions
4. Test MCP client configuration with sample data
5. Document client setup instructions for users

## References
- [AWS Blog: Implementing conversational AI for S3 Tables using MCP](https://aws.amazon.com/blogs/storage/implementing-conversational-ai-for-s3-tables-using-model-context-protocol-mcp/)
- [AWS MCP Servers GitHub](https://awslabs.github.io/mcp/)
- [S3 Tables Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-tables.html)
- [Apache Iceberg Documentation](https://iceberg.apache.org/docs/latest/)
