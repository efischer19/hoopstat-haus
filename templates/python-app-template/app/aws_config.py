"""
AWS Configuration utilities for Hoopstat Haus applications.

This module provides a standardized way for applications to discover and connect
to AWS resources using environment variables and configuration files.

See ADR-017 for the configuration strategy.
"""

import os
from typing import Optional, Dict, Any
import boto3
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class AWSConfig(BaseSettings):
    """
    AWS configuration settings loaded from environment variables.
    
    This class follows the twelve-factor app pattern for configuration
    and provides a structured way to access AWS resource information.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    # AWS Region
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    
    # S3 Bucket configurations  
    s3_bucket_raw_data: str = Field(alias="AWS_S3_BUCKET_RAW_DATA")
    s3_bucket_processed_data: str = Field(alias="AWS_S3_BUCKET_PROCESSED_DATA")
    s3_bucket_backup: str = Field(alias="AWS_S3_BUCKET_BACKUP")
    
    # ECR Repository
    ecr_repository: Optional[str] = Field(default=None, alias="AWS_ECR_REPOSITORY")


class AWSClientManager:
    """
    Manages AWS service clients with consistent configuration.
    
    This class provides a centralized way to create and cache AWS service clients
    with the correct region and configuration.
    """
    
    def __init__(self, config: Optional[AWSConfig] = None):
        self.config = config or AWSConfig()
        self._clients: Dict[str, Any] = {}
    
    def get_s3_client(self):
        """Get an S3 client configured for the project region."""
        if "s3" not in self._clients:
            self._clients["s3"] = boto3.client("s3", region_name=self.config.aws_region)
        return self._clients["s3"]
    
    def get_ecr_client(self):
        """Get an ECR client configured for the project region."""
        if "ecr" not in self._clients:
            self._clients["ecr"] = boto3.client("ecr", region_name=self.config.aws_region)
        return self._clients["ecr"]


class S3DataManager:
    """
    High-level interface for S3 data operations.
    
    This class provides convenient methods for common S3 operations
    following the project's data storage patterns.
    """
    
    def __init__(self, client_manager: Optional[AWSClientManager] = None):
        self.client_manager = client_manager or AWSClientManager()
        self.config = self.client_manager.config
        self.s3_client = self.client_manager.get_s3_client()
    
    def upload_raw_data(self, key: str, data: bytes, content_type: str = "application/json"):
        """Upload raw data to the raw data bucket."""
        return self.s3_client.put_object(
            Bucket=self.config.s3_bucket_raw_data,
            Key=key,
            Body=data,
            ContentType=content_type
        )
    
    def download_raw_data(self, key: str) -> bytes:
        """Download raw data from the raw data bucket."""
        response = self.s3_client.get_object(
            Bucket=self.config.s3_bucket_raw_data,
            Key=key
        )
        return response["Body"].read()
    
    def upload_processed_data(self, key: str, data: bytes, content_type: str = "application/json"):
        """Upload processed data to the processed data bucket."""
        return self.s3_client.put_object(
            Bucket=self.config.s3_bucket_processed_data,
            Key=key,
            Body=data,
            ContentType=content_type
        )
    
    def download_processed_data(self, key: str) -> bytes:
        """Download processed data from the processed data bucket."""
        response = self.s3_client.get_object(
            Bucket=self.config.s3_bucket_processed_data,
            Key=key
        )
        return response["Body"].read()
    
    def backup_data(self, key: str, data: bytes, content_type: str = "application/json"):
        """Upload data to the backup bucket."""
        return self.s3_client.put_object(
            Bucket=self.config.s3_bucket_backup,
            Key=key,
            Body=data,
            ContentType=content_type
        )
    
    def list_objects(self, bucket_type: str, prefix: str = "") -> list:
        """
        List objects in a bucket by type.
        
        Args:
            bucket_type: One of 'raw', 'processed', or 'backup'
            prefix: Optional prefix to filter objects
            
        Returns:
            List of object metadata dictionaries
        """
        bucket_map = {
            "raw": self.config.s3_bucket_raw_data,
            "processed": self.config.s3_bucket_processed_data,
            "backup": self.config.s3_bucket_backup
        }
        
        if bucket_type not in bucket_map:
            raise ValueError(f"Invalid bucket_type: {bucket_type}. Must be one of: {list(bucket_map.keys())}")
        
        bucket_name = bucket_map[bucket_type]
        response = self.s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        return response.get("Contents", [])


def get_aws_config() -> AWSConfig:
    """
    Get AWS configuration for the current environment.
    
    This is the recommended way to get AWS configuration in applications.
    """
    return AWSConfig()


def verify_aws_configuration() -> bool:
    """
    Verify that AWS configuration is valid and accessible.
    
    Returns:
        True if configuration is valid and AWS resources are accessible
    """
    try:
        config = get_aws_config()
        client_manager = AWSClientManager(config)
        s3_client = client_manager.get_s3_client()
        
        # Test S3 access by listing buckets
        s3_client.list_objects_v2(Bucket=config.s3_bucket_raw_data, MaxKeys=1)
        
        return True
    except Exception as e:
        print(f"AWS configuration verification failed: {e}")
        return False


if __name__ == "__main__":
    # Simple CLI for testing AWS configuration
    import sys
    
    print("🔍 Verifying AWS configuration...")
    
    try:
        config = get_aws_config()
        print(f"✅ AWS Region: {config.aws_region}")
        print(f"✅ Raw Data Bucket: {config.s3_bucket_raw_data}")
        print(f"✅ Processed Data Bucket: {config.s3_bucket_processed_data}")
        print(f"✅ Backup Bucket: {config.s3_bucket_backup}")
        
        if config.ecr_repository:
            print(f"✅ ECR Repository: {config.ecr_repository}")
        
        if verify_aws_configuration():
            print("🎉 AWS configuration is valid and accessible!")
            sys.exit(0)
        else:
            print("❌ AWS configuration verification failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error loading AWS configuration: {e}")
        sys.exit(1)