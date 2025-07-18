# Medallion Data Architecture (Bronze/Silver/Gold) Strategy

## Executive Summary

This plan defines the Medallion Architecture for the Hoopstat Haus data platform, establishing a three-tier data lake structure that progressively refines raw NBA statistics into high-value, analysis-ready datasets. The architecture follows the industry-standard Bronze (raw), Silver (cleaned/conformed), and Gold (aggregated/business-ready) layer pattern, ensuring data quality, lineage, and scalability while supporting the project's MCP server and future analytics applications.

The implementation leverages our established tech stack including AWS S3 for storage, Apache Parquet for data format (per ADR-014), the nba-api for data ingestion (per ADR-013), and Python/Docker/Terraform for processing infrastructure.

## Data Layer Definitions

### Bronze Layer (Raw/Landing Zone)

**Purpose:** Store raw, unprocessed data exactly as received from source systems with minimal transformation.

**Data State:**
- **Immutable**: Data is never modified once written, preserving complete audit trail
- **Schema-on-Read**: No enforcement of schema at write time, maintaining source fidelity
- **Full Fidelity**: Complete preservation of source data including metadata, timestamps, and error records
- **Append-Only**: New data is always appended, never updated or deleted

**Data Sources:**
- Raw JSON responses from nba-api endpoints (games, players, teams, statistics)
- API metadata (request timestamps, response headers, rate limiting info)
- Error logs and failed API calls for data quality monitoring
- External data feeds (future expansion to other sports data sources)

**File Organization:**
```
s3://hoopstat-haus-bronze/
├── nba-api/
│   ├── games/year=2024/month=01/day=15/hour=14/
│   ├── players/year=2024/month=01/day=15/hour=14/
│   ├── teams/year=2024/month=01/day=15/hour=14/
│   └── statistics/year=2024/month=01/day=15/hour=14/
├── api-metadata/
│   └── ingestion-logs/year=2024/month=01/day=15/hour=14/
└── errors/
    └── failed-requests/year=2024/month=01/day=15/hour=14/
```

**Transformations Applied:**
- Format conversion: JSON to Parquet with embedded original JSON
- Partitioning by ingestion timestamp (year/month/day/hour)
- Addition of technical metadata (ingestion_timestamp, source_system, api_version)
- Compression using Snappy codec for optimal storage/query balance

**Retention Policy:** 
- Primary data: 7 years (regulatory compliance and historical analysis)
- Error logs: 1 year (operational debugging)
- API metadata: 2 years (performance monitoring and optimization)

### Silver Layer (Cleaned/Conformed)

**Purpose:** Store cleaned, validated, and standardized data with consistent schema and data quality rules applied.

**Data State:**
- **Schema-Enforced**: Strict schema validation with data type enforcement
- **Deduplicated**: Removal of duplicate records with configurable business rules
- **Standardized**: Consistent naming conventions, data types, and value formats
- **Quality-Assured**: Data quality rules applied with quarantine of invalid records
- **Slowly Changing Dimensions**: Type 2 SCD implementation for player/team changes

**Data Transformations:**
- **Data Cleaning**: Handle null values, standardize text fields, validate numeric ranges
- **Schema Standardization**: Convert to consistent column names and data types across all tables
- **Deduplication**: Remove duplicate API calls and apply business rules for record uniqueness
- **Data Quality Validation**: Implement comprehensive validation rules with quality metrics
- **Reference Data Integration**: Enrich with standardized team names, player positions, etc.
- **Temporal Consistency**: Ensure consistent time zone handling and date formats

**File Organization:**
```
s3://hoopstat-haus-silver/
├── games/
│   └── season=2023-24/month=01/
├── players/
│   └── effective_date=2024-01-15/
├── teams/
│   └── effective_date=2024-01-15/
├── game_statistics/
│   └── season=2023-24/month=01/
├── player_statistics/
│   └── season=2023-24/month=01/
└── data_quality/
    ├── validation_results/date=2024-01-15/
    └── quarantine/date=2024-01-15/
```

