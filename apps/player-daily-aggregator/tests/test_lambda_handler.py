"""Tests for Lambda handler module."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from player_daily_aggregator.lambda_handler import (
    lambda_handler,
    create_response,
    log_info,
    log_warning,
    log_error
)


class TestLambdaHandler:
    """Test cases for Lambda handler function."""
    
    @patch('player_daily_aggregator.lambda_handler.S3DataHandler')
    @patch('player_daily_aggregator.lambda_handler.extract_s3_info_from_event')
    def test_successful_processing(self, mock_extract_s3, mock_s3_handler_class):
        """Test successful processing of player data."""
        # Mock S3 event info extraction
        mock_extract_s3.return_value = {
            'season': '2023-24',
            'date': '2024-01-15',
            'silver_path': 's3://test-bucket/silver/player_games/season=2023-24/date=2024-01-15'
        }
        
        # Mock S3 handler
        mock_s3_handler = Mock()
        mock_s3_handler_class.return_value = mock_s3_handler
        
        # Mock Silver layer data
        mock_player_data = pd.DataFrame([
            {
                'player_id': 'player1',
                'points': 25,
                'rebounds': 8,
                'assists': 5,
                'steals': 2,
                'blocks': 1,
                'turnovers': 3,
                'field_goals_made': 10,
                'field_goals_attempted': 20,
                'three_pointers_made': 3,
                'three_pointers_attempted': 8,
                'free_throws_made': 2,
                'free_throws_attempted': 2,
                'minutes_played': 35.0,
                'game_id': 'game1',
                'season': '2023-24',
                'game_date': '2024-01-15'
            }
        ])
        mock_s3_handler.read_silver_layer_data.return_value = mock_player_data
        mock_s3_handler.write_gold_layer_data.return_value = ['s3://path1', 's3://path2']
        mock_s3_handler.read_existing_season_data.return_value = pd.DataFrame()
        
        # Create test event
        event = {
            'Records': [{
                's3': {
                    'bucket': {'name': 'test-bucket'},
                    'object': {'key': 'player_games/season=2023-24/date=2024-01-15/data.parquet'}
                }
            }]
        }
        
        context = Mock()
        
        # Execute handler
        result = lambda_handler(event, context)
        
        # Verify results
        assert result['status'] == 'success'
        assert result['records_processed'] == 1
        assert 'duration_in_seconds' in result
        assert 'correlation_id' in result
        
        # Verify S3 operations were called
        mock_s3_handler.read_silver_layer_data.assert_called_once()
        assert mock_s3_handler.write_gold_layer_data.call_count == 2  # Daily + season stats
    
    @patch('player_daily_aggregator.lambda_handler.S3DataHandler')
    @patch('player_daily_aggregator.lambda_handler.extract_s3_info_from_event')
    def test_empty_silver_data_handling(self, mock_extract_s3, mock_s3_handler_class):
        """Test handling of empty Silver layer data."""
        mock_extract_s3.return_value = {
            'season': '2023-24',
            'date': '2024-01-15',
            'silver_path': 's3://test-bucket/silver/player_games/season=2023-24/date=2024-01-15'
        }
        
        mock_s3_handler = Mock()
        mock_s3_handler_class.return_value = mock_s3_handler
        mock_s3_handler.read_silver_layer_data.return_value = pd.DataFrame()  # Empty data
        
        event = {
            'Records': [{
                's3': {
                    'bucket': {'name': 'test-bucket'},
                    'object': {'key': 'player_games/season=2023-24/date=2024-01-15/data.parquet'}
                }
            }]
        }
        
        context = Mock()
        result = lambda_handler(event, context)
        
        assert result['status'] == 'success'
        assert result['records_processed'] == 0
        assert 'No data to process' in result['message']
    
    @patch('player_daily_aggregator.lambda_handler.S3DataHandler')
    @patch('player_daily_aggregator.lambda_handler.extract_s3_info_from_event')
    def test_s3_error_handling(self, mock_extract_s3, mock_s3_handler_class):
        """Test handling of S3 errors."""
        mock_extract_s3.return_value = {
            'season': '2023-24',
            'date': '2024-01-15',
            'silver_path': 's3://test-bucket/silver/player_games/season=2023-24/date=2024-01-15'
        }
        
        mock_s3_handler = Mock()
        mock_s3_handler_class.return_value = mock_s3_handler
        mock_s3_handler.read_silver_layer_data.side_effect = Exception("S3 read error")
        
        event = {
            'Records': [{
                's3': {
                    'bucket': {'name': 'test-bucket'},
                    'object': {'key': 'player_games/season=2023-24/date=2024-01-15/data.parquet'}
                }
            }]
        }
        
        context = Mock()
        result = lambda_handler(event, context)
        
        assert result['status'] == 'error'
        assert 'S3 read error' in result['message']
        assert 'duration_in_seconds' in result
    
    @patch('player_daily_aggregator.lambda_handler.extract_s3_info_from_event')
    def test_invalid_event_handling(self, mock_extract_s3):
        """Test handling of invalid S3 events."""
        mock_extract_s3.side_effect = Exception("Invalid S3 event format")
        
        event = {'invalid': 'event'}
        context = Mock()
        
        result = lambda_handler(event, context)
        
        assert result['status'] == 'error'
        assert 'Invalid S3 event format' in result['message']


class TestCreateResponse:
    """Test cases for response creation."""
    
    def test_success_response(self):
        """Test creation of success response."""
        response = create_response(
            'success', 
            'Processing completed', 
            'test-correlation-id',
            100,
            45.67
        )
        
        assert response['status'] == 'success'
        assert response['message'] == 'Processing completed'
        assert response['correlation_id'] == 'test-correlation-id'
        assert response['records_processed'] == 100
        assert response['duration_in_seconds'] == 45.67
    
    def test_error_response(self):
        """Test creation of error response."""
        response = create_response(
            'error',
            'Processing failed',
            'test-correlation-id',
            50,
            23.45
        )
        
        assert response['status'] == 'error'
        assert response['message'] == 'Processing failed'
        assert response['records_processed'] == 50
        assert response['duration_in_seconds'] == 23.45


class TestLoggingFunctions:
    """Test cases for structured logging functions."""
    
    @patch('builtins.print')
    def test_log_info_basic(self, mock_print):
        """Test basic INFO logging."""
        log_info("Test message", "test-correlation-id")
        
        # Verify print was called
        mock_print.assert_called_once()
        
        # Parse the logged JSON
        logged_data = json.loads(mock_print.call_args[0][0])
        
        assert logged_data['level'] == 'INFO'
        assert logged_data['message'] == 'Test message'
        assert logged_data['job_name'] == 'player_daily_aggregator'
        assert logged_data['correlation_id'] == 'test-correlation-id'
        assert 'timestamp' in logged_data
    
    @patch('builtins.print')
    def test_log_info_with_extra(self, mock_print):
        """Test INFO logging with extra fields."""
        extra_data = {
            'records_processed': 100,
            'duration_in_seconds': 45.67
        }
        
        log_info("Processing completed", "test-correlation-id", extra_data)
        
        logged_data = json.loads(mock_print.call_args[0][0])
        
        assert logged_data['records_processed'] == 100
        assert logged_data['duration_in_seconds'] == 45.67
    
    @patch('builtins.print')
    def test_log_warning(self, mock_print):
        """Test WARNING logging."""
        log_warning("Warning message", "test-correlation-id")
        
        logged_data = json.loads(mock_print.call_args[0][0])
        
        assert logged_data['level'] == 'WARNING'
        assert logged_data['message'] == 'Warning message'
    
    @patch('builtins.print')
    def test_log_error(self, mock_print):
        """Test ERROR logging."""
        log_error("Error message", "test-correlation-id")
        
        logged_data = json.loads(mock_print.call_args[0][0])
        
        assert logged_data['level'] == 'ERROR'
        assert logged_data['message'] == 'Error message'
    
    @patch('builtins.print')
    def test_log_structured_format_adr015_compliance(self, mock_print):
        """Test that logging complies with ADR-015 structured format."""
        # Test with duration_in_seconds and records_processed fields
        extra_data = {
            'duration_in_seconds': 45.67,
            'records_processed': 150,
            'season': '2023-24'
        }
        
        log_info("Job completed successfully", "test-correlation-id", extra_data)
        
        logged_data = json.loads(mock_print.call_args[0][0])
        
        # Verify ADR-015 required fields are present
        assert 'timestamp' in logged_data
        assert 'level' in logged_data
        assert 'message' in logged_data
        assert 'job_name' in logged_data
        assert 'duration_in_seconds' in logged_data
        assert 'records_processed' in logged_data
        
        # Verify specific values
        assert logged_data['duration_in_seconds'] == 45.67
        assert logged_data['records_processed'] == 150
        assert logged_data['job_name'] == 'player_daily_aggregator'