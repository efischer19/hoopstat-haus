# S3 Medallion Architecture Implementation

This document describes the implementation of the medallion data architecture (Bronze/Silver/Gold) S3 buckets and access policies for the Hoopstat Haus project.

## Overview

The implementation creates a three-tier data lake structure following industry-standard medallion architecture:

- **Bronze Layer**: Raw data landing zone for unprocessed NBA API data
- **Silver Layer**: Cleaned and conformed data with quality validation
- **Gold Layer**: Business-ready aggregated data optimized for MCP server consumption

## Infrastructure Components

### S3 Buckets

Four S3 buckets are created with the following naming convention:

```
hoopstat-haus-bronze      # Raw data landing zone
hoopstat-haus-silver      # Cleaned and conformed data  
hoopstat-haus-gold        # Business-ready aggregated data
hoopstat-haus-access-logs # Access logging for all buckets
```

Each bucket includes:
- **Encryption**: AES256 server-side encryption enabled
- **Versioning**: Object versioning enabled for data lineage
- **Public Access**: All public access blocked for security
- **Access Logging**: Detailed access logs stored in dedicated logging bucket

### Lifecycle Policies for Cost Optimization

#### Bronze Layer Lifecycle
- Day 30: Transition to Intelligent Tiering
- Day 90: Transition to Standard-IA
- Day 365: Transition to Glacier for archival
- Cleanup: Incomplete multipart uploads (7 days), delete markers (30 days)

#### Silver Layer Lifecycle  
- Day 90: Transition to Standard-IA
- Day 730: Transition to Glacier for long-term storage
- Cleanup: Incomplete multipart uploads (7 days), delete markers (30 days)

#### Gold Layer Lifecycle
- No storage class transitions (kept in Standard for MCP server performance)
- Cleanup: Incomplete multipart uploads (7 days), delete markers (30 days)

### IAM Roles and Policies (Least-Privilege Access)

#### Bronze Layer Access Role
- **Purpose**: Data ingestion services
- **Permissions**: Write-only access to Bronze bucket
- **Actions**: `s3:PutObject`, `s3:PutObjectAcl`, `s3:ListBucket`

#### Silver Layer Access Role  
- **Purpose**: Data transformation and cleaning services
- **Permissions**: Read Bronze bucket, write Silver bucket
- **Actions**: Read from Bronze + write to Silver + CloudWatch logging

#### Gold Layer Access Role
- **Purpose**: Aggregation and business logic services  
- **Permissions**: Read Silver bucket, read/write Gold bucket
- **Actions**: Read from Silver + read/write to Gold + CloudWatch logging

#### MCP Server Access Role
- **Purpose**: Read-only access for serving processed data
- **Permissions**: Read-only access to Gold bucket
- **Actions**: `s3:GetObject`, `s3:ListBucket` on Gold bucket only

### Monitoring and Observability

#### CloudWatch Alarms
- **Bronze/Silver/Gold Bucket 4xx Errors**: Monitors access errors
- **Gold Bucket High Request Rate**: Monitors performance for MCP server
- **Lambda Timeout Monitoring**: Monitors processing pipeline health
- **Execution Time Anomaly**: Monitors data pipeline performance

#### Access Logging
- All bucket access logged to dedicated `hoopstat-haus-access-logs` bucket
- Log prefixes: `bronze-access-logs/`, `silver-access-logs/`, `gold-access-logs/`
- Logs retained for 90 days with automatic lifecycle management

## Data Flow Architecture

```
NBA API → Bronze Layer → Silver Layer → Gold Layer → MCP Server
   ↓           ↓             ↓           ↓
Raw JSON  → Parquet    → Validated  → Aggregated
Files       Files        Parquet      Business
                         Files        Data
```

### Access Patterns

1. **Data Ingestion** (Bronze): Write-only by ingestion services
2. **Data Transformation** (Silver): Read Bronze → Write Silver
3. **Data Aggregation** (Gold): Read Silver → Write Gold  
4. **Data Serving** (MCP): Read-only from Gold

## Security Features

- **Encryption at Rest**: AES256 encryption for all buckets
- **Encryption in Transit**: HTTPS enforced for all bucket access
- **Access Control**: Least-privilege IAM policies per data layer
- **Public Access**: Completely blocked for all buckets
- **Audit Trail**: Complete access logging and CloudWatch monitoring

## Backward Compatibility

The legacy `hoopstat-haus-prod-data` bucket is preserved with `Status = "legacy"` tag to maintain backward compatibility during the transition period.

## Testing

Comprehensive test suite validates:
- Bucket configuration and security settings
- IAM policy least-privilege compliance  
- Lifecycle policy cost optimization
- Monitoring and alerting setup
- Terraform syntax and structure

Run tests: `python3 tests/test_s3_medallion_architecture.py`

## Outputs

The following Terraform outputs are available for integration:

### Bucket Information
- `bronze_bucket_name` / `bronze_bucket_arn`
- `silver_bucket_name` / `silver_bucket_arn`  
- `gold_bucket_name` / `gold_bucket_arn`
- `access_logs_bucket_name` / `access_logs_bucket_arn`

### IAM Role Information
- `bronze_layer_role_arn` / `bronze_layer_role_name`
- `silver_layer_role_arn` / `silver_layer_role_name`
- `gold_layer_role_arn` / `gold_layer_role_name`
- `mcp_server_role_arn` / `mcp_server_role_name`

## Cost Optimization

The implementation includes several cost optimization features:

1. **Lifecycle Policies**: Automatic transition to cheaper storage classes
2. **Intelligent Tiering**: Automatic optimization based on access patterns
3. **Log Cleanup**: Automatic deletion of old access logs (90 days)
4. **Multipart Upload Cleanup**: Automatic cleanup of incomplete uploads
5. **Versioning Management**: Cleanup of old delete markers

Estimated monthly costs for typical hobby project usage:
- Bronze Layer: $5-15 (depending on ingestion volume)
- Silver Layer: $10-25 (processed data storage)
- Gold Layer: $5-15 (aggregated data, frequently accessed)
- Access Logs: $1-3 (minimal log storage)

## Related Documentation

- [Medallion Data Architecture Plan](../meta/plans/medallion-data-architecture.md)
- [ADR-009: AWS Cloud Provider Selection](../meta/adr/ADR-009-aws_cloud.md)
- [ADR-010: Terraform Infrastructure as Code](../meta/adr/ADR-010-terraform_iac.md)
- [ADR-014: Parquet Storage Format](../meta/adr/ADR-014-parquet_storage.md)