**Data Quality Framework:**
- **Completeness**: Validation of required fields and expected record counts
- **Accuracy**: Range checks, format validation, and referential integrity
- **Consistency**: Cross-table validation and business rule enforcement
- **Timeliness**: Data freshness monitoring and SLA tracking
- **Uniqueness**: Duplicate detection and resolution with configurable business rules

**Retention Policy:**
- Primary data: 10 years (extended for historical analytics)
- Data quality logs: 2 years (trend analysis and process improvement)
- Quarantined data: 90 days (manual review and potential recovery)

### Gold Layer (Business/Analytics-Ready)

**Purpose:** Store aggregated, business-focused datasets optimized for consumption by analytics tools, dashboards, and the MCP server.

**Data State:**
- **Business-Aligned**: Organized by business domains and use cases
- **Pre-Aggregated**: Common aggregations pre-computed for performance
- **Dimension-Modeled**: Star/snowflake schema design for analytical queries
- **Performance-Optimized**: Partitioned and indexed for sub-second query response
- **API-Ready**: Structured for direct consumption by MCP server and applications

**Business Domains:**
- **Player Performance**: Individual player statistics, trends, and advanced metrics
- **Team Analytics**: Team performance, head-to-head comparisons, season trends
- **Game Insights**: Game-level analysis, scoring patterns, key moments
- **Season Summaries**: League-wide statistics, rankings, historical comparisons
- **Fantasy Analytics**: Fantasy-relevant statistics and projections
- **Advanced Metrics**: Calculated statistics like PER, Win Shares, usage rates

**File Organization:**
```
s3://hoopstat-haus-gold/
├── player_performance/
│   ├── daily_stats/season=2023-24/month=01/
│   ├── season_aggregates/season=2023-24/
│   └── career_totals/as_of_date=2024-01-15/
├── team_analytics/
│   ├── team_stats/season=2023-24/month=01/
│   ├── head_to_head/season=2023-24/
│   └── standings/as_of_date=2024-01-15/
├── game_insights/
│   └── game_summary/season=2023-24/month=01/
├── advanced_metrics/
│   └── calculated_stats/season=2023-24/month=01/
└── mcp_datasets/
    ├── current_season/
    ├── player_lookup/
    └── team_lookup/
```

**Aggregation Strategies:**
- **Temporal**: Daily, weekly, monthly, and season-to-date aggregations
- **Hierarchical**: Individual → Team → Conference → League rollups
- **Dimensional**: By position, age group, experience level, salary range
- **Performance Windows**: Rolling averages (5-game, 10-game, season)
- **Comparative**: vs. season average, vs. career average, vs. position peers

**MCP Server Integration:**
- **Optimized Datasets**: Pre-built tables for common MCP queries
- **Lookup Tables**: Fast reference data for player/team information
- **Real-time Views**: Current season data updated within 1 hour of games
- **Historical Context**: Easy access to comparative historical data
- **API-Friendly Formats**: JSON-compatible schemas for direct API serving

**Retention Policy:**
- All aggregated data: Indefinite (core business value)
- Historical snapshots: Indefinite (trend analysis and model training)
- Lookup tables: Indefinite with versioning (reference data)

## S3 Bucket Architecture & Partitioning Strategy

### Bucket Structure

Following AWS best practices and the project's single-environment strategy (ADR-012), we'll use three dedicated S3 buckets:

```
hoopstat-haus-bronze    # Raw data landing zone
hoopstat-haus-silver    # Cleaned and conformed data
hoopstat-haus-gold      # Business-ready aggregated data
```

### Partitioning Strategy

**Bronze Layer Partitioning:**
- **Primary**: Ingestion timestamp for efficient data lifecycle management
- **Pattern**: `year=YYYY/month=MM/day=DD/hour=HH/`
- **Benefits**: Enables efficient data archival, cost optimization, and debugging
- **Query Optimization**: Temporal queries benefit from partition pruning

**Silver Layer Partitioning:**
- **Primary**: Business-relevant time dimensions (season, month)
- **Pattern**: `season=YYYY-YY/month=MM/` or `effective_date=YYYY-MM-DD/`
- **Benefits**: Aligns with NBA season structure and common query patterns
- **Flexibility**: Mixed partitioning strategies based on data characteristics

