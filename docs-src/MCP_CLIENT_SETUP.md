# [Moved to Future Plans] MCP Client Setup Guide

> This guide is MCP-first and out of initial scope per ADR-027. It has been moved under meta/plans/future/ for later reference.

This guide shows you how to access Hoopstat Haus basketball analytics data using the AWS S3 Tables MCP Server.

## Overview

Hoopstat Haus provides public read access to our Gold layer basketball analytics data through AWS S3 Tables. You can query this data using any MCP-compatible AI assistant by configuring the AWS S3 Tables MCP Server locally.

**No AWS credentials required** - our data is publicly accessible for read operations.

## Quick Start

### 1. Install the AWS S3 Tables MCP Server

```bash
# Install using uvx (recommended)
uvx install awslabs.s3-tables-mcp-server@latest

# Or install using pip
pip install awslabs.s3-tables-mcp-server
```

### 2. Configure Your MCP Client

Add the following configuration to your MCP client (e.g., Claude Desktop):

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

### 3. Start Querying

You can now ask your AI assistant basketball analytics questions like:
- "Show me LeBron's efficiency this week"
- "What's the Lakers defensive rating this month?"
- "Top 10 players by True Shooting % yesterday"
- "Compare team offensive ratings for the 2023-24 season"

## Configuration Details

### Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `AWS_REGION` | `us-east-1` | AWS region where our S3 Tables are hosted |
| `S3_TABLES_BUCKET` | `hoopstat-haus-gold-tables` | Our public S3 Tables bucket name |

### Data Schema

Our analytics data includes two main tables:

#### Player Analytics (`player_analytics`)
- `player_id` (int): NBA player identifier
- `game_date` (date): Date of the game
- `season` (string): NBA season (e.g., "2023-24")
- `team_id` (int): Team identifier
- `points`, `rebounds`, `assists` (int): Basic stats
- `true_shooting_pct` (double): True Shooting percentage
- `player_efficiency_rating` (double): PER rating
- `usage_rate` (double): Usage rate percentage
- `effective_field_goal_pct` (double): eFG%
- `defensive_rating`, `offensive_rating` (double): Advanced ratings

#### Team Analytics (`team_analytics`)
- `team_id` (int): Team identifier
- `game_date` (date): Date of the game
- `season` (string): NBA season
- `offensive_rating`, `defensive_rating` (double): Team ratings
- `net_rating` (double): Net rating (ORtg - DRtg)
- `pace` (double): Pace of play
- `effective_field_goal_pct` (double): Team eFG%
- `true_shooting_pct` (double): Team TS%
- `turnover_rate`, `rebound_rate` (double): Team rates

## Client-Specific Setup

### Claude Desktop

1. Open Claude Desktop settings
2. Navigate to "Developer" tab
3. Add the MCP server configuration above
4. Restart Claude Desktop
5. Look for the "🏀" indicator showing the basketball analytics server is connected

### Other MCP Clients

The configuration pattern is similar for other MCP-compatible clients. Refer to your specific client's documentation for MCP server setup instructions.

## Data Updates

- **Frequency**: Daily updates after games complete
- **Latency**: Data typically available within 2-4 hours after game completion
- **Retention**: Full historical data available from 2023-24 season onwards

## Example Queries

Here are some example queries you can try:

### Player Performance
```
"Show me Stephen Curry's shooting efficiency over the last 10 games"
"Who has the highest Player Efficiency Rating this season?"
"Compare LeBron James and Kevin Durant's advanced stats"
```

### Team Analysis
```
"What teams have the best defensive rating this month?"
"Show me the Boston Celtics' offensive trends this season"
"Which teams play at the fastest pace?"
```

### Historical Comparisons
```
"How do this season's MVP candidates compare statistically?"
"Show me playoff teams' Four Factors rankings"
"Compare home vs away performance for the Warriors"
```

## Troubleshooting

### Common Issues

#### "Connection failed" or "Server not found"
- Verify you have internet connectivity
- Check that the AWS region is correctly set to `us-east-1`
- Ensure the bucket name is exactly `hoopstat-haus-gold-tables`

#### "Permission denied" errors
- Our data is publicly accessible, so this usually indicates a configuration issue
- Double-check the environment variables in your MCP configuration
- Try restarting your MCP client

#### "No data returned" for recent games
- Game data may take 2-4 hours to process after completion
- Check if the game actually finished (not postponed/cancelled)
- Historical data should always be available

#### Slow query performance
- Our data is partitioned by date - queries filtering by recent dates are fastest
- Avoid queries that scan entire seasons without date filters
- Player-specific queries are optimized and should be fast

### Getting Help

If you encounter issues:

1. Check our [GitHub Issues](https://github.com/efischer19/hoopstat-haus/issues) for known problems
2. Review the [AWS S3 Tables MCP Server documentation](https://github.com/awslabs/s3-tables-mcp-server)
3. File a new issue with:
   - Your MCP client type and version
   - The exact error message
   - The query you were trying to run

## Privacy and Usage

- **Public Data**: All analytics data is derived from publicly available NBA statistics
- **No Personal Data**: We don't store or track personal information
- **Rate Limiting**: None currently, but may be implemented if usage grows significantly
- **Cost**: Free for all users

## Technical Details

- **Storage Format**: Apache Iceberg tables on AWS S3 Tables
- **Partitioning**: Data is partitioned by date for optimal query performance
- **Updates**: Automated daily pipeline processes fresh game data
- **Architecture**: See [ADR-026](../meta/adr/ADR-026-s3_tables_gold_layer.md) for technical details

---

**Questions?** Check our [FAQ](FAQ.md) or [open an issue](https://github.com/efischer19/hoopstat-haus/issues/new).