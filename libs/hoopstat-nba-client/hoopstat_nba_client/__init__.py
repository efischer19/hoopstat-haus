"""
Hoopstat NBA Client Library

A shared library for NBA API interaction with rate limiting, error handling,
and observability for Hoopstat Haus applications.
"""

from .client import NBAClient
from .rate_limiter import RateLimiter

__version__ = "0.1.0"
__all__ = ["NBAClient", "RateLimiter"]