**Gold Layer Partitioning:**
- **Primary**: Business domain and temporal relevance
- **Pattern**: `season=YYYY-YY/month=MM/` for time-series data
- **Pattern**: `as_of_date=YYYY-MM-DD/` for snapshot data
- **Benefits**: Optimizes for MCP server queries and dashboard performance

### Storage Optimization

**Parquet Configuration (aligned with ADR-014):**
- **Compression**: Snappy (optimal balance of compression ratio and query speed)
- **Row Group Size**: 128MB (optimal for S3 and analytical queries)
- **Column Chunk Size**: 1MB (balance memory usage and I/O efficiency)
- **Metadata**: Include data lineage and quality metrics in file metadata

**S3 Storage Classes:**
- **Bronze**: Standard → Intelligent Tiering after 30 days
- **Silver**: Standard → Standard-IA after 90 days
- **Gold**: Standard (frequently accessed by MCP server)

**Cost Optimization:**
- **Lifecycle Policies**: Automatic transition to cheaper storage classes
- **Incomplete Multipart Upload Cleanup**: 7-day automatic cleanup
- **Delete Markers**: Cleanup after 30 days for versioned objects

## Required ADRs for Implementation

The following ADRs need to be proposed to support the full implementation of this Medallion Architecture:

### ADR-016: Bronze Layer Ingestion Pattern and Error Handling
- **Decision Scope**: Define standardized patterns for ingesting raw data from nba-api
- **Key Areas**: API rate limiting strategy, error handling and retry logic, data validation at ingestion
- **Impact**: Ensures reliable and consistent data ingestion across all pipeline components
- **Dependencies**: ADR-013 (NBA API), ADR-014 (Parquet format)

### ADR-017: Silver Layer Data Quality and Validation Framework
- **Decision Scope**: Establish comprehensive data quality rules and validation processes
- **Key Areas**: Schema validation, data quality metrics, quarantine and recovery processes
- **Impact**: Ensures data reliability and trust for downstream consumers
- **Dependencies**: ADR-016 (bronze ingestion), ADR-015 (JSON logging)

### ADR-018: Data Lineage and Metadata Management Strategy
- **Decision Scope**: Define how data lineage is tracked and metadata is managed across layers
- **Key Areas**: Lineage tracking, metadata schema, catalog integration
- **Impact**: Enables data governance, debugging, and impact analysis
- **Dependencies**: ADR-014 (Parquet), ADR-009 (AWS infrastructure)

### ADR-019: Gold Layer Aggregation and Partitioning for MCP Integration
- **Decision Scope**: Define aggregation strategies and data structures optimized for MCP server
- **Key Areas**: Pre-computed aggregations, API-friendly schemas, caching strategies
- **Impact**: Optimizes performance and user experience for MCP server consumers
- **Dependencies**: ADR-017 (data quality), future MCP server ADR

### ADR-020: Data Pipeline Orchestration and Scheduling
- **Decision Scope**: Choose orchestration platform and define scheduling patterns
- **Key Areas**: Workflow management, dependency handling, error recovery
- **Impact**: Ensures reliable, automated data processing across all layers
- **Dependencies**: ADR-007 (GitHub Actions), ADR-010 (Terraform)

### ADR-021: Data Security and Access Control Framework
- **Decision Scope**: Define security model for data access across different layers
- **Key Areas**: IAM policies, encryption at rest/transit, audit logging
- **Impact**: Ensures data security and compliance with privacy requirements
- **Dependencies**: ADR-009 (AWS), ADR-011 (GitHub OIDC)

### ADR-022: Data Monitoring and Alerting Strategy
- **Decision Scope**: Define monitoring approach for data quality, pipeline health, and performance
- **Key Areas**: Data quality metrics, pipeline monitoring, alerting thresholds
- **Impact**: Enables proactive issue detection and resolution
- **Dependencies**: ADR-015 (JSON logging), AWS monitoring services

## Implementation Strategy with Current Tech Stack

### Phase 1: Foundation and Bronze Layer (Weeks 1-3)

