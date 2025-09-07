# Bronze Layer Ingestion: Daily Data Refresh Pipeline

> **⚠️ SUPERSEDED:** This plan has been replaced by `bronze-layer-ingestion-simplified.md` as part of the September 2025 scope reduction. The original comprehensive approach below is preserved for reference but not currently being implemented.

## Executive Summary

This plan defines the implementation strategy for a daily data ingestion pipeline that refreshes the Bronze layer of our Medallion Architecture with fresh NBA statistics. The pipeline will run automatically at 4-5 AM ET daily to ensure all previous day's games are completed and data is available, providing the foundation for fresh stats every day.

Building on our established architectural decisions (ADR-013 NBA API data source, ADR-014 Parquet storage format), this implementation focuses specifically on the operational aspects of reliable, scheduled data ingestion into the Bronze layer as defined in our existing [Medallion Data Architecture plan](./medallion-data-architecture.md).

The pipeline will be designed as a containerized Python application following our monorepo patterns, with comprehensive error handling, monitoring, and data quality validation at the ingestion layer.

## High-Level Implementation Strategy

### 1. Pipeline Architecture

**Containerized Microservice Approach:**
- Single-purpose Python application in `apps/bronze-ingestion/`
- Docker container for consistent execution environment
- Scheduled execution via GitHub Actions (leveraging ADR-007)
- Stateless design with external state management in S3

**Data Ingestion Flow:**
```
NBA API → Raw JSON → Validation → Parquet Conversion → S3 Bronze Layer
    ↓         ↓           ↓            ↓              ↓
Rate Limit  Schema    Quality      Compression    Partition
Management  Check     Metrics      + Metadata     by Date
```

### 2. Scheduling Strategy

**Daily Execution Window:**
- Primary run: 4:30 AM ET (9:30 AM UTC)
- Backup run: 5:30 AM ET (10:30 AM UTC) if primary fails
- Weekend handling: Reduced frequency when no games scheduled

**Intelligent Scheduling:**
- Check NBA schedule API to determine if games occurred previous day
- Skip execution on days with no games (reduce API calls and costs)
- Holiday and All-Star break handling with configurable schedules

### 3. Data Scope and Organization

**Daily Ingestion Targets:**
- Previous day's completed games (box scores, play-by-play)
- Updated player statistics and season totals
- Team standings and statistics updates
- Injury reports and roster changes
- Incremental updates to season-long datasets

**Bronze Layer Organization (following existing plan):**
```
s3://hoopstat-haus-bronze/
├── nba-api/
│   ├── games/year=2024/month=01/day=15/hour=04/
│   ├── players/year=2024/month=01/day=15/hour=04/
│   ├── teams/year=2024/month=01/day=15/hour=04/
│   └── statistics/year=2024/month=01/day=15/hour=04/
├── ingestion-metadata/
│   └── run-logs/year=2024/month=01/day=15/hour=04/
└── data-quality/
    └── validation-results/year=2024/month=01/day=15/hour=04/
```

### 4. Error Handling and Reliability

**Robust Error Recovery:**
- Exponential backoff for API rate limiting (following nba-api best practices)
- Partial failure recovery: continue processing other data sources if one fails
- Dead letter queue: Store failed API calls for manual investigation
- Circuit breaker pattern: Temporarily halt requests if API is consistently failing

**Data Validation at Ingestion:**
- JSON schema validation for all API responses
- Completeness checks: Verify expected number of games/players for the day
- Freshness validation: Ensure data is for the expected date range
- Duplicate detection: Prevent re-ingesting same data multiple times

### 5. Monitoring and Observability

**Pipeline Health Monitoring:**
- Success/failure metrics for each data source
- API response time and rate limit utilization tracking
- Data quality metrics: completeness, freshness, schema compliance
- Storage utilization and cost tracking

**Alerting Strategy:**
- Critical: Pipeline failure or data quality issues → Immediate notification
- Warning: API rate limiting or performance degradation → Daily summary
- Info: Successful runs and data statistics → Weekly reports

