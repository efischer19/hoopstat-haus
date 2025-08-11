"""
Hoopstat NBA Ingestion Library

A library for ingesting NBA data from the nba-api, converting to Parquet format,
and uploading to S3 with proper partitioning and rate limiting.
"""

try:
    from .nba_client import NBAClient
except ImportError:
    NBAClient = None

try:
    from .parquet_converter import ParquetConverter
except ImportError:
    ParquetConverter = None

try:
    from .rate_limiter import RateLimiter
except ImportError:
    RateLimiter = None

try:
    from .s3_uploader import S3Uploader
except ImportError:
    S3Uploader = None

try:
    from .s3_parquet_client import S3ParquetClient
except ImportError:
    S3ParquetClient = None

try:
    from .bronze_nba_client import NBAAPIClient
except ImportError:
    NBAAPIClient = None

__version__ = "0.1.0"
__all__ = ["NBAClient", "ParquetConverter", "S3Uploader", "S3ParquetClient", "RateLimiter", "NBAAPIClient"]
