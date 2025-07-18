# Silver to Gold ETL Jobs Implementation Plan

**Status:** Planning  
**Date:** 2025-01-18  
**Author:** AI Contributor  
**Scope:** Define ETL job patterns and implementation strategy for transforming Silver layer data into Gold layer business-ready aggregations

## Executive Summary

This plan defines the implementation strategy for ETL (Extract, Transform, Load) jobs that will transform cleaned and validated Silver layer NBA data into business-ready Gold layer aggregations optimized for MCP server consumption. Building upon the established [Medallion Data Architecture](./medallion-data-architecture.md), this plan focuses specifically on the data transformation workflows that bridge the gap between clean, standardized data and analytics-ready business intelligence.

The implementation leverages serverless AWS infrastructure (Lambda functions orchestrated by EventBridge/Step Functions), follows the project's static-first philosophy, and creates aggregations specifically designed to optimize MCP server response times and data access patterns. The approach emphasizes incremental, cost-effective processing with built-in quality validation and error recovery.

Using player season statistics as our primary example, we'll establish patterns that can be extended to team analytics, game insights, and advanced metrics as the system matures.

## High-Level Implementation Strategy

### Core ETL Job Architecture

The Silver to Gold ETL system will be implemented as a collection of specialized, serverless processing jobs that can run independently or as part of orchestrated workflows. Each job follows a consistent pattern:

1. **Extract:** Read specific partitions of Silver layer Parquet data from S3
2. **Transform:** Apply business logic, aggregations, and calculations using pandas/polars
3. **Load:** Write results to Gold layer with optimized partitioning for MCP queries
4. **Validate:** Perform data quality checks and update processing metadata

### Processing Patterns and Job Types

#### 1. Incremental Aggregation Jobs
**Purpose:** Process new or updated Silver data and incrementally update Gold aggregations
**Pattern:** Event-driven processing triggered by new Silver data arrival
**Example:** Daily player statistics aggregation that updates season-to-date totals

```
Trigger: S3 EventBridge notification (new Silver data)
↓
Lambda: Extract yesterday's player game stats
↓
Transform: Calculate rolling averages, update season totals
↓
Load: Update Gold layer partitioned by player_id/season
↓
Validate: Check data consistency and freshness
```

#### 2. Full Refresh Jobs
**Purpose:** Recalculate complete aggregations when business logic changes
**Pattern:** Scheduled batch processing with parallelization
**Example:** Recalculating advanced metrics like Player Efficiency Rating (PER) across all seasons

```
Schedule: Weekly via EventBridge
↓
Step Function: Orchestrate parallel processing by season
↓
Multiple Lambdas: Process seasons in parallel
↓
Coordinator Lambda: Validate and consolidate results
```

#### 3. Dimensional Lookup Jobs
**Purpose:** Create and maintain reference tables for fast MCP server lookups
**Pattern:** Daily refresh of slowly-changing dimensional data
**Example:** Player roster lookups, team hierarchies, position classifications

```
Schedule: Daily at 2 AM ET
↓
Lambda: Extract current rosters from Silver
↓
Transform: Create lookup mappings and hierarchies
↓
Load: Update Gold dimensional tables
↓
Cache Warm: Pre-populate MCP server caches
```

### Data Transformation Strategies

#### Temporal Aggregations
- **Daily Stats:** Game-by-game performance rolled up by day
- **Rolling Windows:** 5-game, 10-game, 30-game moving averages
- **Season Progressions:** Game 1 through current game cumulative stats
- **Historical Context:** Comparative analysis vs. previous seasons

#### Hierarchical Aggregations
- **Individual → Position → Team → Conference → League**
- **Game → Series → Season → Career**
- **Regular Season vs. Playoffs** differentiation

#### Business-Focused Calculations
- **Advanced Metrics:** PER, Win Shares, Usage Rate, True Shooting %
- **Fantasy Relevance:** Points per game, consistency scores, injury impact
- **MCP Optimization:** Pre-calculated answers to common AI queries

### Technology Stack and Tools