## Required ADRs

The following ADRs need to be proposed to support the Bronze layer ingestion implementation:

### ADR-018: Bronze Layer Ingestion Scheduling and Orchestration
- **Decision Scope:** Define the scheduling mechanism and orchestration platform for daily data ingestion
- **Key Areas:** GitHub Actions vs AWS EventBridge, timezone handling, retry logic, failure recovery
- **Impact:** Determines reliability and operational complexity of the ingestion pipeline
- **Dependencies:** ADR-007 (GitHub Actions), ADR-009 (AWS Cloud), ADR-012 (Single Environment), ADR-017 (Infrastructure Deployment)

### ADR-019: NBA API Rate Limiting and Request Management Strategy
- **Decision Scope:** Establish patterns for managing API rate limits with emphasis on respectful API usage
- **Key Areas:** Request spacing, conservative rate limiting, backoff algorithms, API citizenship practices
- **Impact:** Ensures reliable data ingestion while maintaining respectful relationship with unofficial NBA API
- **Dependencies:** ADR-013 (NBA API Data Source), existing rate limiting research
- **Philosophy:** Prioritize being respectful and not getting kicked off the API over ingestion speed

### ADR-020: Bronze Layer Data Validation and Quality Gates
- **Decision Scope:** Define validation rules and quality thresholds for raw data ingestion
- **Key Areas:** Schema validation, completeness checks, freshness requirements, quarantine processes
- **Impact:** Ensures data quality and prevents propagation of bad data to Silver/Gold layers
- **Dependencies:** ADR-014 (Parquet Storage), ADR-015 (JSON Logging)

### ADR-021: Ingestion Pipeline State Management and Recovery
- **Decision Scope:** Define how pipeline state is managed and how recovery from failures works
- **Key Areas:** Idempotent operations, checkpoint mechanisms, partial failure recovery, state storage
- **Impact:** Ensures pipeline reliability and data consistency across runs
- **Dependencies:** ADR-009 (AWS Cloud), ADR-014 (Parquet Storage)

### ADR-022: UTC Datetime Standardization and ISO-8601 Format
- **Decision Scope:** Establish UTC as standard timezone with ISO-8601 format for all datetime handling
- **Key Areas:** Timezone standardization, datetime serialization, game time recording, data consistency
- **Impact:** Eliminates timezone complexity and ensures consistent datetime handling across all systems
- **Dependencies:** ADR-014 (Parquet Storage), ADR-015 (JSON Logging)

### ADR-023: Ingestion Monitoring and Alerting Framework
- **Decision Scope:** Define monitoring strategy, metrics collection, and alerting thresholds for data ingestion pipeline
- **Key Areas:** Health checks, performance metrics, data quality alerts, email notification integration
- **Impact:** Enables proactive issue detection and operational visibility for ingestion pipeline
- **Dependencies:** ADR-015 (JSON Logging), existing CloudWatch alarms infrastructure, AWS monitoring services
- **Note:** Should integrate with existing CloudWatch alarms and notification framework being established

## Risks & Open Questions

### Technical Risks

**1. NBA API Reliability and Changes**
- *Risk:* Unofficial API endpoints may change without notice, breaking the ingestion pipeline
- *Mitigation:* Comprehensive error handling, schema validation, and quick deployment capabilities
- *Open Question:* Should we implement a secondary data source as backup?

**2. Rate Limiting and API Access**
- *Risk:* Aggressive rate limiting could cause daily ingestion to fail or take too long
- *Mitigation:* Conservative, respectful request patterns with generous delays and intelligent backoff
- *Philosophy:* For this hobby project, we care far more about being respectful and not getting kicked off the API than being "blazing fast"
- *Open Question:* What's the optimal balance between ingestion completeness and API citizenship?

