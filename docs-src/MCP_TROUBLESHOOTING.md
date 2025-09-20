# MCP Connection Troubleshooting Guide

This guide helps you resolve common issues when connecting to Hoopstat Haus basketball analytics data via MCP.

## Quick Diagnostics

### Check Your Configuration

1. **Verify MCP Server Configuration**
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

2. **Test AWS S3 Tables MCP Server Installation**
   ```bash
   # Check if uvx is installed
   uvx --version
   
   # Test the S3 Tables MCP server
   uvx awslabs.s3-tables-mcp-server@latest --help
   ```

3. **Verify Environment Variables**
   - `AWS_REGION` must be exactly `us-east-1`
   - `S3_TABLES_BUCKET` must be exactly `hoopstat-haus-gold-tables`
   - No AWS credentials are needed (data is publicly accessible)

## Common Error Messages

### "Connection failed" or "Server not responding"

**Possible Causes:**
- Internet connectivity issues
- MCP server not properly installed
- Incorrect configuration

**Solutions:**
1. Check internet connectivity:
   ```bash
   ping aws.amazon.com
   ```

2. Reinstall the MCP server:
   ```bash
   uvx uninstall awslabs.s3-tables-mcp-server
   uvx install awslabs.s3-tables-mcp-server@latest
   ```

3. Restart your MCP client completely

4. Check for typos in the configuration (especially bucket name and region)

### "Permission denied" or "Access denied"

**Possible Causes:**
- Incorrect AWS region
- Wrong bucket name
- Client trying to perform write operations

**Solutions:**
1. Double-check the region is `us-east-1`
2. Verify bucket name is `hoopstat-haus-gold-tables`
3. Ensure `--allow-read` flag is present in the args
4. Make sure no AWS credentials are set that might interfere

### "No data found" or Empty Results

**Possible Causes:**
- Query targeting very recent games (data latency)
- Invalid player/team names or IDs
- Querying outside available date range

**Solutions:**
1. Try queries for data from 2-3 days ago
2. Use common player names: "LeBron James", "Stephen Curry", etc.
3. Query for the 2023-24 season onwards
4. Try simpler queries first:
   ```
   "Show me all available tables"
   "What data do you have for the Lakers?"
   ```

### "Query timeout" or Slow Performance

**Possible Causes:**
- Large queries without date filtering
- Network latency
- Unoptimized query patterns

**Solutions:**
1. Add date ranges to your queries:
   ```
   "Show me Lakers stats from the last week"
   "Player stats from January 2024"
   ```

2. Avoid season-wide aggregations without filters
3. Use specific player/team names rather than open-ended queries

## Client-Specific Issues

### Claude Desktop

**Issue: MCP server not appearing in client**
1. Completely quit Claude Desktop (check system tray)
2. Update configuration file
3. Restart Claude Desktop
4. Look for 🏀 basketball icon in the UI

**Issue: Configuration file location**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Other MCP Clients

**General troubleshooting:**
1. Check client documentation for MCP server configuration format
2. Verify the client supports the MCP protocol version used by the S3 Tables server
3. Check client logs for specific error messages

## Advanced Diagnostics

### Manual Testing

Test the S3 Tables connection directly:

```bash
# Test basic connectivity (requires AWS CLI)
aws s3tables list-table-buckets --region us-east-1

# Test specific bucket access
aws s3tables list-tables --table-bucket-arn arn:aws:s3tables:us-east-1:ACCOUNT:bucket/hoopstat-haus-gold-tables --region us-east-1
```

### Network Issues

**Corporate Firewalls:**
- The MCP server needs outbound HTTPS access to AWS services
- Port 443 must be open for AWS API calls
- Some corporate networks block or proxy AWS traffic

**VPN/Proxy Issues:**
- Try connecting without VPN
- Check if proxy settings affect AWS connectivity
- Some VPNs have issues with AWS regions

### Log Analysis

**Enable detailed logging:**
1. Most MCP clients have debug/verbose modes
2. Check client documentation for log file locations
3. Look for specific error messages in logs

**Common log patterns:**
- `Connection refused`: Network connectivity issue
- `Access denied`: Permission/configuration problem
- `Region not found`: Incorrect AWS region setting
- `Bucket not found`: Wrong bucket name

## Performance Optimization

### Query Best Practices

1. **Use date filters:**
   ```
   ✅ "Lakers stats from last week"
   ❌ "All Lakers stats ever"
   ```

2. **Be specific:**
   ```
   ✅ "LeBron James efficiency this season"
   ❌ "All player efficiency ratings"
   ```

3. **Avoid cross-season aggregations:**
   ```
   ✅ "Top scorers in 2023-24 season"
   ❌ "Top scorers across all seasons"
   ```

### Expected Performance

| Query Type | Expected Response Time |
|------------|----------------------|
| Single player, recent date | 1-3 seconds |
| Team stats, last month | 2-5 seconds |
| League leaders, current season | 5-10 seconds |
| Historical comparisons | 10-30 seconds |

## Data Availability

### Current Coverage
- **Seasons**: 2023-24 onwards
- **Data Types**: Player and team analytics
- **Update Frequency**: Daily, 2-4 hours after games
- **Partitioning**: By date for optimal performance

### Known Limitations
- No real-time data (2-4 hour delay)
- Limited to basic and advanced analytics (no play-by-play)
- English language queries work best
- Some very recent expansion team data may be limited

## Getting Additional Help

### Before Asking for Help

1. Check this troubleshooting guide
2. Review the [MCP Client Setup Guide](MCP_CLIENT_SETUP.md)
3. Search [existing GitHub issues](https://github.com/efischer19/hoopstat-haus/issues)

### When Filing an Issue

Include:
- **MCP Client**: Name and version
- **Operating System**: OS and version
- **Error Message**: Exact text of any errors
- **Configuration**: Your MCP server config (sanitized)
- **Query**: The specific query that failed
- **Expected vs Actual**: What you expected vs what happened

### Contact Methods

1. **GitHub Issues**: [Create a new issue](https://github.com/efischer19/hoopstat-haus/issues/new)
2. **Discussions**: [Community forum](https://github.com/efischer19/hoopstat-haus/discussions)

---

**Still stuck?** The basketball analytics community is here to help! 🏀