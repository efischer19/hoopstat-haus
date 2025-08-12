"""
Hoopstat S3 Library

A library for S3 storage and Parquet data processing for NBA data.
"""

from .parquet_converter import ParquetConversionError, ParquetConverter
from .s3_uploader import S3Uploader, S3UploadError

__version__ = "0.1.0"
__all__ = ["ParquetConverter", "ParquetConversionError", "S3Uploader", "S3UploadError"]