#### Processing Engine Selection
**Primary:** Python with pandas for familiar, maintainable code
**Alternative:** polars for performance-critical large dataset processing
**Rationale:** Aligns with project's Python-first approach while providing flexibility

#### Orchestration Approach
**Primary:** AWS Step Functions for complex, multi-stage workflows
**Secondary:** EventBridge for simple event-driven processing
**Rationale:** Serverless, cost-effective, integrates with existing AWS infrastructure

#### Data Quality Integration
**Validation Framework:** Custom validation library with configurable rules
**Quality Metrics:** Completeness, consistency, timeliness tracking
**Error Handling:** Quarantine invalid results, alert on quality degradation

### MCP Server Optimization Strategy

#### Pre-Computed Query Patterns
Based on expected AI agent query patterns, pre-compute common aggregations:
- "Show me LeBron James' season stats"
- "Compare team offensive ratings"
- "Find players with similar performance profiles"
- "Analyze scoring trends over time"

#### Data Structure Design
**Star Schema:** Fact tables (stats) connected to dimension tables (players, teams, games)
**Partitioning:** By player_id and season for optimal query performance
**Indexing:** JSON metadata includes common search keys
**Caching Keys:** Pre-generate lookup keys for fastest MCP response

### Example Implementation: Player Season Statistics ETL

To illustrate the approach, here's how we'll implement player season statistics aggregation:

#### Input (Silver Layer)
```
s3://hoopstat-haus-silver/game_statistics/season=2023-24/month=01/
├── player_game_stats_2024-01-15.parquet
├── player_game_stats_2024-01-16.parquet
└── ...
```

#### Transformation Logic
1. **Daily Processing:** Extract yesterday's player performances
2. **Season Aggregation:** Update running totals (points, rebounds, assists)
3. **Advanced Metrics:** Calculate efficiency ratings and advanced stats
4. **Context Addition:** Add league rankings, position comparisons
5. **MCP Formatting:** Structure for optimal API response times

#### Output (Gold Layer)
```
s3://hoopstat-haus-gold/player_performance/
├── season_aggregates/season=2023-24/player_id=2544/stats.parquet
├── daily_stats/season=2023-24/month=01/daily_rollup.parquet
└── mcp_datasets/current_season/player_lookup.parquet
```

#### Processing Workflow
1. **Trigger:** EventBridge detects new Silver data (daily at 6 AM ET)
2. **Extract:** Lambda reads previous day's game statistics
3. **Transform:** Python job calculates aggregations and metrics
4. **Load:** Write to partitioned Gold layer with metadata
5. **Validate:** Check data quality and update freshness indicators
6. **Notify:** Update MCP server cache invalidation queue

## Required ADRs

Beyond the ADRs already identified in the Medallion Architecture plan, the following additional decisions are needed specifically for ETL job implementation:

### ADR-023: ETL Job Processing Framework and Orchestration Platform
- **Decision Scope:** Choose between Step Functions, Airflow, or custom orchestration for ETL workflows
- **Key Areas:** Cost effectiveness, complexity management, monitoring and debugging capabilities
- **Impact:** Affects development velocity, operational overhead, and system maintainability
- **Dependencies:** ADR-009 (AWS infrastructure), ADR-007 (GitHub Actions)

### ADR-024: Python Data Processing Library Selection (pandas vs. polars)
- **Decision Scope:** Standardize on data manipulation framework for ETL transformations
- **Key Areas:** Performance characteristics, memory usage, learning curve, ecosystem compatibility
- **Impact:** Affects processing speed, resource costs, and developer productivity
- **Dependencies:** ADR-002 (Python version), ADR-014 (Parquet format)

### ADR-025: ETL Job Error Handling and Recovery Strategy
- **Decision Scope:** Define patterns for job failure handling, retry logic, and partial failure recovery
- **Key Areas:** Data consistency guarantees, alerting mechanisms, manual intervention workflows
- **Impact:** Affects system reliability and operational burden
- **Dependencies:** ADR-015 (JSON logging), monitoring infrastructure

### ADR-026: Gold Layer Partitioning and Storage Optimization for MCP Queries
- **Decision Scope:** Optimize Gold layer data organization for MCP server query patterns
- **Key Areas:** Partitioning schemes, file sizing, caching strategies
- **Impact:** Affects query performance and storage costs for MCP server
- **Dependencies:** MCP server architecture decisions, ADR-014 (Parquet format)

