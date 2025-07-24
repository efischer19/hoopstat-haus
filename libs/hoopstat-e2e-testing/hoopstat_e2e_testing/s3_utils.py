"""
S3 testing utilities for Localstack integration.

Provides utilities for creating, reading, writing, and deleting S3 objects
and buckets during testing.
"""

import json
import logging
from datetime import datetime
from typing import Any

import boto3
import pandas as pd
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class S3TestUtils:
    """Utilities for S3 operations during testing with Localstack."""

    def __init__(
        self,
        endpoint_url: str | None = "http://localhost:4566",
        aws_access_key_id: str = "test",
        aws_secret_access_key: str = "test",
        region_name: str = "us-east-1",
    ):
        """
        Initialize S3 test utilities.

        Args:
            endpoint_url: Localstack endpoint URL (defaults to http://localhost:4566, 
                         set to None for moto or real AWS)
            aws_access_key_id: AWS access key for testing
            aws_secret_access_key: AWS secret access key for testing
            region_name: AWS region name
        """
        self.endpoint_url = endpoint_url
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name

        # Initialize S3 client
        if self.endpoint_url:
            # Use custom endpoint (e.g., Localstack)
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name,
            )
        else:
            # Use default AWS client (for moto or real AWS)
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name,
            )

        # Initialize S3 resource for higher-level operations
        self.s3_resource = boto3.resource(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
        )

    def create_bucket(self, bucket_name: str) -> bool:
        """
        Create an S3 bucket.

        Args:
            bucket_name: Name of the bucket to create

        Returns:
            True if bucket was created successfully, False otherwise
        """
        try:
            self.s3_client.create_bucket(Bucket=bucket_name)
            logger.info(f"Created bucket: {bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "BucketAlreadyOwnedByYou":
                logger.info(f"Bucket already exists: {bucket_name}")
                return True
            else:
                logger.error(f"Error creating bucket {bucket_name}: {e}")
                return False

    def delete_bucket(self, bucket_name: str, delete_objects: bool = True) -> bool:
        """
        Delete an S3 bucket.

        Args:
            bucket_name: Name of the bucket to delete
            delete_objects: Whether to delete all objects in the bucket first

        Returns:
            True if bucket was deleted successfully, False otherwise
        """
        try:
            if delete_objects:
                # Delete all objects in the bucket first
                bucket = self.s3_resource.Bucket(bucket_name)
                bucket.objects.all().delete()
                logger.info(f"Deleted all objects in bucket: {bucket_name}")

            self.s3_client.delete_bucket(Bucket=bucket_name)
            logger.info(f"Deleted bucket: {bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting bucket {bucket_name}: {e}")
            return False

    def bucket_exists(self, bucket_name: str) -> bool:
        """
        Check if a bucket exists.

        Args:
            bucket_name: Name of the bucket to check

        Returns:
            True if bucket exists, False otherwise
        """
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError:
            return False

    def put_object(
        self,
        bucket_name: str,
        key: str,
        data: str | bytes | dict[str, Any] | pd.DataFrame,
        content_type: str | None = None,
    ) -> bool:
        """
        Put an object in S3.

        Args:
            bucket_name: Name of the bucket
            key: Object key (path)
            data: Data to upload (string, bytes, dict, or DataFrame)
            content_type: Content type of the object

        Returns:
            True if object was uploaded successfully, False otherwise
        """
        try:
            # Convert data based on type
            if isinstance(data, dict):
                body = json.dumps(data, indent=2, cls=DateTimeEncoder)
                content_type = content_type or "application/json"
            elif isinstance(data, pd.DataFrame):
                # For DataFrames, save as Parquet
                import io

                buffer = io.BytesIO()
                data.to_parquet(buffer, index=False)
                body = buffer.getvalue()
                content_type = content_type or "application/octet-stream"
            elif isinstance(data, str):
                body = data.encode("utf-8")
                content_type = content_type or "text/plain"
            else:
                body = data
                content_type = content_type or "application/octet-stream"

            # Upload the object
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=body,
                ContentType=content_type,
            )
            logger.info(f"Uploaded object: s3://{bucket_name}/{key}")
            return True
        except Exception as e:
            logger.error(f"Error uploading object s3://{bucket_name}/{key}: {e}")
            return False

    def get_object(
        self, bucket_name: str, key: str, return_type: str = "string"
    ) -> str | bytes | dict[str, Any] | pd.DataFrame | None:
        """
        Get an object from S3.

        Args:
            bucket_name: Name of the bucket
            key: Object key (path)
            return_type: Type to return data as ('string', 'bytes', 'json', 'dataframe')

        Returns:
            Object data in the specified format, or None if error
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=key)
            body = response["Body"].read()

            if return_type == "bytes":
                return body
            elif return_type == "string":
                return body.decode("utf-8")
            elif return_type == "json":
                return json.loads(body.decode("utf-8"))
            elif return_type == "dataframe":
                import io

                return pd.read_parquet(io.BytesIO(body))
            else:
                raise ValueError(f"Unsupported return_type: {return_type}")

        except Exception as e:
            logger.error(f"Error getting object s3://{bucket_name}/{key}: {e}")
            return None

    def delete_object(self, bucket_name: str, key: str) -> bool:
        """
        Delete an object from S3.

        Args:
            bucket_name: Name of the bucket
            key: Object key (path)

        Returns:
            True if object was deleted successfully, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)
            logger.info(f"Deleted object: s3://{bucket_name}/{key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting object s3://{bucket_name}/{key}: {e}")
            return False

    def list_objects(self, bucket_name: str, prefix: str = "") -> list[dict[str, Any]]:
        """
        List objects in a bucket.

        Args:
            bucket_name: Name of the bucket
            prefix: Prefix to filter objects

        Returns:
            List of object information dictionaries
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            return response.get("Contents", [])
        except Exception as e:
            logger.error(f"Error listing objects in s3://{bucket_name}: {e}")
            return []

    def cleanup_test_buckets(self, prefix: str = "test-") -> None:
        """
        Clean up all test buckets with a given prefix.

        Args:
            prefix: Prefix to identify test buckets
        """
        try:
            response = self.s3_client.list_buckets()
            for bucket in response.get("Buckets", []):
                bucket_name = bucket["Name"]
                if bucket_name.startswith(prefix):
                    logger.info(f"Cleaning up test bucket: {bucket_name}")
                    self.delete_bucket(bucket_name, delete_objects=True)
        except Exception as e:
            logger.error(f"Error cleaning up test buckets: {e}")

    def setup_medallion_buckets(
        self, project_name: str = "test-hoopstat"
    ) -> dict[str, str]:
        """
        Set up bronze, silver, and gold buckets for medallion architecture testing.

        Args:
            project_name: Project name prefix for buckets

        Returns:
            Dictionary with bucket names for each layer
        """
        buckets = {
            "bronze": f"{project_name}-bronze",
            "silver": f"{project_name}-silver",
            "gold": f"{project_name}-gold",
        }

        for layer, bucket_name in buckets.items():
            if self.create_bucket(bucket_name):
                logger.info(f"Set up {layer} bucket: {bucket_name}")
            else:
                logger.error(f"Failed to set up {layer} bucket: {bucket_name}")

        return buckets
