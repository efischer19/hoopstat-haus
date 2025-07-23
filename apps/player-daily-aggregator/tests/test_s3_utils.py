"""Tests for S3 utilities module."""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import boto3
from moto import mock_aws
import io

from player_daily_aggregator.s3_utils import (
    S3DataHandler,
    extract_s3_info_from_event
)


class TestS3DataHandler:
    """Test cases for S3DataHandler class."""
    
    @mock_aws
    def test_read_silver_layer_data_success(self):
        """Test successful reading of Silver layer data."""
        # Create mock S3 bucket and data
        s3_client = boto3.client('s3', region_name='us-east-1')
        bucket_name = 'test-silver-bucket'
        s3_client.create_bucket(Bucket=bucket_name)
        
        # Create sample parquet data
        test_df = pd.DataFrame([
            {
                'player_id': 'player1',
                'points': 25,
                'rebounds': 8,
                'assists': 5,
                'season': '2023-24',
                'game_date': '2024-01-15'
            }
        ])
        
        # Write parquet data to S3
        parquet_buffer = io.BytesIO()
        test_df.to_parquet(parquet_buffer, index=False)
        parquet_buffer.seek(0)
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key='player_games/season=2023-24/date=2024-01-15/data.parquet',
            Body=parquet_buffer.getvalue()
        )
        
        # Test reading the data
        handler = S3DataHandler()
        result_df = handler.read_silver_layer_data(
            f's3://{bucket_name}/player_games/season=2023-24/date=2024-01-15/'
        )
        
        assert len(result_df) == 1
        assert result_df.iloc[0]['player_id'] == 'player1'
        assert result_df.iloc[0]['points'] == 25
    
    @mock_aws
    def test_read_silver_layer_data_empty_bucket(self):
        """Test reading from empty S3 path."""
        s3_client = boto3.client('s3', region_name='us-east-1')
        bucket_name = 'test-empty-bucket'
        s3_client.create_bucket(Bucket=bucket_name)
        
        handler = S3DataHandler()
        result_df = handler.read_silver_layer_data(f's3://{bucket_name}/nonexistent/')
        
        assert result_df.empty
    
    @mock_aws
    def test_write_gold_layer_data_with_partitioning(self):
        """Test writing Gold layer data with partitioning."""
        s3_client = boto3.client('s3', region_name='us-east-1')
        bucket_name = 'test-gold-bucket'
        s3_client.create_bucket(Bucket=bucket_name)
        
        # Test data with partitioning columns
        test_df = pd.DataFrame([
            {
                'player_id': 'player1',
                'season': '2023-24',
                'points': 25,
                'rebounds': 8,
                'assists': 5
            },
            {
                'player_id': 'player2',
                'season': '2023-24',
                'points': 15,
                'rebounds': 12,
                'assists': 3
            }
        ])
        
        handler = S3DataHandler()
        written_paths = handler.write_gold_layer_data(
            test_df,
            f's3://{bucket_name}/player_daily_stats',
            partition_columns=['season', 'player_id']
        )
        
        assert len(written_paths) == 2  # Two players, two partitions
        assert any('player_id=player1' in path for path in written_paths)
        assert any('player_id=player2' in path for path in written_paths)
    
    @mock_aws 
    def test_write_gold_layer_data_empty_dataframe(self):
        """Test writing empty DataFrame."""
        handler = S3DataHandler()
        written_paths = handler.write_gold_layer_data(
            pd.DataFrame(),
            's3://test-bucket/path'
        )
        
        assert written_paths == []
    
    def test_read_existing_season_data_no_file(self):
        """Test reading season data when file doesn't exist."""
        handler = S3DataHandler()
        result_df = handler.read_existing_season_data(
            'player1', 
            '2023-24',
            's3://nonexistent-bucket/path'
        )
        
        assert result_df.empty


class TestExtractS3InfoFromEvent:
    """Test cases for S3 event information extraction."""
    
    def test_valid_s3_event_extraction(self):
        """Test extraction from valid S3 event."""
        event = {
            'Records': [{
                's3': {
                    'bucket': {'name': 'test-silver-bucket'},
                    'object': {'key': 'player_games/season=2023-24/date=2024-01-15/data.parquet'}
                }
            }]
        }
        
        result = extract_s3_info_from_event(event)
        
        assert result['bucket'] == 'test-silver-bucket'
        assert result['key'] == 'player_games/season=2023-24/date=2024-01-15/data.parquet'
        assert result['season'] == '2023-24'
        assert result['date'] == '2024-01-15'
        assert result['silver_path'] == 's3://test-silver-bucket/player_games/season=2023-24/date=2024-01-15'
    
    def test_s3_event_missing_season(self):
        """Test extraction when season info is missing."""
        event = {
            'Records': [{
                's3': {
                    'bucket': {'name': 'test-bucket'},
                    'object': {'key': 'player_games/date=2024-01-15/data.parquet'}
                }
            }]
        }
        
        result = extract_s3_info_from_event(event)
        
        assert result['season'] is None
        assert result['date'] == '2024-01-15'
    
    def test_invalid_s3_event_format(self):
        """Test handling of invalid S3 event format."""
        invalid_event = {'invalid': 'format'}
        
        with pytest.raises(Exception) as exc_info:
            extract_s3_info_from_event(invalid_event)
        
        assert "Invalid S3 event format" in str(exc_info.value)
    
    def test_s3_event_missing_records(self):
        """Test handling of event without Records."""
        event = {'no_records': 'here'}
        
        with pytest.raises(Exception) as exc_info:
            extract_s3_info_from_event(event)
        
        assert "Invalid S3 event format" in str(exc_info.value)