### ADR-027: ETL Job State Management and Idempotency Patterns
- **Decision Scope:** Ensure ETL jobs can be safely re-run and handle partial completions
- **Key Areas:** State tracking, checkpoint mechanisms, duplicate detection
- **Impact:** Affects data consistency and operational simplicity
- **Dependencies:** ADR-018 (data lineage), database/storage choices

### ADR-028: Real-Time vs. Batch Processing Strategy for Gold Layer Updates
- **Decision Scope:** Balance between data freshness and processing costs
- **Key Areas:** Latency requirements, cost optimization, complexity management
- **Impact:** Affects user experience and system costs
- **Dependencies:** MCP server requirements, ADR-020 (orchestration)

## Risks & Open Questions

### High Priority Risks

#### Risk: ETL Job Processing Costs at Scale
- **Description:** As data volume grows, Lambda processing costs and S3 access charges could become prohibitive
- **Impact:** Could make the system financially unsustainable as usage scales
- **Mitigation:** Implement cost monitoring, optimize processing patterns, consider EC2 Spot instances for large batch jobs
- **Timeline:** Critical to address before production deployment

#### Risk: Data Consistency During Incremental Updates
- **Description:** Partial failures in incremental ETL jobs could lead to inconsistent Gold layer data
- **Impact:** Could cause incorrect analytics results and loss of trust in data quality
- **Mitigation:** Implement atomic operations, comprehensive validation, and rollback capabilities
- **Timeline:** Must be resolved in foundational implementation

#### Risk: ETL Job Orchestration Complexity
- **Description:** Complex dependencies between ETL jobs could create maintenance burden and failure cascades  
- **Impact:** Could lead to operational overhead and difficult debugging scenarios
- **Mitigation:** Keep job dependencies minimal, implement clear monitoring, design for independent execution
- **Timeline:** Architecture decision needed before implementation begins

### Medium Priority Risks

#### Risk: Silver to Gold Schema Evolution Management
- **Description:** Changes to Silver layer schemas could break existing ETL transformations
- **Impact:** Could cause processing failures and require manual intervention
- **Mitigation:** Implement schema validation, version detection, backward compatibility patterns
- **Timeline:** Can be addressed incrementally as system matures

#### Risk: Processing Latency vs. Data Freshness Trade-offs
- **Description:** More complex aggregations may require longer processing times, affecting data freshness
- **Impact:** Could impact MCP server response quality for time-sensitive queries
- **Mitigation:** Design tiered processing (fast basic aggregations, slower advanced metrics)
- **Timeline:** Can be optimized iteratively based on usage patterns

#### Risk: ETL Resource Contention and Throttling
- **Description:** Multiple concurrent ETL jobs could overwhelm AWS service limits or S3 request rates
- **Impact:** Could cause job failures and processing delays
- **Mitigation:** Implement job queuing, rate limiting, and resource allocation strategies
- **Timeline:** Monitor and address as processing volume grows

### Open Questions

#### Question: Real-Time Processing Requirements
- **Question:** Should any Gold layer aggregations support near-real-time updates for live games?
- **Impact:** Affects architecture complexity and cost model significantly
- **Investigation Needed:** Analyze MCP server use cases, evaluate streaming vs. batch processing trade-offs
- **Decision Timeline:** Before Phase 2 implementation

#### Question: Cross-Season Historical Analysis Patterns
- **Question:** How should ETL jobs handle historical comparisons and trend analysis across multiple seasons?
- **Impact:** Affects data modeling and processing complexity
- **Investigation Needed:** Analyze common historical query patterns, evaluate processing vs. storage trade-offs
- **Decision Timeline:** Can be deferred to Phase 3 advanced features

#### Question: Data Aggregation Granularity and Pre-computation Strategy
- **Question:** What level of aggregation should be pre-computed vs. calculated on-demand?
- **Impact:** Affects storage costs, query performance, and processing complexity
- **Investigation Needed:** Profile MCP server query patterns, analyze cost/performance trade-offs
- **Decision Timeline:** Refine iteratively based on usage data

