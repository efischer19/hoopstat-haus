"""
Hoopstat NBA API Library

A library for accessing NBA data from the nba-api with rate limiting and error handling.
"""

from .nba_client import NBAAPIError, NBAClient
from .rate_limiter import RateLimiter

__version__ = "0.1.0"
__all__ = ["NBAClient", "NBAAPIError", "RateLimiter"]
