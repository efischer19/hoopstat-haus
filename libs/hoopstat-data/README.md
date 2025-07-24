# Hoopstat Data Processing Utilities

Data processing utilities for basketball statistics - providing validation, transformation, and quality checking functionality for consistent data handling across Hoopstat Haus applications.

## Features

- **Data Validation**: Common validation functions for basketball statistics
- **Data Transformation**: Standard utilities for data transformation and processing  
- **Data Models**: Shared Pydantic models for basketball statistics (Silver and Gold layers)
- **Quality Checking**: Data quality and consistency validation tools
- **Gold Layer Partitioning**: Optimized S3 partitioning strategy for fast MCP server queries
- **Performance Optimized**: Utilities designed for efficient processing of large datasets

## Installation

This library is part of the Hoopstat Haus monorepo. For local development, install dependencies:

```bash
poetry install
```

## Usage

```python
from hoopstat_data.validation import validate_player_stats
from hoopstat_data.models import PlayerStats, GoldPlayerDailyStats
from hoopstat_data.transforms import normalize_team_name
from hoopstat_data.quality import check_data_completeness
from hoopstat_data.partitioning import create_player_daily_partition

# Validate player statistics
stats_data = {"points": 25, "rebounds": 10, "assists": 5}
is_valid = validate_player_stats(stats_data)

# Use Silver layer data models
player_stats = PlayerStats(player_id="12345", points=25, rebounds=10, assists=5)

# Use Gold layer models with computed metrics
gold_stats = GoldPlayerDailyStats(
    player_id="12345", 
    points=25, 
    rebounds=10, 
    assists=5,
    efficiency_rating=1.15,
    season="2023-24"
)

# Transform data
normalized_name = normalize_team_name("Lakers")

# Check data quality
completeness = check_data_completeness(stats_data)

# Create optimized S3 partition keys
partition_key = create_player_daily_partition(
    season="2023-24",
    player_id="12345",
    date="2024-01-15"
)
print(partition_key.s3_path)
# s3://hoopstat-haus-gold/player_daily_stats/season=2023-24/player_id=12345/date=2024-01-15/stats.parquet
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Quality

```bash
poetry run ruff check .
poetry run black --check .
```

## Architecture

The library is organized into focused modules:

- `validation.py`: Data validation functions
- `transforms.py`: Data transformation utilities
- `models.py`: Shared data models using Pydantic (Silver and Gold layers)
- `quality.py`: Data quality checking tools
- `partitioning.py`: Gold layer S3 partitioning strategy and optimization utilities

Each module follows the project's static-first design philosophy and emphasizes simplicity and performance.

## Gold Layer Partitioning

This library implements the Gold layer data partitioning strategy defined in ADR-020. See [PARTITIONING_GUIDE.md](./PARTITIONING_GUIDE.md) for detailed usage examples.

## Contributing

Follow the project's development philosophy documented in `meta/DEVELOPMENT_PHILOSOPHY.md`. All changes should include tests and maintain backward compatibility.