#### Question: ETL Job Testing and Quality Assurance Strategy
- **Question:** How should ETL transformations be tested, especially for complex business logic?
- **Impact:** Affects code quality, debugging capability, and confidence in data accuracy
- **Investigation Needed:** Evaluate data testing frameworks, establish quality assurance patterns
- **Decision Timeline:** Must be addressed before first ETL job implementation

#### Question: Integration with External Data Sources
- **Question:** How should ETL jobs handle integration with external data sources (advanced metrics, betting odds, etc.)?
- **Impact:** Affects architecture flexibility and data enrichment capabilities
- **Investigation Needed:** Assess external data value, evaluate integration complexity
- **Decision Timeline:** Future enhancement, not critical for initial implementation

## Phase-Based Implementation Roadmap

### Phase 1: Foundation and Core Infrastructure (Weeks 1-3)

#### Sprint 1.1: ETL Framework Foundation
- Set up Lambda function templates for ETL job patterns
- Implement basic Silver to Gold data transfer with validation
- Create error handling and logging framework
- Establish S3 access patterns and permissions

#### Sprint 1.2: Orchestration Infrastructure
- Configure EventBridge for event-driven ETL triggers
- Implement Step Functions for complex workflow orchestration
- Set up monitoring and alerting for ETL job execution
- Create operational dashboards for ETL health

#### Sprint 1.3: Data Quality Framework
- Implement ETL-specific data validation rules
- Create quality metrics collection and reporting
- Set up automated quality alerting and degradation detection
- Build quarantine and recovery mechanisms for bad data

### Phase 2: Core ETL Jobs Implementation (Weeks 4-6)

#### Sprint 2.1: Player Season Statistics ETL Job
- Implement daily incremental player statistics aggregation
- Create season-to-date cumulative statistics calculation
- Build rolling averages and performance trends
- Add data freshness and completeness validation

#### Sprint 2.2: Advanced Player Metrics ETL Job
- Calculate Player Efficiency Rating (PER) and advanced statistics
- Implement league ranking and percentile calculations
- Create comparative analysis vs. career/position averages
- Add historical context and trend analysis

#### Sprint 2.3: MCP-Optimized Lookup Tables
- Create player and team dimensional lookup tables
- Implement fast search and suggestion capabilities
- Build API-optimized data structures for MCP server
- Set up cache warming and pre-computation strategies

### Phase 3: Extended Analytics and Optimization (Weeks 7-9)

#### Sprint 3.1: Team Analytics ETL Jobs
- Implement team-level statistics aggregation
- Create head-to-head comparison datasets
- Build team ranking and performance trend analysis
- Add team composition and roster change tracking

#### Sprint 3.2: Game-Level Insights ETL Jobs
- Create game summary and key moments analysis
- Implement scoring pattern and momentum detection
- Build game impact and context aggregations
- Add playoff vs. regular season differentiation

#### Sprint 3.3: Performance Optimization and Scaling
- Optimize ETL job performance and resource usage
- Implement intelligent caching and data pre-computation
- Add cost monitoring and optimization recommendations
- Create automated scaling and resource management

### Phase 4: Advanced Features and Integration (Weeks 10-12)

#### Sprint 4.1: Historical Analysis ETL Jobs
- Implement cross-season trend analysis and comparisons
- Create career milestone and achievement tracking
- Build historical context and era-adjusted statistics
- Add injury impact and availability analysis

#### Sprint 4.2: Fantasy and Predictive Analytics
- Create fantasy-relevant statistics and projections
- Implement consistency scores and reliability metrics
- Build matchup analysis and opponent-adjusted stats
- Add injury risk and availability predictions

#### Sprint 4.3: MCP Server Integration Optimization
- Fine-tune Gold layer data structures for MCP queries
- Implement advanced caching strategies for frequent requests
- Add query pattern analysis and optimization recommendations
- Create A/B testing framework for data structure improvements

## 🎯 ACTIONABLE FEATURE REQUESTS

### Phase 1: Foundation Implementation

