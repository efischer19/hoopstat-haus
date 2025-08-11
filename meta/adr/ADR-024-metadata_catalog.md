---
title: "ADR-024: Metadata Catalog Strategy for Data Discovery and Schema Management"
status: "Accepted"
date: "2025-08-11"
tags:
  - "data-pipeline"
  - "metadata"
  - "catalog"
  - "data-discovery"
  - "schema-management"
---

## Context

* **Problem:** The data pipeline currently lacks a centralized metadata catalog for data discovery and schema management across Bronze, Silver, and Gold layers. While hierarchical S3 partitioning (ADR-020) provides efficient storage and query performance, discovering available datasets, understanding schema evolution, and enabling automated data lineage tracking requires additional metadata infrastructure. The MCP server and E2E testing frameworks need efficient mechanisms to discover and validate data artifacts without hardcoded S3 path assumptions.
* **Constraints:** Must integrate with existing S3+Parquet architecture (ADR-014, ADR-020), support sub-100ms MCP server response times, maintain alignment with project's static-first philosophy preferring build-time optimizations, operate within AWS single-environment constraints (ADR-012), support CI/testing automation, enable schema evolution without breaking existing consumers, and minimize operational overhead consistent with the project's simplicity principles.

## Decision

We will implement a **lightweight metadata index** using S3-stored JSON manifests combined with a small index library integrated into `hoopstat-data`, providing static catalog generation at ETL time with fast runtime discovery capabilities.

## Considered Options

1. **Lightweight S3 Metadata Index (The Chosen One):** JSON/YAML manifests stored in S3 with small indexing library in `hoopstat-data`.
   * *Pros:* Minimal operational overhead aligning with project simplicity, leverages existing S3 infrastructure, static generation fits build-time optimization philosophy, fast discovery for MCP server queries (sub-10ms), integrates seamlessly with current partitioning strategy, version-controlled metadata enables schema evolution tracking, minimal cost impact (<$1/month storage), supports both programmatic and human-readable discovery, enables automated lineage tracking via manifest dependencies
   * *Cons:* Manual integration required for ETL jobs, limited advanced query capabilities compared to full catalog systems, no built-in schema enforcement (relies on Pydantic models), requires custom tooling for complex metadata operations, potential for manifest inconsistencies if not properly maintained

2. **AWS Glue Data Catalog + Athena Integration:** AWS-native catalog service with SQL query capabilities.
   * *Pros:* Native AWS integration, robust schema management with automatic evolution detection, SQL query interface for advanced analytics, built-in data lineage tracking, integrates with other AWS analytics services, handles schema enforcement automatically, excellent for complex cross-dataset queries
   * *Cons:* Significant cost increase (~$1-10/month for storage + query costs), adds operational complexity requiring Glue expertise, vendor lock-in to AWS ecosystem, heavier infrastructure not aligned with lightweight philosophy, requires Athena query optimization knowledge, potential latency impact for MCP server real-time queries

3. **Table-Format Catalogs (Delta Lake/Apache Iceberg/Apache Hudi):** Rich metadata embedded in table formats with transactional capabilities.
   * *Pros:* Advanced features including ACID transactions, time travel queries, automatic schema evolution, built-in data versioning, industry-standard approach for data lakes, excellent schema enforcement, sophisticated conflict resolution
   * *Cons:* Significant architectural change requiring new storage formats, high operational complexity for maintenance, steep learning curve for team, substantial dependency addition, over-engineered for current use cases, increased storage costs, complex integration with existing Parquet workflows

## Metadata Index Architecture

### S3 Manifest Structure
```
s3://hoopstat-haus-metadata/
├── catalogs/
│   ├── bronze_catalog.json      # Bronze layer datasets
│   ├── silver_catalog.json      # Silver layer datasets
│   ├── gold_catalog.json        # Gold layer datasets
│   └── lineage_graph.json       # Dataset dependencies
├── schemas/
│   ├── bronze/
│   │   ├── player_stats_v1.json
│   │   └── game_stats_v1.json
│   ├── silver/
│   │   └── player_daily_v2.json
│   └── gold/
│       └── player_season_summary_v1.json
└── partitions/
    ├── 2023-24/
    │   ├── player_manifest.json
    │   └── team_manifest.json
    └── 2024-25/
        └── player_manifest.json
```

