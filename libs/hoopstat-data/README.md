# Hoopstat Data Processing Utilities

Data processing utilities for basketball statistics - providing validation, transformation, and quality checking functionality for consistent data handling across Hoopstat Haus applications.

## Features

- **Data Validation**: Common validation functions for basketball statistics
- **Data Transformation**: Standard utilities for data transformation and processing  
- **Data Models**: Shared Pydantic models for basketball statistics
- **Quality Checking**: Data quality and consistency validation tools
- **Performance Optimized**: Utilities designed for efficient processing of large datasets

## Installation

This library is part of the Hoopstat Haus monorepo. For local development, install dependencies:

```bash
poetry install
```

## Usage

```python
from hoopstat_data.validation import validate_player_stats
from hoopstat_data.models import PlayerStats
from hoopstat_data.transforms import normalize_team_name
from hoopstat_data.quality import check_data_completeness

# Validate player statistics
stats_data = {"points": 25, "rebounds": 10, "assists": 5}
is_valid = validate_player_stats(stats_data)

# Use data models
player_stats = PlayerStats(player_id="12345", points=25, rebounds=10, assists=5)

# Transform data
normalized_name = normalize_team_name("Lakers")

# Check data quality
completeness = check_data_completeness(stats_data)
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
- `models.py`: Shared data models using Pydantic
- `quality.py`: Data quality checking tools

Each module follows the project's static-first design philosophy and emphasizes simplicity and performance.

## Contributing

Follow the project's development philosophy documented in `meta/DEVELOPMENT_PHILOSOPHY.md`. All changes should include tests and maintain backward compatibility.