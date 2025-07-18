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
- Primary data: 2 years (sufficient for hobby project historical analysis)
- Error logs: 30 days (operational debugging)
- API metadata: 90 days (performance monitoring and optimization)

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
- Primary data: 3 years (sufficient for hobby project historical analytics)
- Data quality logs: 90 days (trend analysis and process improvement)
- Quarantined data: 30 days (manual review and potential recovery)

### Gold Layer (Business/Analytics-Ready)

**Purpose:** Store aggregated, business-focused datasets optimized for consumption by analytics tools, dashboards, and the MCP server.

**Note:** The exact aggregations, dimensions, and data structures in the Gold layer will be largely driven by the capabilities and requirements of our MCP server.

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

## Next Steps: Feature Requests for Implementation

Based on this Medallion Architecture plan, here are the specific feature requests that can be created as GitHub issues to implement the data platform:

### **Phase 1: Foundation & Bronze Layer**

**1. Create S3 Bucket Infrastructure with Terraform**
```
Title: Set up S3 buckets for Medallion Architecture (Bronze/Silver/Gold)
Description: Create three S3 buckets with proper lifecycle policies, IAM roles, and CloudWatch logging.
Deliverables: Terraform configuration for hoopstat-haus-bronze, hoopstat-haus-silver, hoopstat-haus-gold buckets
```

**2. Build Bronze Layer Data Ingestion Pipeline**
```
Title: Implement Bronze layer NBA API data ingestion
Description: Create Python service to ingest raw NBA data from nba-api and store as Parquet in Bronze layer
Deliverables: Dockerized Python app with scheduled ingestion, error handling, and audit logging
```

**3. Propose Required ADRs for Data Architecture**
```
Title: Create ADR-016 through ADR-022 for data pipeline architecture decisions
Description: Propose 7 ADRs covering ingestion patterns, data quality, lineage, aggregation, orchestration, security, and monitoring
Deliverables: 7 new ADR files with Proposed status ready for review
```

### **Phase 2: Silver Layer & Data Quality**

**4. Implement Silver Layer Data Transformation Pipeline**
```
Title: Build Silver layer data cleaning and validation framework
Description: Create transformation pipeline with schema enforcement, deduplication, and data quality validation
Deliverables: Python transformation service with comprehensive quality checks and quarantine handling
```

**5. Create Data Quality Monitoring Dashboard**
```
Title: Implement data quality metrics and monitoring
Description: Build dashboard to track completeness, accuracy, timeliness, and consistency across all data layers
Deliverables: Monitoring dashboard with alerting for quality issues
```

### **Phase 3: Gold Layer & MCP Integration**

**6. Build Gold Layer Aggregation Engine**
```
Title: Implement Gold layer pre-computed aggregations for MCP server
Description: Create aggregation pipeline optimized for MCP server consumption patterns
Deliverables: Star schema dimensional model with pre-computed metrics and fast lookup tables
```

**7. Optimize Data Pipeline for MCP Server Performance**
```
Title: Create MCP-optimized datasets and caching layer
Description: Build API-ready datasets with sub-second response times for MCP server integration
Deliverables: Partitioned Gold layer datasets with Redis caching for frequent queries
```

### **Infrastructure & Operations**

**8. Set Up Data Pipeline CI/CD**
```
Title: Implement automated deployment and testing for data pipelines
Description: Create GitHub Actions workflows for pipeline deployment, testing, and monitoring
Deliverables: Complete CI/CD pipeline with automated testing and deployment
```

**9. Implement Data Security and Access Controls**
```
Title: Set up data security framework with encryption and IAM policies
Description: Implement least-privilege access, encryption at rest/transit, and audit logging
Deliverables: Security framework with proper IAM roles and encryption configuration
```

**10. Create Data Pipeline Orchestration**
```
Title: Implement pipeline scheduling and dependency management
Description: Set up orchestration system for automated data processing across all layers
Deliverables: Scheduled pipeline execution with dependency handling and error recovery
```

---

*Copy any of the above feature request templates to create new GitHub issues for implementing the Medallion Data Architecture.*