**3. Data Volume Growth**
- *Risk:* As we add more data sources and historical depth, ingestion time may exceed acceptable windows
- *Mitigation:* Start with conservative data scope (play-by-play focus), monitor volume trends, and reduce fields if needed
- *Expectation:* Daily ingestion volume should be relatively constant once flowing; will evaluate field reduction before moving to streaming
- *Open Question:* At what data volume do we need to move from daily batch to streaming ingestion?

**4. Storage Costs and Lifecycle Management**
- *Risk:* Indefinite retention of raw data in Bronze layer may become cost-prohibitive
- *Mitigation:* Implement intelligent lifecycle policies and compression optimization
- *Initial Approach:* Start with 1-year retention period, then evaluate over time based on usage and costs
- *Open Question:* How do storage costs scale with current data volume and retention needs?

### Operational Risks

**5. GitHub Actions Reliability**
- *Risk:* GitHub Actions downtime could prevent daily ingestion runs
- *Mitigation:* Backup scheduling mechanism, manual trigger capabilities
- *Open Question:* Should we have a secondary orchestration platform for critical runs?

**6. Timezone and Scheduling Complexity**
- *Risk:* Complex timezone handling for games across different time zones
- *Mitigation:* Standardize on UTC for all processing (ISO-8601 format), use game start time as effective record time
- *Game Logic:* A game's effective time in our records is its start time, which is always on the published date, so timezone complexity is simplified
- *ADR Needed:* Propose ADR for UTC everywhere and ISO-8601 datetime standardization if not already covered
- *Open Question:* Should we add timezone conversion utilities for user-facing interfaces?

**7. Monitoring and Alerting Gaps**
- *Risk:* Silent failures or data quality issues may go unnoticed
- *Mitigation:* Simple but effective monitoring focused on email notifications for maintainer when action is needed
- *Approach:* Integrate with existing CloudWatch alarms framework for email notifications on daily run failures
- *Scope:* Keep monitoring appropriate for hobby project - occasional emails when maintainer needs to take action
- *Open Question:* What are the essential failure scenarios that require immediate notification?

### Business/Project Risks

**8. Over-Engineering for Current Scale**
- *Risk:* Building enterprise-grade infrastructure for hobby project needs
- *Mitigation:* Start simple with play-by-play data focus, add complexity only when needed, follow YAGNI principle
- *Initial Scope:* Focus on play-by-play data at Bronze layer as primary data source
- *Open Question:* What's the minimum viable ingestion pipeline for current needs?

**9. Maintenance Burden**
- *Risk:* Complex ingestion pipeline requires ongoing maintenance and updates
- *Mitigation:* Simple architecture, comprehensive tests, clear documentation
- *Open Question:* How do we balance feature richness with maintenance simplicity?

## 🎯 ACTIONABLE FEATURE REQUESTS

### Phase 1: Foundation and Core Ingestion (MVP)

#### 1. feat: create bronze layer ingestion application structure
**Description:** Set up the basic application structure for the bronze ingestion pipeline following the established monorepo patterns.

**Deliverables:**
- New Python application in `apps/bronze-ingestion/`
- Poetry configuration with required dependencies (nba-api, pyarrow, boto3)
- Docker container configuration following existing patterns
- Basic project structure with main.py, requirements, and tests

**Acceptance Criteria:**
- [ ] Application follows existing app template structure
- [ ] Poetry configuration includes all required dependencies for NBA API and S3 access
- [ ] Dockerfile builds successfully and follows project Docker patterns
- [ ] Basic test structure is in place with pytest configuration
- [ ] Application can be built and tested using existing CI pipeline

---

#### 2. feat: implement basic NBA API data ingestion
**Description:** Create the core functionality to fetch and store raw NBA data from the nba-api library.

**Deliverables:**
- NBA API client with rate limiting and error handling
- Data fetching for games, players, and basic statistics
- Raw JSON to Parquet conversion functionality
- Basic S3 upload capabilities with proper partitioning

