"""
Tests for AWS configuration and integration functionality.

These tests demonstrate how to test AWS integration in Hoopstat Haus applications.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import json
from app.aws_config import AWSConfig, AWSClientManager, S3DataManager, verify_aws_configuration


class TestAWSConfig:
    """Test AWS configuration loading and validation."""
    
    def test_aws_config_default_values(self):
        """Test that AWS config loads with default values."""
        with patch.dict(os.environ, {}, clear=True):
            # Should raise validation error for required fields
            with pytest.raises(Exception):
                AWSConfig()
    
    def test_aws_config_from_environment(self):
        """Test AWS config loading from environment variables."""
        env_vars = {
            "AWS_REGION": "us-west-2",
            "AWS_S3_BUCKET_RAW_DATA": "test-raw-bucket",
            "AWS_S3_BUCKET_PROCESSED_DATA": "test-processed-bucket",
            "AWS_S3_BUCKET_BACKUP": "test-backup-bucket",
            "AWS_ECR_REPOSITORY": "123456789.dkr.ecr.us-west-2.amazonaws.com/test/app"
        }
        
        with patch.dict(os.environ, env_vars):
            config = AWSConfig()
            
            assert config.aws_region == "us-west-2"
            assert config.s3_bucket_raw_data == "test-raw-bucket"
            assert config.s3_bucket_processed_data == "test-processed-bucket"
            assert config.s3_bucket_backup == "test-backup-bucket"
            assert config.ecr_repository == "123456789.dkr.ecr.us-west-2.amazonaws.com/test/app"


class TestAWSClientManager:
    """Test AWS client management functionality."""
    
    @patch('boto3.client')
    def test_get_s3_client(self, mock_boto3_client):
        """Test S3 client creation and caching."""
        # Setup
        mock_s3_client = Mock()
        mock_boto3_client.return_value = mock_s3_client
        
        env_vars = {
            "AWS_REGION": "us-east-1",
            "AWS_S3_BUCKET_RAW_DATA": "test-bucket",
            "AWS_S3_BUCKET_PROCESSED_DATA": "test-bucket-2",
            "AWS_S3_BUCKET_BACKUP": "test-bucket-3"
        }
        
        with patch.dict(os.environ, env_vars):
            config = AWSConfig()
            client_manager = AWSClientManager(config)
            
            # First call should create client
            s3_client_1 = client_manager.get_s3_client()
            mock_boto3_client.assert_called_once_with("s3", region_name="us-east-1")
            
            # Second call should return cached client
            s3_client_2 = client_manager.get_s3_client()
            assert s3_client_1 is s3_client_2
            assert mock_boto3_client.call_count == 1
    
    @patch('boto3.client')
    def test_get_ecr_client(self, mock_boto3_client):
        """Test ECR client creation."""
        mock_ecr_client = Mock()
        mock_boto3_client.return_value = mock_ecr_client
        
        env_vars = {
            "AWS_REGION": "us-east-1",
            "AWS_S3_BUCKET_RAW_DATA": "test-bucket",
            "AWS_S3_BUCKET_PROCESSED_DATA": "test-bucket-2",
            "AWS_S3_BUCKET_BACKUP": "test-bucket-3"
        }
        
        with patch.dict(os.environ, env_vars):
            config = AWSConfig()
            client_manager = AWSClientManager(config)
            
            ecr_client = client_manager.get_ecr_client()
            mock_boto3_client.assert_called_once_with("ecr", region_name="us-east-1")


class TestS3DataManager:
    """Test S3 data management functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.env_vars = {
            "AWS_REGION": "us-east-1",
            "AWS_S3_BUCKET_RAW_DATA": "test-raw-bucket",
            "AWS_S3_BUCKET_PROCESSED_DATA": "test-processed-bucket",
            "AWS_S3_BUCKET_BACKUP": "test-backup-bucket"
        }
    
    @patch('boto3.client')
    def test_upload_raw_data(self, mock_boto3_client):
        """Test uploading data to raw data bucket."""
        mock_s3_client = Mock()
        mock_boto3_client.return_value = mock_s3_client
        
        with patch.dict(os.environ, self.env_vars):
            s3_manager = S3DataManager()
            
            test_data = b'{"test": "data"}'
            test_key = "test/file.json"
            
            s3_manager.upload_raw_data(test_key, test_data)
            
            mock_s3_client.put_object.assert_called_once_with(
                Bucket="test-raw-bucket",
                Key=test_key,
                Body=test_data,
                ContentType="application/json"
            )
    
    @patch('boto3.client')
    def test_download_raw_data(self, mock_boto3_client):
        """Test downloading data from raw data bucket."""
        mock_s3_client = Mock()
        mock_response = {
            'Body': MagicMock()
        }
        mock_response['Body'].read.return_value = b'{"test": "data"}'
        mock_s3_client.get_object.return_value = mock_response
        mock_boto3_client.return_value = mock_s3_client
        
        with patch.dict(os.environ, self.env_vars):
            s3_manager = S3DataManager()
            
            test_key = "test/file.json"
            result = s3_manager.download_raw_data(test_key)
            
            mock_s3_client.get_object.assert_called_once_with(
                Bucket="test-raw-bucket",
                Key=test_key
            )
            assert result == b'{"test": "data"}'
    
    @patch('boto3.client')
    def test_list_objects(self, mock_boto3_client):
        """Test listing objects in buckets."""
        mock_s3_client = Mock()
        mock_response = {
            'Contents': [
                {'Key': 'test/file1.json', 'Size': 100},
                {'Key': 'test/file2.json', 'Size': 200}
            ]
        }
        mock_s3_client.list_objects_v2.return_value = mock_response
        mock_boto3_client.return_value = mock_s3_client
        
        with patch.dict(os.environ, self.env_vars):
            s3_manager = S3DataManager()
            
            result = s3_manager.list_objects("raw", "test/")
            
            mock_s3_client.list_objects_v2.assert_called_once_with(
                Bucket="test-raw-bucket",
                Prefix="test/"
            )
            assert len(result) == 2
            assert result[0]['Key'] == 'test/file1.json'
    
    @patch('boto3.client')
    def test_list_objects_invalid_bucket_type(self, mock_boto3_client):
        """Test error handling for invalid bucket type."""
        with patch.dict(os.environ, self.env_vars):
            s3_manager = S3DataManager()
            
            with pytest.raises(ValueError, match="Invalid bucket_type"):
                s3_manager.list_objects("invalid", "test/")


class TestAWSIntegration:
    """Test overall AWS integration functionality."""
    
    @patch('app.aws_config.AWSClientManager')
    @patch('app.aws_config.get_aws_config')
    def test_verify_aws_configuration_success(self, mock_get_config, mock_client_manager):
        """Test successful AWS configuration verification."""
        # Setup mocks
        mock_config = Mock()
        mock_config.s3_bucket_raw_data = "test-bucket"
        mock_get_config.return_value = mock_config
        
        mock_manager = Mock()
        mock_s3_client = Mock()
        mock_manager.get_s3_client.return_value = mock_s3_client
        mock_client_manager.return_value = mock_manager
        
        # Test verification
        result = verify_aws_configuration()
        
        assert result is True
        mock_s3_client.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket", 
            MaxKeys=1
        )
    
    @patch('app.aws_config.AWSClientManager')
    @patch('app.aws_config.get_aws_config')
    def test_verify_aws_configuration_failure(self, mock_get_config, mock_client_manager):
        """Test AWS configuration verification failure."""
        # Setup mocks to raise an exception
        mock_get_config.side_effect = Exception("AWS configuration error")
        
        # Test verification
        result = verify_aws_configuration()
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])