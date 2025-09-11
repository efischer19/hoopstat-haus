"""
Hoopstat S3 Library

A library for S3 storage and data processing for NBA data.
Supports both Parquet (for production) and JSON (for MVP) formats.
"""

from .parquet_converter import ParquetConversionError, ParquetConverter
from .s3_uploader import S3Uploader, S3UploadError
from .silver_s3_manager import SilverS3Manager, SilverS3ManagerError

__version__ = "0.1.0"
__all__ = [
    "ParquetConverter",
    "ParquetConversionError",
    "S3Uploader",
    "S3UploadError",
    "SilverS3Manager",
    "SilverS3ManagerError",
]
