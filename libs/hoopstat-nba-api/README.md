# hoopstat-nba-api

NBA API access layer for fetching basketball statistics and game data.

## Overview

This shared library provides a consistent interface for accessing NBA data through the nba-api package. It includes utilities for fetching games, player statistics, team information, and other basketball-related data needed across Hoopstat Haus applications.

## Features

- **Game Data**: Fetch game schedules, scores, and details
- **Player Statistics**: Access player performance data and career stats  
- **Team Information**: Get team rosters, standings, and team-level statistics
- **Date-based Queries**: Efficient filtering by date ranges
- **Error Handling**: Robust error handling for API failures and rate limiting
- **Data Validation**: Structured data models for type safety

## Usage

```python
from hoopstat_nba_api import NBAAPIClient, GamesFetcher, PlayerStatsFetcher

# Initialize the client
client = NBAAPIClient()

# Fetch games for a specific date
games_fetcher = GamesFetcher(client)
games_data = games_fetcher.fetch_games_by_date("2025-01-15")

# Fetch player statistics
stats_fetcher = PlayerStatsFetcher(client)
player_stats = stats_fetcher.fetch_player_stats("2025-01-15")
```

## Installation

This library is part of the Hoopstat Haus monorepo and is installed automatically when used as a dependency in other applications.

## Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run ruff check .
```

## Versioning

This library follows [Semantic Versioning (SemVer)](https://semver.org/) as defined in ADR-016.