**Acceptance Criteria:**
- [ ] Successfully fetch data from nba-api for a given date range
- [ ] Convert raw JSON responses to Parquet format using PyArrow
- [ ] Upload Parquet files to S3 Bronze layer with correct partitioning scheme
- [ ] Handle API rate limiting with exponential backoff
- [ ] Comprehensive error logging for debugging

---

#### 3. feat: implement daily scheduling with GitHub Actions
**Description:** Set up automated daily scheduling for the ingestion pipeline using GitHub Actions.

**Deliverables:**
- GitHub Actions workflow for scheduled execution
- UTC timezone handling for consistent 4:30 AM ET runs
- Manual trigger capability for testing and recovery
- Basic success/failure notification

**Acceptance Criteria:**
- [ ] Workflow triggers automatically at 4:30 AM ET daily
- [ ] Manual workflow dispatch available for testing
- [ ] Proper AWS credentials configuration using GitHub OIDC
- [ ] Basic notification on workflow success/failure
- [ ] Workflow follows existing CI patterns and security practices

---

#### 4. feat: basic data validation and quality checks
**Description:** Implement essential data validation to ensure ingested data meets basic quality standards.

**Deliverables:**
- JSON schema validation for API responses
- Completeness checks for expected daily data
- Data freshness validation
- Quality metrics logging

**Acceptance Criteria:**
- [ ] Validate all API responses against expected JSON schemas
- [ ] Verify expected number of games and players for ingestion date
- [ ] Check that ingested data is for the correct date range
- [ ] Log data quality metrics for monitoring and debugging
- [ ] Quarantine invalid data for manual review

---

### Phase 2: Reliability and Monitoring

#### 5. feat: comprehensive error handling and recovery
**Description:** Implement robust error handling and recovery mechanisms for production reliability.

**Deliverables:**
- Circuit breaker pattern for API failures
- Partial failure recovery and continuation
- Failed request dead letter queue
- Automatic retry logic with configurable parameters

**Acceptance Criteria:**
- [ ] Pipeline continues processing other data sources when one fails
- [ ] Failed API requests are stored for manual investigation
- [ ] Circuit breaker prevents cascade failures during API outages
- [ ] Configurable retry logic with exponential backoff
- [ ] Clear error categorization (transient vs permanent failures)

---

#### 6. feat: ingestion monitoring and alerting system
**Description:** Build comprehensive monitoring and alerting for pipeline health and data quality.

**Deliverables:**
- Pipeline execution metrics and dashboards
- Data quality monitoring with trend analysis
- Multi-channel alerting (email, Slack, etc.)
- Cost and performance tracking

**Acceptance Criteria:**
- [ ] Track and visualize pipeline success rates and execution times
- [ ] Monitor data quality trends over time
- [ ] Alert on critical failures within 15 minutes
- [ ] Weekly summary reports of pipeline health and data statistics
- [ ] Cost tracking and optimization recommendations

---

### Phase 3: Optimization and Advanced Features

#### 7. feat: intelligent scheduling based on NBA schedule
**Description:** Optimize ingestion frequency based on actual NBA game schedule to reduce unnecessary API calls.

**Deliverables:**
- NBA schedule API integration
- Dynamic scheduling based on game availability
- Holiday and off-season handling
- Weekend and back-to-back game optimization

**Acceptance Criteria:**
- [ ] Skip ingestion on days with no NBA games
- [ ] Adjust ingestion frequency during playoffs and special events
- [ ] Handle holiday schedules and All-Star break appropriately
- [ ] Optimize for back-to-back games and West Coast game endings
- [ ] Maintain data freshness SLAs while minimizing unnecessary runs

---

#### 8. feat: incremental ingestion and change detection
**Description:** Implement incremental ingestion patterns to improve efficiency and reduce redundant data processing.

**Deliverables:**
- Change detection for player and team data
- Incremental updates for season statistics
- Deduplication at ingestion layer
- State management for tracking processed data