#### 1. Setup ETL Infrastructure with Lambda and EventBridge
```markdown
**Title:** feat: setup serverless ETL infrastructure for silver to gold transformations

**Description:** 
Create the foundational AWS infrastructure for running ETL jobs that transform Silver layer data into Gold layer aggregations. This includes Lambda functions, EventBridge rules, IAM roles, and basic monitoring.

**Deliverables:**
- Terraform configuration for ETL-specific AWS resources
- Lambda function template with common ETL patterns
- EventBridge rules for triggering ETL jobs based on Silver data updates
- CloudWatch logging and monitoring setup
- IAM roles and policies for secure S3 access

**Acceptance Criteria:**
- [ ] Terraform creates all necessary AWS resources for ETL processing
- [ ] Lambda function template includes error handling and logging
- [ ] EventBridge successfully triggers ETL jobs when new Silver data arrives
- [ ] CloudWatch dashboards show ETL job execution status and performance
- [ ] IAM policies follow least-privilege principles for S3 access
- [ ] All resources tagged appropriately for cost tracking
- [ ] Documentation includes deployment and troubleshooting guides
```

#### 2. Implement Data Quality Validation Framework for ETL Jobs
```markdown
**Title:** feat: create data quality validation framework for ETL transformations

**Description:**
Build a comprehensive data quality validation system that ensures ETL transformations produce accurate, complete, and consistent Gold layer data. Include automated quality checks, alerting, and quarantine mechanisms.

**Deliverables:**
- Python validation library with configurable quality rules
- Quality metrics collection and reporting system
- Automated alerting for quality degradation
- Quarantine system for handling invalid data
- Quality dashboard for operational monitoring

**Acceptance Criteria:**
- [ ] Validation framework supports completeness, accuracy, and consistency checks
- [ ] Quality metrics are tracked and stored for trend analysis
- [ ] Automated alerts trigger when quality thresholds are exceeded
- [ ] Invalid data is quarantined with clear recovery procedures
- [ ] Quality dashboard provides real-time visibility into ETL health
- [ ] Framework is extensible for new quality rules and metrics
- [ ] Documentation includes quality rule configuration guide
```

#### 3. Create Step Functions Workflow for Complex ETL Orchestration
```markdown
**Title:** feat: implement Step Functions orchestration for multi-stage ETL workflows

**Description:**
Design and implement AWS Step Functions workflows that can orchestrate complex, multi-stage ETL processes with proper error handling, retry logic, and dependency management.

**Deliverables:**
- Step Functions state machines for ETL workflow orchestration
- Error handling and retry logic for each processing stage
- Parallel processing patterns for improved performance
- Integration with EventBridge and Lambda functions
- Workflow monitoring and debugging capabilities

**Acceptance Criteria:**
- [ ] Step Functions can orchestrate multi-Lambda ETL workflows
- [ ] Error handling includes appropriate retry logic and failure notifications
- [ ] Parallel processing stages execute efficiently without resource conflicts
- [ ] Workflow execution history is preserved for debugging and auditing
- [ ] Integration with existing EventBridge triggers works seamlessly
- [ ] Workflow costs are optimized through efficient execution patterns
- [ ] Documentation includes workflow design patterns and examples
```

### Phase 2: Core ETL Jobs

#### 4. Build Player Season Statistics Daily Aggregation ETL Job
```markdown
**Title:** feat: implement daily player season statistics aggregation ETL job

**Description:**
Create the core ETL job that processes daily NBA game data from the Silver layer and produces season-to-date player statistics optimized for MCP server consumption. This is the foundational ETL job that establishes patterns for other aggregations.

**Deliverables:**
- Lambda function for daily player statistics processing
- Season-to-date aggregation logic with rolling averages
- Incremental processing to handle new game data efficiently
- Gold layer output optimized for MCP server queries
- Comprehensive testing and validation

**Acceptance Criteria:**
- [ ] ETL job processes previous day's player game statistics
- [ ] Season aggregates include points, rebounds, assists, and shooting percentages
- [ ] Rolling averages calculated for 5-game, 10-game, and 30-game windows
- [ ] Incremental processing updates only affected player records
- [ ] Output data is partitioned optimally for MCP server access patterns
- [ ] Data quality validation ensures statistical accuracy
- [ ] Job runs within cost and performance targets (<$1 per day, <10 minutes runtime)
```

