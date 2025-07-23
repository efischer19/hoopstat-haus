# Mock NBA Data Generation Framework

A comprehensive mock data generation system for testing NBA data pipelines in the Hoopstat Haus project.

## Features

- **Realistic NBA Data Simulation**: Generate players, teams, games, and statistics with realistic distributions
- **Configurable Data Volume**: From small test sets to large-scale simulations
- **Deterministic Generation**: Seeded randomization for reproducible tests
- **Multiple Export Formats**: JSON (Bronze layer) and Parquet (Silver/Gold layers)
- **Schema Validation**: Utilities to ensure generated data meets expected schemas
- **CLI Interface**: Command-line tool for generating test datasets on demand

## Installation

```bash
cd libs/hoopstat-mock-data
poetry install
```

## Usage

### CLI Interface

```bash
# Generate a small test dataset
hoopstat-mock-data generate --teams 5 --players 50 --games 20 --output test_data.json

# Generate a large simulation dataset in Parquet format
hoopstat-mock-data generate --teams 30 --players 450 --games 1230 --output simulation_data.parquet --seed 42

# Generate specific season data
hoopstat-mock-data generate --season 2023-24 --output season_2023_24.json
```

### Python API

```python
from hoopstat_mock_data import MockDataGenerator

# Create generator with seed for reproducible results
generator = MockDataGenerator(seed=42)

# Generate teams
teams = generator.generate_teams(count=30)

# Generate players for those teams
players = generator.generate_players(teams=teams, count=450)

# Generate a season of games
games = generator.generate_games(teams=teams, season="2023-24")

# Export to different formats
generator.export_json(data, "output.json")
generator.export_parquet(data, "output.parquet")
```

## Data Models

The framework generates realistic NBA data following established schemas:

- **Teams**: NBA team information with cities, names, divisions, conferences
- **Players**: Player profiles with positions, attributes, and career stats
- **Games**: Regular season and playoff games with realistic schedules
- **Statistics**: Player and team statistics with realistic distributions

## Testing

```bash
poetry run pytest -v
```

## Development

The framework follows the Hoopstat Haus development philosophy:
- Simple, readable code
- Comprehensive test coverage
- Minimal dependencies
- Clear documentation