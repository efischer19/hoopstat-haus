# Data Validation and Quality Checks

This document describes the data validation and quality checks implemented in the bronze layer ingestion pipeline.

## Overview

The bronze layer ingestion pipeline now includes comprehensive data validation and quality checks that ensure only high-quality data is stored and processed. Invalid data is automatically quarantined for manual review.

## Features

### 1. JSON Schema Validation

All NBA API responses are validated against predefined JSON schemas to ensure they match expected structure and data types.

**Schemas Implemented:**
- **Schedule Schema**: Validates game schedule data from `LeagueGameFinder` endpoint (legacy format)
- **Box Score Schema**: Validates box score data supporting both:
  - **V3 Format** (`BoxScoreTraditionalV3`): Uses `boxScoreTraditional` root key with `homeTeam` and `awayTeam` objects
  - **Legacy Format**: Uses `resultSets` array structure

**Key Validations:**
- Required fields presence
- Data type validation (strings, integers, arrays)
- Field format validation (game IDs, dates)
- Reasonable value ranges for statistics
- Team and player structure validation for V3 format

### 2. Data Completeness Checks

The system validates that ingested data is complete and meets expectations:

- **Game Count Validation**: Ensures expected number of games for the date
- **Player Data Completeness**: Validates all required player statistics are present
- **Data Freshness**: Ensures ingested data is for the correct date range

### 3. Data Quality Metrics

Comprehensive quality scoring using the `hoopstat-data` library:

- **Completeness Score**: Percentage of required fields present
- **Validity Score**: Percentage of fields with valid values and ranges
- **Consistency Score**: Internal consistency of related statistics
- **Overall Quality Score**: Weighted average of all quality factors

### 4. Data Quarantine System

Invalid data is automatically quarantined instead of being discarded:

**Quarantine Structure:**
```
s3://bronze-bucket/quarantine/
├── year=2024/month=01/day=15/
│   ├── schedule/
│   │   └── quarantine_20240115_043022_123456.json
│   └── box_score/
│       └── quarantine_20240115_043055_789012.json
```

**Quarantine Triggers:**
- Schema validation failures
- Critical data quality issues
- Date consistency problems
- Missing required fields

## Implementation Details

### DataValidator Class

The `DataValidator` class provides the main validation functionality:

```python
from app.validation import DataValidator

validator = DataValidator()

# Validate API response
result = validator.validate_api_response(
    response_data=raw_api_data,
    response_type="schedule",
    context={"target_date": date(2024, 1, 15)}
)

# Check completeness
completeness = validator.validate_completeness(
    data=games_list,
    expected_count=10,
    context="daily_games"
)
```

### DataQuarantine Class

The `DataQuarantine` class manages quarantining of invalid data:

```python
from app.quarantine import DataQuarantine

quarantine = DataQuarantine(s3_manager)

# Quarantine invalid data
quarantine_key = quarantine.quarantine_data(
    data=invalid_data,
    validation_result=validation_result,
    data_type="schedule",
    target_date=date(2024, 1, 15)
)

# List quarantined items
items = quarantine.list_quarantined_data(
    target_date=date(2024, 1, 15),
    data_type="schedule"
)
```

## Configuration

No additional configuration is required. The validation system uses:

- Built-in JSON schemas for NBA API responses
- Default quality thresholds from `hoopstat-data` library
- Automatic quarantine decisions based on validation results

## Monitoring and Observability

### Quality Metrics Logging

All validation results are logged with structured data for monitoring:

```json
{
  "timestamp": "2024-01-15T04:30:22Z",
  "level": "INFO",
  "message": "Validation completed for schedule",
  "extra": {
    "validation_result": true,
    "issue_count": 0,
    "metrics": {
      "schema_valid": true,
      "game_count": 12,
      "date_consistency": true,
      "valid_games": 12,
      "game_validity_ratio": 1.0
    },
    "response_type": "schedule"
  }
}
```

### Quarantine Monitoring

Quarantined data is logged for alerting and investigation:

```json
{
  "timestamp": "2024-01-15T04:30:25Z",
  "level": "WARNING",
  "message": "Data quarantined: schedule for 2024-01-15",
  "extra": {
    "quarantine_key": "quarantine/year=2024/month=01/day=15/schedule/quarantine_20240115_043025_123456.json",
    "data_type": "schedule",
    "target_date": "2024-01-15",
    "issues_count": 2,
    "validation_issues": [
      "Schema validation failed: 'TEAM_ID' is a required property",
      "Date inconsistencies found: ['2024-01-16']"
    ]
  }
}
```

## Integration with Existing Flow

The validation system is seamlessly integrated into the existing ingestion flow:

1. **Fetch Data**: NBA API data is fetched as before
2. **Validate**: New validation step checks data quality
3. **Quarantine**: Invalid data is quarantined automatically
4. **Continue**: Valid data continues through normal ingestion flow
5. **Log Metrics**: Quality metrics are logged for monitoring

The ingestion pipeline continues to work normally, but now with enhanced data quality assurance.

## Error Handling

The validation system is designed to be resilient:

- **Validation Failures**: Data is quarantined but pipeline continues
- **Schema Errors**: Graceful degradation with logging
- **S3 Quarantine Failures**: Logged but don't stop ingestion
- **Quality Calculation Errors**: Default to conservative quality scores

## Future Enhancements

Potential future improvements:

1. **Dynamic Schemas**: Update schemas based on NBA API changes
2. **Machine Learning Quality**: ML-based quality anomaly detection
3. **Historical Quality Trends**: Track quality metrics over time
4. **Automated Quality Alerts**: Integration with monitoring systems
5. **Quality-Based Retry Logic**: Retry ingestion for borderline quality data