#### 5. Implement Advanced Player Metrics Calculation ETL Job
```markdown
**Title:** feat: create advanced basketball metrics calculation ETL job

**Description:**
Build ETL job that calculates advanced basketball analytics like Player Efficiency Rating (PER), True Shooting Percentage, Usage Rate, and other sophisticated metrics that provide deeper insights into player performance.

**Deliverables:**
- Advanced metrics calculation library with NBA-standard formulas
- ETL job for processing and updating advanced statistics
- League-wide context and ranking calculations
- Historical trend analysis and career comparisons
- MCP-optimized output formatting

**Acceptance Criteria:**
- [ ] Accurately calculates PER, TS%, Usage Rate, and Win Shares
- [ ] Provides league rankings and percentile scores for each metric
- [ ] Includes historical comparisons and career trend analysis
- [ ] Output includes confidence intervals and data quality indicators
- [ ] Calculations match published NBA advanced statistics where available
- [ ] Processing efficiently handles full season recalculations
- [ ] Documentation explains each metric calculation and interpretation
```

#### 6. Create MCP-Optimized Player and Team Lookup Tables
```markdown
**Title:** feat: build dimensional lookup tables optimized for MCP server queries

**Description:**
Create and maintain reference tables that enable fast lookups for common MCP server queries. These tables should support fuzzy matching, autocomplete, and rapid data retrieval for AI agents.

**Deliverables:**
- Player lookup table with names, IDs, and current team information
- Team lookup table with hierarchies and historical information
- Position and role classification systems
- Fuzzy matching and search optimization
- Cache warming strategies for MCP server

**Acceptance Criteria:**
- [ ] Player lookup supports fuzzy name matching with 95%+ accuracy
- [ ] Team lookup includes current rosters and historical affiliations
- [ ] Position classifications include primary and secondary positions
- [ ] Lookup tables update daily with roster changes and trades
- [ ] Query response times under 100ms for common lookups
- [ ] Integration with MCP server caching systems
- [ ] Support for autocomplete and suggestion features
```

### Phase 3: Extended Analytics

#### 7. Implement Team Analytics Aggregation ETL Jobs
```markdown
**Title:** feat: create team-level analytics and comparison ETL jobs

**Description:**
Build ETL jobs that aggregate individual player statistics into team-level metrics, create head-to-head comparisons, and generate team performance analytics optimized for strategic analysis.

**Deliverables:**
- Team offensive and defensive rating calculations
- Head-to-head matchup analysis and historical records
- Team composition analysis and roster strength metrics
- Conference and division standings automation
- Playoff probability and strength-of-schedule calculations

**Acceptance Criteria:**
- [ ] Team ratings accurately reflect offensive and defensive efficiency
- [ ] Head-to-head records include regular season and playoff distinctions
- [ ] Roster strength metrics account for player availability and performance
- [ ] Standings calculations match official NBA standings
- [ ] Analytics update nightly during season and weekly in off-season
- [ ] Output optimized for comparative analysis queries
- [ ] Historical data preserved for multi-season trend analysis
```

#### 8. Build Game-Level Insights and Momentum Analysis ETL Jobs
```markdown
**Title:** feat: implement game analysis and key moments detection ETL jobs

**Description:**
Create ETL jobs that analyze individual games to extract insights about scoring patterns, momentum shifts, clutch performance, and other game-specific analytics that provide context for player and team performance.

**Deliverables:**
- Game flow and momentum detection algorithms
- Clutch performance and high-leverage situation analysis
- Scoring pattern and pace analysis
- Key moment identification and impact measurement
- Game context and significance scoring

**Acceptance Criteria:**
- [ ] Momentum detection identifies scoring runs and lead changes
- [ ] Clutch statistics calculated for final 5 minutes of close games
- [ ] Pace analysis tracks possessions and efficiency trends
- [ ] Key moments identified with statistical significance scoring
- [ ] Game context includes playoff implications and rivalry factors
- [ ] Analysis produces actionable insights for AI agents
- [ ] Processing completes within 1 hour of official game completion
```

