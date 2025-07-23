"""
NBA API client with rate limiting and error handling.

This module now serves as a thin wrapper around the shared hoopstat-nba-client
library, maintaining backward compatibility while leveraging the reusable
NBA API client functionality.
"""

from typing import Any

from hoopstat_nba_client import NBAClient as SharedNBAClient

# Re-export the shared client for backward compatibility
NBAClient = SharedNBAClient