### Catalog Manifest Format
```json
{
  "catalog_version": "1.0",
  "generated_at": "2024-01-22T10:30:00Z",
  "layer": "gold",
  "datasets": [
    {
      "dataset_id": "player_daily_stats",
      "table_name": "player_daily_stats",
      "description": "Daily player performance statistics",
      "schema_version": "v2",
      "schema_location": "s3://hoopstat-haus-metadata/schemas/gold/player_daily_v2.json",
      "partition_strategy": {
        "type": "hierarchical",
        "keys": ["season", "player_id", "date"],
        "pattern": "season={season}/player_id={player_id}/date={date}"
      },
      "s3_location": "s3://hoopstat-haus-gold/player_daily_stats/",
      "file_format": "parquet",
      "partitions": [
        {
          "partition_values": {"season": "2023-24", "player_id": "2544"},
          "location": "s3://hoopstat-haus-gold/player_daily_stats/season=2023-24/player_id=2544/",
          "file_count": 82,
          "total_size_mb": 45.2,
          "last_modified": "2024-01-22T09:15:00Z"
        }
      ],
      "lineage": {
        "upstream_datasets": ["silver.player_stats"],
        "downstream_datasets": ["gold.player_season_summaries"],
        "etl_job": "gold-player-daily-transform"
      },
      "quality_metrics": {
        "completeness": 0.98,
        "last_quality_check": "2024-01-22T08:00:00Z"
      }
    }
  ]
}
```

### hoopstat-data Integration

#### New Catalog Module
```python
# hoopstat_data/catalog.py
from typing import Dict, List, Optional
import json
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel

class DatasetMetadata(BaseModel):
    dataset_id: str
    table_name: str
    description: str
    schema_version: str
    schema_location: str
    s3_location: str
    file_format: str = "parquet"
    partition_strategy: Dict
    partitions: List[Dict]
    lineage: Dict
    quality_metrics: Optional[Dict] = None

class MetadataCatalog:
    """Lightweight metadata catalog for data discovery."""
    
    def __init__(self, s3_bucket: str = "hoopstat-haus-metadata"):
        self.s3_bucket = s3_bucket
        self._cache = {}
    
    def discover_datasets(self, layer: str = None) -> List[DatasetMetadata]:
        """Discover available datasets in specified layer."""
        
    def get_dataset_metadata(self, dataset_id: str) -> DatasetMetadata:
        """Get detailed metadata for specific dataset."""
        
    def find_partitions(self, dataset_id: str, **filters) -> List[Dict]:
        """Find partitions matching filter criteria."""
        
    def get_schema(self, dataset_id: str, version: str = "latest") -> Dict:
        """Retrieve dataset schema definition."""
        
    def register_dataset(self, metadata: DatasetMetadata):
        """Register new dataset in catalog."""
```

#### MCP Server Integration
```python
# Enhanced MCP server queries with catalog discovery
from hoopstat_data.catalog import MetadataCatalog

catalog = MetadataCatalog()

def get_player_stats(player_id: str, season: str) -> Dict:
    """Get player stats using catalog discovery."""
    # Discover available player datasets
    datasets = catalog.discover_datasets(layer="gold")
    player_datasets = [d for d in datasets if "player" in d.dataset_id]
    
    # Find optimal partition
    partitions = catalog.find_partitions(
        "player_daily_stats",
        season=season,
        player_id=player_id
    )
    
    # Load data using discovered S3 paths
    return load_parquet_from_partitions(partitions)
```

## Migration Strategy

### Phase 1: Core Infrastructure (Week 1-2)
- Implement `MetadataCatalog` class in `hoopstat-data`
- Create manifest generation utilities
- Design JSON schema for catalog manifests
- Set up S3 metadata bucket structure

