"""
hoopstat-nba-api

NBA API access layer for fetching basketball statistics and game data.
"""

__version__ = "0.1.0"

# Public API exports
from .client import NBAAPIClient, NBAAPIError
from .games import GamesFetcher
from .players import PlayerStatsFetcher

__all__ = [
    "NBAAPIClient",
    "NBAAPIError",
    "GamesFetcher",
    "PlayerStatsFetcher",
]
