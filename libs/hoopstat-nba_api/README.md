# Hoopstat NBA API Library

A Python library for accessing NBA data from the nba-api with respectful rate limiting and error handling.

## Features

- **NBA API Client**: Respectful rate-limited client for fetching NBA data
- **Rate Limiting**: Built-in protection against API abuse with exponential backoff
- **Error Handling**: Comprehensive error logging and retry logic

## Architecture

This library follows the architectural decisions:
- **ADR-013**: Uses nba-api as the primary NBA data source

## Usage

```python
from hoopstat_nba_api import NBAClient, RateLimiter
from datetime import date

# Initialize client with default rate limiter
client = NBAClient()

# Or with custom rate limiter
rate_limiter = RateLimiter(min_delay=2.0, max_delay=120.0)
client = NBAClient(rate_limiter=rate_limiter)

# Fetch NBA data
game_data = client.get_games_for_date(date(2024, 1, 15))
player_info = client.get_player_info("2544")  # LeBron James
standings = client.get_league_standings("2023-24")
```

## Installation

This library is designed to be used as a shared dependency within the hoopstat-haus monorepo.

## Development

```bash
poetry install
poetry run pytest
poetry run ruff check .
poetry run ruff format .
```

## Rate Limiting

The client includes respectful rate limiting by default:
- Minimum delay: 1.0 seconds between requests
- Maximum delay: 60.0 seconds 
- Exponential backoff on failures
- Maximum retries: 5

This ensures we're being respectful to the NBA API and avoiding rate limit issues.