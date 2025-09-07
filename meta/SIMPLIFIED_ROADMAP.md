# Simplified Roadmap: Pre-v1.0 Focus

**Last Updated:** September 7, 2025  
**Status:** Draft - Pre-v1.0 Scope Reduction

## Vision Statement

Build a focused NBA analytics platform that ingests daily basketball data, processes it through a medallion architecture, and serves insights via Model Context Protocol (MCP) to AI assistants.

## Core Value Proposition

**Problem:** NBA data is scattered, requires manual analysis, and isn't easily accessible to AI assistants for basketball insights.

**Solution:** Automated daily data pipeline that creates clean, queryable basketball datasets accessible via MCP protocol.

## Simplified Architecture

```
NBA API → Bronze (Raw JSON) → Silver (Clean/Validated) → Gold (Analytics) → MCP Server → AI Assistants
```

## Pre-v1.0 Roadmap

### Phase 1: Foundation (MVP) - Target: 2-4 weeks
**Goal:** Prove the core data flow works end-to-end

1. **Bronze Layer - Daily Box Score Ingestion**
   - Switch from play-by-play to box score data (simpler, smaller)
   - Store as JSON in S3 (avoid Parquet complexity for now)
   - Daily GitHub Actions workflow for automated ingestion
   - Basic error handling and logging

2. **Silver Layer - Data Cleaning**
   - Validate JSON schema with Pydantic
   - Basic data cleaning (null handling, type conversion)
   - Simple aggregations (team totals, player season stats)
   - Store cleaned data as JSON

3. **Gold Layer - Basic Analytics**
   - Player season statistics
   - Team performance metrics
   - Simple derived metrics (shooting percentages, efficiency)

4. **MCP Server - Minimal Viable Interface**
   - Single endpoint: get player stats
   - Query by player name and date range
   - Return JSON response suitable for AI consumption
   - Consider adding extremely simple "all box scores for date X" endpoint as well, if it doesn't increase scope too much

### Phase 2: Enhanced Analytics - Target: 4-6 weeks post-MVP
**Goal:** Add more sophisticated basketball insights

1. **Expanded Gold Layer**
   - Advanced player metrics (PER, usage rate, etc.)
   - Team chemistry analysis
   - Head-to-head comparisons

2. **Enhanced MCP Server**
   - Multiple query types (player, team, matchup analysis)
   - Historical trend analysis
   - Performance prediction capabilities

### Phase 3: AI Integration - Target: Future (post-v1.0)
**Goal:** Complete the user experience

1. **Frontend Interface**
   - Simple web interface
   - Amazon Bedrock integration
   - Natural language basketball queries

## Key Simplifications from Original Scope

### What We're Cutting (For Now)
- **Play-by-play data**: Too complex, too large for initial version
- **Parquet storage**: JSON is simpler for early development

### What We're Keeping
- **Medallion architecture**: Proven pattern, keeps data organized
- **Shared libraries**: Code reuse is valuable even at smaller scale
- **Docker containers**: Deployment consistency matters
- **GitHub Actions CI/CD**: Automation prevents tech debt
- **ADR documentation**: Decisions need to be tracked
- **MCP protocol**: This is our key differentiator

## Success Metrics for MVP

1. **Data Pipeline Health**
   - Daily ingestion runs successfully
   - Data quality validation passes
   - Pipeline completion time < 30 minutes

2. **MCP Server Functionality**
   - Responds to player stat queries in < 2 seconds
   - Returns accurate data for current NBA season
   - Handles common error cases gracefully

3. **Development Velocity**
   - New features can be added without breaking existing functionality
   - Local development environment works consistently
   - CI/CD pipeline prevents regressions

## Technical Constraints

- **Budget**: Minimize AWS costs =
- **Complexity**: Prefer simple solutions over optimized ones
- **Maintenance**: Each component should be understandable by a single developer
- **AI-Friendly**: Code and data formats should be easily consumed by AI assistants

## Migration Strategy

This roadmap represents a significant scope reduction from the current 150+ GitHub issues. We will:

1. Archive/close 80-90% of existing issues
2. Create new focused issues aligned with this roadmap
3. Update existing documentation to reflect simplified scope
4. Preserve architectural decisions (ADRs) that remain relevant

## Next Actions

1. Review and iterate on this roadmap document
2. Create GitHub issue cleanup commands
3. Draft 5-10 focused issues for Phase 1 implementation
4. Update project documentation for consistency
5. Begin Phase 1 development with bronze layer simplification
