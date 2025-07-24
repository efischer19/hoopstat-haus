"""
S3 utilities for the player daily aggregator Lambda.

This module provides S3 operations for reading Silver layer data
and writing Gold layer aggregations.
"""

import io
import logging

import boto3
import pandas as pd
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Client:
    """S3 client wrapper for data operations."""

    def __init__(self, region: str = "us-east-1"):
        """
        Initialize S3 client.

        Args:
            region: AWS region for S3 operations
        """
        self.s3_client = boto3.client("s3", region_name=region)
        self.region = region

    def read_parquet(self, bucket: str, key: str) -> pd.DataFrame:
        """
        Read a Parquet file from S3 into a pandas DataFrame.

        Args:
            bucket: S3 bucket name
            key: S3 object key

        Returns:
            pandas DataFrame with the data

        Raises:
            ClientError: If S3 operation fails
            Exception: If data reading fails
        """
        try:
            logger.info(f"Reading parquet file: s3://{bucket}/{key}")

            # Get object from S3
            response = self.s3_client.get_object(Bucket=bucket, Key=key)

            # Read parquet data
            parquet_bytes = response["Body"].read()
            df = pd.read_parquet(io.BytesIO(parquet_bytes))

            logger.info(f"Successfully read {len(df)} rows from s3://{bucket}/{key}")
            return df

        except ClientError as e:
            logger.error(f"S3 error reading s3://{bucket}/{key}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading parquet file s3://{bucket}/{key}: {e}")
            raise

    def write_parquet(self, df: pd.DataFrame, bucket: str, key: str) -> None:
        """
        Write a pandas DataFrame to S3 as a Parquet file.

        Args:
            df: pandas DataFrame to write
            bucket: S3 bucket name
            key: S3 object key

        Raises:
            ClientError: If S3 operation fails
            Exception: If data writing fails
        """
        try:
            logger.info(f"Writing {len(df)} rows to s3://{bucket}/{key}")

            # Convert DataFrame to Parquet bytes
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False, engine="pyarrow")
            buffer.seek(0)

            # Upload to S3
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=buffer.getvalue(),
                ContentType="application/octet-stream",
            )

            logger.info(f"Successfully wrote parquet file to s3://{bucket}/{key}")

        except ClientError as e:
            logger.error(f"S3 error writing s3://{bucket}/{key}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error writing parquet file s3://{bucket}/{key}: {e}")
            raise

    def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        """
        List objects in S3 bucket with given prefix.

        Args:
            bucket: S3 bucket name
            prefix: Object key prefix to filter by

        Returns:
            List of object keys

        Raises:
            ClientError: If S3 operation fails
        """
        try:
            logger.debug(f"Listing objects in s3://{bucket}/{prefix}")

            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

            keys = []
            for page in pages:
                for obj in page.get("Contents", []):
                    keys.append(obj["Key"])

            logger.debug(f"Found {len(keys)} objects with prefix {prefix}")
            return keys

        except ClientError as e:
            logger.error(f"S3 error listing objects in s3://{bucket}/{prefix}: {e}")
            raise

    def object_exists(self, bucket: str, key: str) -> bool:
        """
        Check if an object exists in S3.

        Args:
            bucket: S3 bucket name
            key: S3 object key

        Returns:
            True if object exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                logger.error(f"S3 error checking existence of s3://{bucket}/{key}: {e}")
                raise
