# Bronze Layer Summary Data

This document describes the bronze layer summary data feature that provides at-a-glance insights into the bronze layer contents and ingestion status.

## Overview

The bronze layer summary is a JSON file stored at a well-known S3 location that gets updated at the end of each daily ingestion run. It provides essential information about:

- How much data is in the bronze layer
- Which date was last fetched  
- When data was last refreshed
- Data quality metrics and success rates
- Per-entity breakdown of storage and processing status

## Architecture

### Summary File Location

The summary is stored at: `s3://{bronze-bucket}/_metadata/summary.json`

This location is:
- **Predictable**: Always at the same path for easy programmatic access
- **Human-readable**: JSON format for debugging and manual inspection
- **Lightweight**: Single file approach minimizing operational complexity

### Integration Points

1. **Ingestion Process**: Automatically generates summary at completion of each run
2. **S3 Storage**: Leverages existing S3 infrastructure  
3. **JSON Logging**: Integrates with ADR-015 structured logging
4. **Observability**: Supports ADR-018 CloudWatch monitoring

## Summary Data Structure

```json
{
  "summary_version": "1.0",
  "generated_at": "2024-01-15T14:30:22Z",
  "bronze_layer_stats": {
    "last_ingestion_date": "2024-01-15",
    "last_successful_run": "2024-01-15T14:30:22Z",
    "total_entities": 3,
    "entities": {
      "schedule": {
        "last_updated": "2024-01-15T14:30:22Z",
        "file_count": 1,
        "estimated_size_mb": 0.5,
        "last_processed_date": "2024-01-15"
      },
      "box_scores": {
        "last_updated": "2024-01-15T14:30:22Z", 
        "file_count": 12,
        "estimated_size_mb": 24.7,
        "last_processed_date": "2024-01-15"
      }
    },
    "data_quality": {
      "last_run_games_count": 12,
      "last_run_successful_box_scores": 12,
      "last_run_success_rate": 1.0,
      "last_quality_check": "2024-01-15T14:30:22Z"
    },
    "storage_info": {
      "total_files": 14,
      "estimated_size_mb": 27.3
    }
  }
}
```

### Field Descriptions

| Field | Description |
|-------|-------------|
| `summary_version` | Schema version for compatibility |
| `generated_at` | ISO timestamp when summary was generated |
| `last_ingestion_date` | Date that was processed in the last run |
| `last_successful_run` | ISO timestamp of last successful ingestion |
| `total_entities` | Number of data entity types in bronze layer |
| `entities.*` | Per-entity statistics (files, size, timestamps) |
| `data_quality.*` | Quality metrics from the last ingestion run |
| `storage_info.*` | Aggregate storage statistics |

## Use Cases

### 1. Operations Monitoring

**Question**: "Has our daily ingestion run successfully?"

**Answer**: Check `last_successful_run` timestamp and `last_ingestion_date`

```bash
# Quick check via AWS CLI
aws s3 cp s3://hoopstat-haus-bronze/_metadata/summary.json - | jq '.bronze_layer_stats.last_successful_run'
```

### 2. Data Volume Tracking  

**Question**: "How much data do we have in the bronze layer?"

**Answer**: Check `storage_info` and per-entity `file_count`

```json
{
  "storage_info": {
    "total_files": 14,
    "estimated_size_mb": 27.3
  }
}
```

### 3. Data Quality Assessment

**Question**: "Are we successfully processing all games?"

**Answer**: Check `data_quality.last_run_success_rate`

```json
{
  "data_quality": {
    "last_run_success_rate": 0.95,
    "last_run_games_count": 12,
    "last_run_successful_box_scores": 11
  }
}
```

### 4. Entity-Level Analysis

**Question**: "Which entities have the most recent data?"

**Answer**: Compare `last_processed_date` across entities

## Implementation Details

### BronzeSummaryManager Class

The `BronzeSummaryManager` class handles summary generation:

```python
from app.bronze_summary import BronzeSummaryManager

# Initialize with existing S3 manager
summary_manager = BronzeSummaryManager(s3_manager)

# Generate and store summary
summary_manager.update_bronze_summary(
    target_date=date(2024, 1, 15),
    games_count=12,
    successful_box_scores=11
)
```

### Integration with Ingestion

The summary is automatically generated at the end of each ingestion run:

```python
# In DateScopedIngestion.run()
if not dry_run:
    self.summary_manager.update_bronze_summary(
        target_date, len(games), successful_box_scores
    )
```

### Error Handling

- **Graceful Degradation**: Summary generation failures don't fail the ingestion
- **Empty Statistics**: Returns valid summary even when S3 queries fail
- **Logging**: All operations logged with structured data per ADR-015

## Future Enhancements

### Potential Extensions

1. **Historical Tracking**: Store daily summaries for trend analysis
2. **CloudWatch Integration**: Create custom metrics from summary data  
3. **Alerting**: Monitor summary metrics for operational alerts
4. **Metadata Catalog**: Integration with ADR-024 metadata catalog approach

### Compatibility

The approach is designed to be:
- **Forward Compatible**: Summary schema can evolve with versioning
- **Extensible**: Easy to add new metrics or entities
- **Catalog Ready**: Can integrate with future metadata catalog implementations

## Conclusion

The bronze layer summary provides a simple, effective solution for gaining insights into bronze layer data:

✅ **Solves Core Requirements**: Provides data volume, last fetch date, and refresh status  
✅ **Minimal Complexity**: Leverages existing S3 and JSON infrastructure  
✅ **Human Readable**: JSON format for debugging and manual inspection  
✅ **Operationally Friendly**: Single file at predictable location  
✅ **Extensible**: Can grow with future requirements