**Acceptance Criteria:**
- [ ] Only ingest changed player and team information
- [ ] Efficiently update season statistics without full reprocessing
- [ ] Detect and prevent ingestion of duplicate data
- [ ] Maintain state between runs for incremental processing
- [ ] Significant reduction in processing time and API calls

---

#### 9. feat: bronze layer data lifecycle management
**Description:** Implement automated data lifecycle policies for cost optimization and compliance.

**Deliverables:**
- S3 lifecycle policies for automated data archival
- Configurable retention periods by data type
- Cost optimization with storage class transitions
- Data deletion and archival capabilities

**Acceptance Criteria:**
- [ ] Automatic transition to cheaper storage classes based on age
- [ ] Configurable retention periods for different data types
- [ ] Cost reporting and optimization recommendations
- [ ] Secure data deletion when required
- [ ] Compliance with data retention policies

---

#### 10. feat: ingestion pipeline performance optimization
**Description:** Optimize the ingestion pipeline for speed, efficiency, and cost-effectiveness.

**Deliverables:**
- Parallel processing for independent data sources
- Request batching and optimization
- Compression and storage optimization
- Performance benchmarking and monitoring

**Acceptance Criteria:**
- [ ] Parallel ingestion of independent data sources
- [ ] Optimal request patterns to maximize API efficiency
- [ ] Storage cost reduction through better compression and partitioning
- [ ] Performance benchmarks and regression detection
- [ ] Sub-30-minute ingestion time for daily data

---

## Phase-Based Implementation Roadmap

### Phase 1: Foundation & MVP (Weeks 1-2)
**Goal:** Get basic daily ingestion working reliably

**Priority Features:**
1. Bronze layer ingestion application structure
2. Basic NBA API data ingestion
3. Daily scheduling with GitHub Actions
4. Basic data validation and quality checks

**Success Criteria:**
- Daily ingestion runs successfully at 4:30 AM ET
- Raw NBA data is stored in Bronze layer S3 buckets
- Basic error handling prevents pipeline crashes
- Data quality meets minimum thresholds

### Phase 2: Reliability & Production-Ready (Weeks 3-4)
**Goal:** Make the pipeline production-ready with monitoring and error handling

**Priority Features:**
1. Comprehensive error handling and recovery
2. Ingestion monitoring and alerting system

**Success Criteria:**
- Pipeline has 99% uptime over 2-week period
- All critical failures are detected and alerted within 15 minutes
- Comprehensive monitoring provides operational visibility
- Data quality trends are tracked and reported

### Phase 3: Optimization & Advanced Features (Weeks 5-8)
**Goal:** Optimize for efficiency, cost, and advanced capabilities

**Priority Features:**
1. Intelligent scheduling based on NBA schedule
2. Incremental ingestion and change detection
3. Bronze layer data lifecycle management
4. Ingestion pipeline performance optimization

**Success Criteria:**
- 50% reduction in unnecessary API calls through intelligent scheduling
- Ingestion time reduced by 40% through optimization
- Storage costs optimized through lifecycle management
- Pipeline can handle peak season load (playoffs, high game volume)

### Success Metrics

**Technical Metrics:**
- Pipeline uptime: >99%
- Data freshness: <2 hours after games complete
- Ingestion time: <30 minutes for daily data
- API rate limit utilization: <80%
- Data quality score: >95%

**Operational Metrics:**
- Mean time to detection (MTTD): <15 minutes
- Mean time to recovery (MTTR): <2 hours
- Storage cost efficiency: <$10/month for Bronze layer
- Alert noise ratio: <5% false positives

**Business Metrics:**
- Daily data availability: 100%
- Historical data completeness: >98%
- User satisfaction with data freshness
- Foundation readiness for Silver/Gold layer processing

---

*This plan provides a complete roadmap for implementing reliable, cost-effective daily Bronze layer ingestion that serves as the foundation for the broader Medallion Architecture. Each phase builds upon the previous one while delivering immediate value.*