### Phase 2: Bronze/Silver Integration (Week 3-4)
- Integrate catalog generation into existing ETL jobs
- Migrate partitioning utilities to use catalog discovery
- Update E2E testing framework for catalog-based discovery
- Implement schema version tracking

### Phase 3: Gold Layer and MCP Integration (Week 5-6)
- Enhance Gold layer ETL with catalog registration
- Update MCP server for catalog-based data discovery
- Implement lineage tracking across Bronze/Silver/Gold
- Add quality metrics to catalog manifests

### Phase 4: Optimization and Monitoring (Week 7-8)
- Implement catalog caching for performance
- Add CloudWatch metrics for catalog operations
- Create catalog health monitoring dashboards
- Document usage patterns and best practices

## Backward Compatibility

### Existing Code Preservation
- Current partitioning utilities remain functional
- S3 path generation logic preserved as fallback
- Pydantic models unchanged, extended with catalog metadata
- ETL jobs continue working without catalog initially

### Migration Path
```python
# Before: Direct S3 path construction
from hoopstat_data.partitioning import create_player_daily_partition

partition_key = create_player_daily_partition("2023-24", "2544", "2024-01-15")
s3_path = partition_key.s3_path

# After: Catalog-enhanced discovery (opt-in)
from hoopstat_data.catalog import MetadataCatalog

catalog = MetadataCatalog()
partitions = catalog.find_partitions(
    "player_daily_stats",
    season="2023-24",
    player_id="2544",
    date="2024-01-15"
)
s3_path = partitions[0]["location"]

# Hybrid approach during transition
try:
    s3_path = catalog.find_partitions(...)[0]["location"]
except (IndexError, CatalogNotAvailable):
    # Fallback to existing partitioning logic
    s3_path = create_player_daily_partition(...).s3_path
```

## Implementation Pilot Plan

### Success Criteria
- MCP server discovery queries complete in <50ms
- Catalog manifests update within 5 minutes of ETL completion
- Schema evolution detected and tracked automatically
- E2E tests discover data using catalog without hardcoded paths
- Storage cost increase <$2/month

### Pilot Scope
1. **Single Dataset Implementation**: Start with `player_daily_stats` in Gold layer
2. **MCP Server Integration**: Implement one catalog-based query endpoint
3. **E2E Test Migration**: Convert one test suite to catalog discovery
4. **Performance Validation**: Measure discovery latency and storage impact

### Monitoring and Success Metrics
- **Discovery Performance**: Track catalog query response times
- **Data Freshness**: Monitor lag between ETL completion and catalog updates
- **Schema Evolution**: Track schema version changes and compatibility
- **Cost Impact**: Monitor S3 storage and request costs
- **Developer Experience**: Survey team on catalog usability

### Risk Mitigation
- **Catalog Unavailability**: Fallback to existing partitioning logic
- **Performance Degradation**: Implement aggressive caching strategies
- **Manifest Corruption**: Version control manifests with checksums
- **Cost Overruns**: Implement automated cost monitoring and alerts

## Consequences

* **Positive:** Enables efficient data discovery for MCP server with sub-50ms response times, provides foundation for automated data lineage tracking across pipeline layers, supports schema evolution tracking without breaking existing consumers, integrates seamlessly with current S3+Parquet architecture, minimal operational overhead consistent with project philosophy, enables automated E2E testing without hardcoded S3 paths, provides human-readable data documentation for new developers, establishes foundation for future data governance capabilities.
* **Negative:** Requires manual integration work across existing ETL jobs, adds new dependency on catalog maintenance processes, potential for manifest inconsistencies if ETL jobs fail to update catalogs, limited advanced query capabilities compared to dedicated catalog systems, custom tooling required for complex metadata operations, initial development overhead to implement catalog infrastructure.
* **Future Implications:** All new ETL jobs must implement catalog registration, MCP server performance becomes dependent on catalog responsiveness, data discovery patterns shift from path-based to metadata-driven approaches, enables future migration to more sophisticated catalog systems if needed, establishes metadata standards for potential external integrations, creates foundation for data quality monitoring and governance tools.