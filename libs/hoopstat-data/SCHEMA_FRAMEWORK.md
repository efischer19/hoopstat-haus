# Pydantic Schema Validation Framework

This document describes the comprehensive Pydantic schema validation framework implemented for the Bronze-to-Silver ETL pipeline in the Hoopstat Haus project.

## Overview

The schema validation framework provides:

- **Pydantic v2 models** for all Silver layer entities (players, teams, games, statistics)
- **Schema versioning and evolution** support for backward compatibility
- **Validation strictness levels** (strict/lenient modes) for different data quality scenarios
- **Data lineage tracking** for audit trails and metadata management
- **NBA-specific business rule validation** for domain integrity
- **JSON schema generation** for documentation and external validation

## Core Components

### Data Lineage

All Silver layer models include data lineage tracking:

```python
from hoopstat_data.models import DataLineage, ValidationMode

lineage = DataLineage(
    source_system="nba_api",
    schema_version="1.0.0", 
    transformation_stage="silver",
    validation_mode=ValidationMode.STRICT
)
```

### Validation Modes

Two validation strictness levels are supported:

- **STRICT**: Enforces all NBA business rules and data constraints
- **LENIENT**: Allows data inconsistencies for dirty data ingestion scenarios

```python
# Strict validation (default)
player = PlayerStats(
    validation_mode=ValidationMode.STRICT,
    player_id="player_001",
    points=25,  # Will reject > 100 points
    # ... other fields
)

# Lenient validation
player = PlayerStats(
    validation_mode=ValidationMode.LENIENT,
    player_id="player_001", 
    points=150,  # Allows unrealistic values
    # ... other fields
)
```

### Silver Layer Models

#### PlayerStats
Statistics for individual player performance:

```python
player = PlayerStats(
    player_id="player_001",
    player_name="LeBron James",
    points=25,
    rebounds=8,
    assists=7,
    steals=2,
    blocks=1,
    turnovers=3,
    field_goals_made=10,
    field_goals_attempted=15,
    minutes_played=35.5
)
```

**NBA-Specific Validations:**
- Points cannot exceed 100 in strict mode (Wilt Chamberlain record)
- Field goals made ≤ attempted
- Three-pointers made ≤ attempted  
- Free throws made ≤ attempted
- Player names cannot be empty strings

#### TeamStats
Team-level aggregated statistics:

```python
team = TeamStats(
    team_id="lakers_001",
    team_name="Los Angeles Lakers",
    points=112,
    field_goals_made=42,
    field_goals_attempted=88,
    rebounds=45,
    assists=28
)
```

**NBA-Specific Validations:**
- Team names cannot be empty
- Points between 60-200 in strict mode
- All shooting statistics must have made ≤ attempted

#### GameStats
Game-level metadata and results:

```python
game = GameStats(
    game_id="game_20241215_lal_bos",
    home_team_id="lakers",
    away_team_id="celtics", 
    home_score=112,
    away_score=108,
    season="2024-25",
    game_date="2024-12-15T20:00:00Z",
    quarters=4
)
```

**NBA-Specific Validations:**
- Teams cannot play themselves
- Games cannot end in ties (strict mode)
- Overtime games must have 5+ quarters
- Season format must be YYYY-YY pattern
- Game dates must be ISO format

## Schema Evolution

The framework supports schema versioning and evolution:

```python
from hoopstat_data.models import SchemaEvolution, get_schema_version

# Current version
current_version = get_schema_version()  # "1.0.0"

# Migrate old data format
old_data = {"player_id": "legacy_001", "points": 25}
migrated_data = SchemaEvolution.migrate_from_version(
    old_data, 
    from_version="0.1.0",
    to_version="1.0.0"
)
# Automatically adds lineage metadata
```

## JSON Schema Generation

Generate JSON schemas for external validation and documentation:

```python
from hoopstat_data.models import generate_json_schema, PlayerStats

schema = generate_json_schema(PlayerStats)

# Save for external use
import json
with open('player_stats_schema.json', 'w') as f:
    json.dump(schema, f, indent=2)
```

## Backward Compatibility

The framework maintains backward compatibility with existing code:

```python
# Legacy usage - lineage auto-generated
player = PlayerStats(
    player_id="legacy_player",
    points=25,
    rebounds=8,
    assists=5,
    # ... other required fields
)

# Auto-generated lineage
assert player.lineage.source_system == "unknown"
assert player.lineage.schema_version == get_schema_version()
```

## Performance Features

- **Pydantic v2** with performance optimizations
- **String stripping** for input data cleaning
- **Assignment validation** for runtime safety
- **Extra field rejection** for data integrity
- **Comprehensive error messages** with field context

## Usage Examples

See `demo_schema_framework.py` for comprehensive usage examples demonstrating all features.

## Testing

The framework includes 25+ comprehensive tests covering:

- Data lineage functionality
- Validation mode behaviors  
- NBA-specific business rules
- JSON schema generation
- Schema evolution capabilities
- Performance and error messaging

Run tests with:
```bash
poetry run pytest tests/test_schema_framework.py -v
```

## Integration

The schema framework integrates with:

- **NBA API data source** (ADR-013) for official statistics
- **Parquet storage format** (ADR-014) for efficient data serialization
- **Existing validation functions** for backward compatibility
- **ETL pipeline stages** for Bronze-to-Silver transformations