**Terraform Infrastructure (leveraging ADR-010):**
```hcl
# S3 buckets with proper lifecycle policies
# IAM roles for data pipeline access  
# CloudWatch log groups for monitoring
```

**Python Pipeline Components (leveraging ADR-002, ADR-003):**
- **Bronze Ingestion Service**: Python application using nba-api for data extraction
- **Data Validation**: Basic schema validation and error handling
- **Parquet Conversion**: Raw JSON to Parquet conversion with metadata

**Docker Containerization (leveraging ADR-006):**
- Containerized ingestion pipeline for consistent deployment
- Multi-stage builds for optimized image size
- Health checks and graceful shutdown handling

**GitHub Actions Integration (leveraging ADR-007):**
- Automated pipeline deployment on code changes
- Scheduled data ingestion jobs
- Infrastructure deployment workflows

### Phase 2: Silver Layer and Data Quality (Weeks 4-6)

**Data Transformation Pipeline:**
- **Schema Evolution**: Handle API schema changes gracefully
- **Data Quality Engine**: Comprehensive validation and quality scoring
- **Deduplication Service**: Business rule-based duplicate resolution
- **Reference Data Management**: Maintain standardized lookup tables

**Quality Monitoring:**
- **Data Quality Dashboard**: Real-time visibility into data health
- **Alerting System**: Proactive notification of quality issues
- **Quality Metrics**: Track completeness, accuracy, timeliness, and consistency

**Testing Strategy (leveraging ADR-004):**
- **Unit Tests**: Core transformation logic validation
- **Integration Tests**: End-to-end pipeline testing
- **Data Quality Tests**: Validation of business rules and constraints

### Phase 3: Gold Layer and MCP Integration (Weeks 7-9)

**Aggregation Engine:**
- **Dimensional Modeling**: Star schema implementation for analytics
- **Pre-computation Service**: Calculate common aggregations and metrics
- **Incremental Processing**: Efficient updates for new data

**MCP Server Optimization:**
- **API-Ready Datasets**: Pre-structured data for fast API responses
- **Caching Layer**: Redis/ElastiCache for frequently accessed data
- **Query Optimization**: Partitioning and indexing for sub-second response

**Performance Monitoring:**
- **Query Performance**: Track response times and optimization opportunities
- **Cost Monitoring**: S3 storage costs and optimization recommendations
- **Usage Analytics**: Track MCP server data consumption patterns

### Technology Integration Points

**Python Ecosystem:**
- **pandas/polars**: Data manipulation and transformation
- **PyArrow**: High-performance Parquet I/O operations
- **Great Expectations**: Data quality validation framework
- **Prefect/Airflow**: Pipeline orchestration (to be decided in ADR-020)

**AWS Services Integration:**
- **S3**: Primary storage layer with lifecycle management
- **Lambda**: Serverless processing for lightweight transformations
- **Glue**: ETL jobs for heavy transformations (if needed)
- **Athena**: Ad-hoc querying and data exploration
- **CloudWatch**: Monitoring, logging, and alerting

**Docker and CI/CD:**
- **Multi-stage builds**: Separate images for different pipeline stages
- **Environment promotion**: Dev → Staging → Production pipeline
- **Infrastructure as Code**: Terraform for reproducible environments

## Data Governance and Quality Framework

### Data Quality Dimensions

**Completeness:**
- Required field validation (player names, game dates, scores)
- Expected record count validation (games per season, players per team)
- Missing data tracking and reporting

**Accuracy:**
- Range validation (scores >= 0, game duration within reasonable bounds)
- Format validation (dates, numeric fields, categorical values)
- Referential integrity (player-team relationships, game-team consistency)

**Consistency:**
- Cross-table validation (player statistics sum to team totals)
- Temporal consistency (no future game dates, logical progression)
- Business rule enforcement (active roster limits, salary cap rules)

**Timeliness:**
- Data freshness monitoring (games updated within 2 hours)
- SLA tracking (Bronze → Silver → Gold processing times)
- Late data handling and backfill procedures

**Uniqueness:**
- Duplicate detection across all layers
- Business key validation (unique game IDs, player-game combinations)
- Conflict resolution for overlapping data sources

