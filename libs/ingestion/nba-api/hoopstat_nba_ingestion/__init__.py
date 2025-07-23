"""
Hoopstat NBA Ingestion Library

A library for ingesting NBA data from the nba-api, converting to Parquet format,
and uploading to S3 with proper partitioning and rate limiting.
"""

from .nba_client import NBAClient
from .parquet_converter import ParquetConverter
from .rate_limiter import RateLimiter
from .s3_uploader import S3Uploader

__version__ = "0.1.0"
__all__ = ["NBAClient", "ParquetConverter", "S3Uploader", "RateLimiter"]
