# Hoopstat NBA Client

A shared library for NBA API interaction with rate limiting, error handling, and observability for Hoopstat Haus applications.

## Features

- **Rate-limited NBA API client** with adaptive behavior
- **Comprehensive error handling** with retry logic
- **Structured logging** integration with hoopstat-observability
- **Session statistics** for monitoring and debugging
- **Extensible design** for different NBA data types

## Usage

```python
from hoopstat_nba_client import NBAClient

# Initialize client with rate limiting
client = NBAClient(rate_limit_seconds=5.0, max_retries=3)

# Get season games
games = client.get_season_games("2024-25")

# Get box scores
traditional_stats = client.get_box_score_traditional("game_id")
advanced_stats = client.get_box_score_advanced("game_id")

# Get play-by-play data
pbp_data = client.get_play_by_play("game_id")

# Monitor session statistics
stats = client.get_session_stats()
print(f"Successful requests: {stats['successful_requests']}")
```

## Architecture

The library provides two main components:

### RateLimiter
- Token bucket rate limiting with configurable base delay
- Adaptive rate adjustment based on API response patterns
- Exponential backoff for rate limit violations
- Conservative approach to prevent API abuse

### NBAClient
- High-level interface for NBA API endpoints
- Automatic retries with exponential backoff for transient failures
- Comprehensive error logging and classification
- Session statistics tracking for observability

## Development

This library follows the Hoopstat Haus development philosophy and integrates with the existing observability infrastructure.

### Testing
```bash
poetry run pytest
```

### Linting
```bash
poetry run ruff check .
poetry run black --check .
```