### Phase 4: Advanced Features

#### 9. Create Historical Analysis and Career Milestone Tracking ETL Jobs
```markdown
**Title:** feat: implement cross-season analysis and career milestone tracking

**Description:**
Build ETL jobs that perform historical analysis across multiple seasons, track career milestones and achievements, and create era-adjusted statistics for fair historical comparisons.

**Deliverables:**
- Cross-season trend analysis and career trajectory modeling
- Milestone tracking for records, achievements, and career marks
- Era adjustment calculations for historical fair comparisons
- Career phase detection and performance decline analysis
- Hall of Fame probability and legacy metrics

**Acceptance Criteria:**
- [ ] Historical comparisons account for rule changes and era differences
- [ ] Milestone tracking includes both official and unofficial achievements
- [ ] Career trajectory modeling predicts future performance trends
- [ ] Era adjustments enable fair comparison across different time periods
- [ ] Legacy metrics provide objective career value assessment
- [ ] Analysis supports "greatest of all time" discussions with data
- [ ] Processing handles full NBA history efficiently
```

#### 10. Implement Fantasy Analytics and Predictive Modeling ETL Jobs
```markdown
**Title:** feat: create fantasy-relevant analytics and performance prediction ETL jobs

**Description:**
Build specialized ETL jobs that create fantasy basketball relevant statistics, consistency metrics, and predictive models that help assess player value and reliability for fantasy applications.

**Deliverables:**
- Fantasy points calculation across major platforms (ESPN, Yahoo, DraftKings)
- Consistency and reliability scoring systems
- Matchup-specific performance predictions
- Injury risk assessment and availability predictions
- Value-based rankings and sleeper identification

**Acceptance Criteria:**
- [ ] Fantasy points calculated accurately for all major platforms
- [ ] Consistency scores predict week-to-week reliability effectively
- [ ] Matchup analysis accounts for opponent defensive strength
- [ ] Injury predictions show statistical correlation with actual injuries
- [ ] Value rankings identify undervalued and overvalued players
- [ ] Predictions updated daily with 7-day forward-looking analysis
- [ ] Integration supports both season-long and daily fantasy applications
```

---

## Implementation Success Criteria

This Silver to Gold ETL implementation is considered successful when it meets these measurable outcomes:

### Technical Success Criteria
1. **Processing Performance:** Daily ETL jobs complete within 2 hours of data availability
2. **Data Quality:** 99.9% accuracy compared to manual calculations for all metrics
3. **Cost Efficiency:** Total ETL processing costs under $50/month at moderate data volumes
4. **Reliability:** 99.5% successful job completion rate with automated error recovery

### Business Success Criteria
1. **MCP Server Integration:** Gold layer data powers sub-second MCP server responses
2. **Data Freshness:** Player statistics available within 4 hours of game completion
3. **Analytics Value:** Advanced metrics provide insights not available elsewhere
4. **Scalability:** System handles full NBA season processing without manual intervention

### Operational Success Criteria
1. **Monitoring Coverage:** All ETL jobs have comprehensive monitoring and alerting
2. **Debugging Capability:** Issues can be diagnosed and resolved within 2 hours
3. **Extensibility:** New aggregations can be added with <1 week development time
4. **Documentation Quality:** New developers can understand and extend ETL jobs within 3 days

---

**Implementation Timeline Estimate:** 12 weeks total
- Phase 1 (Foundation): 3 weeks
- Phase 2 (Core ETL): 3 weeks  
- Phase 3 (Extended Analytics): 3 weeks
- Phase 4 (Advanced Features): 3 weeks

**Dependencies:**
- Silver layer data availability and schema stability
- AWS infrastructure from medallion architecture implementation
- MCP server requirements and query pattern analysis
- ADR approvals for ETL framework and processing decisions

*This plan builds upon the [Medallion Data Architecture](./medallion-data-architecture.md) and aligns with [MCP Server Architecture](./mcp-server-architecture.md) requirements, ensuring end-to-end data pipeline coherence.*