### Metadata Management

**Technical Metadata:**
- Data lineage tracking from source to consumption
- Schema evolution history and impact analysis
- Processing statistics (record counts, processing times)

**Business Metadata:**
- Data definitions and business glossary
- Quality metrics and data certification status
- Usage statistics and access patterns

**Operational Metadata:**
- Pipeline execution logs and performance metrics
- Error logs and recovery procedures
- Data refresh schedules and dependencies

## Performance and Scalability Considerations

### Query Optimization

**Partitioning Strategy:**
- Time-based partitioning aligns with common query patterns
- Business domain partitioning optimizes analytical workloads
- Composite partitioning for complex query requirements

**File Sizing:**
- Target 100-200MB Parquet files for optimal query performance
- Batch processing to achieve optimal file sizes
- Automatic file compaction for small file problems

**Caching Strategy:**
- MCP server response caching for frequently accessed data
- Intelligent cache invalidation based on data freshness
- Multi-tier caching (application, CDN, browser)

### Cost Optimization

**Storage Management:**
- Intelligent tiering based on access patterns
- Compression optimization across different data types
- Archival policies for historical data

**Compute Optimization:**
- Right-sizing of processing resources
- Spot instances for non-time-critical processing
- Serverless-first approach for variable workloads

**Data Transfer:**
- Minimize cross-region data transfer
- Optimize API call patterns to reduce costs
- Batch processing to reduce per-operation costs

## Security and Compliance

### Data Protection

**Encryption:**
- Encryption at rest using AWS KMS
- Encryption in transit for all data movement
- Key rotation and access logging

**Access Control:**
- Least privilege IAM policies for each layer
- Role-based access control for different user types
- Audit logging for all data access

**Privacy:**
- No PII collection from public NBA data
- Data anonymization for any future user-generated content
- Retention policies aligned with business needs

### Compliance Framework

**Audit Trail:**
- Complete data lineage documentation
- Change tracking for all data modifications
- Access logging and compliance reporting

**Data Quality Assurance:**
- Automated validation and quality scoring
- Manual review processes for critical data
- Quality certification workflows

## Success Criteria and Metrics

### Data Quality Metrics

**Completeness Targets:**
- Bronze Layer: 99.5% of expected API calls successful
- Silver Layer: 99.9% of bronze data successfully processed
- Gold Layer: 100% of silver data aggregated within SLA

**Accuracy Targets:**
- Data validation: <0.1% records failing validation rules
- Referential integrity: 100% consistency across related tables
- Business rule compliance: 100% adherence to NBA rule constraints

**Timeliness Targets:**
- Bronze Layer: Data ingested within 1 hour of game completion
- Silver Layer: Data processed within 2 hours of bronze ingestion
- Gold Layer: Aggregations updated within 4 hours of game completion

### Performance Metrics

**Query Performance:**
- MCP server responses: <500ms for 95th percentile
- Ad-hoc analytics queries: <5 seconds for common patterns
- Bulk data exports: <10 minutes for full season datasets

**Cost Efficiency:**
- Storage costs: <$100/month for full NBA season data
- Compute costs: <$200/month for all processing
- Total cost per query: <$0.001 for typical MCP requests

**Operational Metrics:**
- Pipeline success rate: >99.5% across all layers
- Mean time to recovery: <30 minutes for production issues
- Data freshness SLA: >99% of data updated within target timeframes

### Business Value Metrics

**Data Utilization:**
- MCP server API calls: Track usage growth and user satisfaction
- Analytics queries: Monitor dashboard and report usage
- Data discovery: Track catalog usage and data exploration

**Quality Improvements:**
- Reduction in data quality issues over time
- Faster time-to-insight for new analytics requirements
- Improved confidence in data-driven decisions

---

*This Medallion Architecture plan aligns with the project's development philosophy of simplicity and maintainability while providing a robust foundation for scalable data processing. It builds upon established architectural decisions including AWS cloud infrastructure (ADR-009), Parquet storage format (ADR-014), and NBA API data sourcing (ADR-013), ensuring consistency with the project's technical direction.*