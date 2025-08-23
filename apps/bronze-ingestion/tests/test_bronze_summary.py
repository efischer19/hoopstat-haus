"""
Tests for bronze layer summary functionality.
"""

import json
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.bronze_summary import BronzeSummaryManager


class TestBronzeSummaryManager:
    """Test suite for BronzeSummaryManager class."""

    @pytest.fixture
    def mock_s3_manager(self):
        """Create a mock S3 manager for testing."""
        mock_manager = MagicMock()
        mock_manager.bucket_name = "test-bronze-bucket"
        mock_manager.s3_client = MagicMock()
        return mock_manager

    @pytest.fixture
    def summary_manager(self, mock_s3_manager):
        """Create a BronzeSummaryManager instance for testing."""
        return BronzeSummaryManager(mock_s3_manager)

    def test_generate_summary_basic(self, summary_manager, mock_s3_manager):
        """Test basic summary generation functionality."""
        # Setup mock data
        target_date = date(2024, 1, 15)
        games_count = 5
        successful_box_scores = 4

        # Mock the bronze statistics collection
        mock_bronze_stats = {
            "entities": {
                "schedule": {
                    "last_updated": "2024-01-15T14:30:22Z",
                    "file_count": 1,
                    "estimated_size_mb": 0.5,
                    "last_processed_date": "2024-01-15",
                },
                "box_scores": {
                    "last_updated": "2024-01-15T14:30:22Z",
                    "file_count": 4,
                    "estimated_size_mb": 12.3,
                    "last_processed_date": "2024-01-15",
                },
            },
            "storage_info": {"total_files": 5, "estimated_size_mb": 12.8},
        }

        with patch.object(
            summary_manager,
            "_collect_bronze_statistics",
            return_value=mock_bronze_stats,
        ):
            with patch("app.bronze_summary.datetime") as mock_datetime:
                mock_datetime.utcnow.return_value = datetime(2024, 1, 15, 14, 30, 22)

                summary = summary_manager.generate_summary(
                    target_date, games_count, successful_box_scores
                )

        # Verify summary structure and content
        assert summary["summary_version"] == "1.0"
        assert summary["generated_at"] == "2024-01-15T14:30:22Z"

        bronze_stats = summary["bronze_layer_stats"]
        assert bronze_stats["last_ingestion_date"] == "2024-01-15"
        assert bronze_stats["last_successful_run"] == "2024-01-15T14:30:22Z"
        assert bronze_stats["total_entities"] == 2

        # Verify entities data
        assert "schedule" in bronze_stats["entities"]
        assert "box_scores" in bronze_stats["entities"]
        assert bronze_stats["entities"]["schedule"]["file_count"] == 1
        assert bronze_stats["entities"]["box_scores"]["file_count"] == 4

        # Verify data quality metrics
        data_quality = bronze_stats["data_quality"]
        assert data_quality["last_run_games_count"] == 5
        assert data_quality["last_run_successful_box_scores"] == 4
        assert data_quality["last_run_success_rate"] == 0.8  # 4/5

        # Verify storage info
        storage_info = bronze_stats["storage_info"]
        assert storage_info["total_files"] == 5
        assert storage_info["estimated_size_mb"] == 12.8

    def test_generate_summary_no_games(self, summary_manager):
        """Test summary generation when no games were processed."""
        target_date = date(2024, 1, 15)
        games_count = 0
        successful_box_scores = 0

        mock_bronze_stats = {
            "entities": {},
            "storage_info": {"total_files": 0, "estimated_size_mb": 0.0},
        }

        with patch.object(
            summary_manager,
            "_collect_bronze_statistics",
            return_value=mock_bronze_stats,
        ):
            with patch("app.bronze_summary.datetime") as mock_datetime:
                mock_datetime.utcnow.return_value = datetime(2024, 1, 15, 14, 30, 22)

                summary = summary_manager.generate_summary(
                    target_date, games_count, successful_box_scores
                )

        bronze_stats = summary["bronze_layer_stats"]
        assert bronze_stats["total_entities"] == 0
        assert bronze_stats["data_quality"]["last_run_success_rate"] == 0.0
        assert bronze_stats["storage_info"]["total_files"] == 0

    def test_store_summary(self, summary_manager, mock_s3_manager):
        """Test storing summary to S3."""
        test_summary = {
            "summary_version": "1.0",
            "generated_at": "2024-01-15T14:30:22Z",
            "bronze_layer_stats": {
                "last_ingestion_date": "2024-01-15",
                "total_entities": 1,
            },
        }

        key = summary_manager.store_summary(test_summary)

        # Verify S3 put_object was called correctly
        mock_s3_manager.s3_client.put_object.assert_called_once()
        call_args = mock_s3_manager.s3_client.put_object.call_args

        assert call_args[1]["Bucket"] == "test-bronze-bucket"
        assert call_args[1]["Key"] == "_metadata/summary.json"
        assert call_args[1]["ContentType"] == "application/json"

        # Verify the body is valid JSON
        body = call_args[1]["Body"]
        stored_summary = json.loads(body.decode("utf-8"))
        assert stored_summary == test_summary

        # Verify metadata
        metadata = call_args[1]["Metadata"]
        assert metadata["summary_version"] == "1.0"
        assert metadata["type"] == "bronze_layer_summary"

        assert key == "_metadata/summary.json"

    def test_update_bronze_summary_integration(self, summary_manager):
        """Test the integrated update_bronze_summary method."""
        target_date = date(2024, 1, 15)
        games_count = 3
        successful_box_scores = 3

        # Mock both generate_summary and store_summary
        mock_summary = {"test": "summary"}
        with patch.object(
            summary_manager, "generate_summary", return_value=mock_summary
        ) as mock_generate:
            with patch.object(
                summary_manager, "store_summary", return_value="_metadata/summary.json"
            ) as mock_store:
                key = summary_manager.update_bronze_summary(
                    target_date, games_count, successful_box_scores
                )

        # Verify both methods were called
        mock_generate.assert_called_once_with(
            target_date, games_count, successful_box_scores
        )
        mock_store.assert_called_once_with(mock_summary)
        assert key == "_metadata/summary.json"

    def test_collect_bronze_statistics(self, summary_manager, mock_s3_manager):
        """Test bronze statistics collection."""
        target_date = date(2024, 1, 15)

        # Mock list_entities_for_date
        mock_s3_manager.list_entities_for_date.return_value = ["schedule", "box_scores"]

        # Mock entity statistics calls
        with patch.object(summary_manager, "_get_entity_statistics") as mock_get_stats:
            with patch.object(
                summary_manager,
                "_scan_all_entities",
                return_value=["schedule", "box_scores"],
            ):
                mock_get_stats.side_effect = [
                    {
                        "last_updated": "2024-01-15T14:30:22Z",
                        "file_count": 1,
                        "estimated_size_mb": 0.5,
                        "last_processed_date": "2024-01-15",
                    },
                    {
                        "last_updated": "2024-01-15T14:30:22Z",
                        "file_count": 3,
                        "estimated_size_mb": 5.2,
                        "last_processed_date": "2024-01-15",
                    },
                ]

                stats = summary_manager._collect_bronze_statistics(target_date)

        # Verify statistics structure
        assert "entities" in stats
        assert "storage_info" in stats

        # Verify entity data
        assert len(stats["entities"]) == 2
        assert "schedule" in stats["entities"]
        assert "box_scores" in stats["entities"]

        # Verify storage totals
        assert stats["storage_info"]["total_files"] == 4  # 1 + 3
        assert stats["storage_info"]["estimated_size_mb"] == 5.7  # 0.5 + 5.2

    def test_get_entity_statistics(self, summary_manager, mock_s3_manager):
        """Test getting statistics for a specific entity."""
        target_date = date(2024, 1, 15)
        entity = "schedule"

        # Mock S3 response
        mock_response = {
            "KeyCount": 2,
            "Contents": [
                {"Size": 1024, "LastModified": datetime(2024, 1, 15, 14, 30, 22)},
                {"Size": 2048, "LastModified": datetime(2024, 1, 15, 14, 25, 10)},
            ],
        }
        mock_s3_manager.s3_client.list_objects_v2.return_value = mock_response

        stats = summary_manager._get_entity_statistics(entity, target_date)

        # Verify S3 call
        mock_s3_manager.s3_client.list_objects_v2.assert_called_once_with(
            Bucket="test-bronze-bucket", Prefix="raw/schedule/date=2024-01-15/"
        )

        # Verify statistics
        assert stats["file_count"] == 2
        assert stats["estimated_size_mb"] == round(3072 / (1024 * 1024), 2)  # ~0.003 MB
        assert stats["last_updated"] == "2024-01-15T14:30:22"
        assert stats["last_processed_date"] == "2024-01-15"

    def test_get_entity_statistics_no_data(self, summary_manager, mock_s3_manager):
        """Test getting statistics when entity has no data."""
        target_date = date(2024, 1, 15)
        entity = "schedule"

        # Mock empty S3 response
        mock_response = {"KeyCount": 0, "Contents": []}
        mock_s3_manager.s3_client.list_objects_v2.return_value = mock_response

        stats = summary_manager._get_entity_statistics(entity, target_date)

        # Verify empty statistics
        assert stats["file_count"] == 0
        assert stats["estimated_size_mb"] == 0.0
        assert stats["last_updated"] is None
        assert stats["last_processed_date"] == "2024-01-15"

    def test_scan_all_entities(self, summary_manager, mock_s3_manager):
        """Test scanning for all entities in bronze layer."""
        # Mock S3 response for prefix listing
        mock_response = {
            "CommonPrefixes": [
                {"Prefix": "raw/schedule/"},
                {"Prefix": "raw/box_scores/"},
                {"Prefix": "raw/players/"},
            ]
        }
        mock_s3_manager.s3_client.list_objects_v2.return_value = mock_response

        entities = summary_manager._scan_all_entities()

        # Verify S3 call
        mock_s3_manager.s3_client.list_objects_v2.assert_called_once_with(
            Bucket="test-bronze-bucket", Prefix="raw/", Delimiter="/"
        )

        # Verify entities list
        assert entities == ["schedule", "box_scores", "players"]

    def test_error_handling_in_generate_summary(self, summary_manager):
        """Test error handling in generate_summary method."""
        target_date = date(2024, 1, 15)

        # Mock _collect_bronze_statistics to raise an exception
        with patch.object(
            summary_manager,
            "_collect_bronze_statistics",
            side_effect=Exception("S3 error"),
        ):
            with pytest.raises(Exception, match="S3 error"):
                summary_manager.generate_summary(target_date, 5, 4)

    def test_error_handling_in_collect_statistics(
        self, summary_manager, mock_s3_manager
    ):
        """Test error handling in _collect_bronze_statistics method."""
        target_date = date(2024, 1, 15)

        # Mock S3 manager to raise an exception
        mock_s3_manager.list_entities_for_date.side_effect = Exception(
            "S3 connection error"
        )

        # Should return empty stats instead of failing
        stats = summary_manager._collect_bronze_statistics(target_date)

        assert stats == {
            "entities": {},
            "storage_info": {"total_files": 0, "estimated_size_mb": 0.0},
        }
