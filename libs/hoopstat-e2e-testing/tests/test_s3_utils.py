"""
Tests for S3 utilities.
"""

import pandas as pd
import pytest
from moto import mock_aws

from hoopstat_e2e_testing.s3_utils import S3TestUtils


class TestS3TestUtils:
    """Test cases for S3TestUtils class."""

    @pytest.fixture
    def s3_utils(self):
        """Create S3TestUtils instance for testing with moto."""
        with mock_aws():
            # Use moto's mock AWS service instead of real Localstack
            yield S3TestUtils(endpoint_url=None)  # moto doesn't need endpoint_url

    @pytest.fixture
    def test_bucket_name(self):
        """Generate a unique test bucket name."""
        return "test-bucket-s3utils"

    def test_create_bucket(self, s3_utils, test_bucket_name):
        """Test bucket creation."""
        # Clean up any existing bucket
        if s3_utils.bucket_exists(test_bucket_name):
            s3_utils.delete_bucket(test_bucket_name, delete_objects=True)

        # Create bucket
        assert s3_utils.create_bucket(test_bucket_name)
        assert s3_utils.bucket_exists(test_bucket_name)

        # Clean up
        s3_utils.delete_bucket(test_bucket_name)

    def test_bucket_exists(self, s3_utils, test_bucket_name):
        """Test bucket existence check."""
        # Should not exist initially
        assert not s3_utils.bucket_exists(test_bucket_name)

        # Create and check
        s3_utils.create_bucket(test_bucket_name)
        assert s3_utils.bucket_exists(test_bucket_name)

        # Clean up
        s3_utils.delete_bucket(test_bucket_name)
        assert not s3_utils.bucket_exists(test_bucket_name)

    def test_put_get_object_string(self, s3_utils, test_bucket_name):
        """Test putting and getting string objects."""
        s3_utils.create_bucket(test_bucket_name)

        test_data = "Hello, World!"
        key = "test/string_object.txt"

        # Put object
        assert s3_utils.put_object(test_bucket_name, key, test_data)

        # Get object
        retrieved_data = s3_utils.get_object(test_bucket_name, key, "string")
        assert retrieved_data == test_data

        # Clean up
        s3_utils.delete_bucket(test_bucket_name, delete_objects=True)

    def test_put_get_object_json(self, s3_utils, test_bucket_name):
        """Test putting and getting JSON objects."""
        s3_utils.create_bucket(test_bucket_name)

        test_data = {"name": "John Doe", "age": 30, "city": "New York"}
        key = "test/json_object.json"

        # Put object
        assert s3_utils.put_object(test_bucket_name, key, test_data)

        # Get object
        retrieved_data = s3_utils.get_object(test_bucket_name, key, "json")
        assert retrieved_data == test_data

        # Clean up
        s3_utils.delete_bucket(test_bucket_name, delete_objects=True)

    def test_put_get_object_dataframe(self, s3_utils, test_bucket_name):
        """Test putting and getting DataFrame objects."""
        s3_utils.create_bucket(test_bucket_name)

        test_data = pd.DataFrame(
            {
                "name": ["Alice", "Bob", "Charlie"],
                "age": [25, 30, 35],
                "salary": [50000, 60000, 70000],
            }
        )
        key = "test/dataframe_object.parquet"

        # Put object
        assert s3_utils.put_object(test_bucket_name, key, test_data)

        # Get object
        retrieved_data = s3_utils.get_object(test_bucket_name, key, "dataframe")
        pd.testing.assert_frame_equal(retrieved_data, test_data)

        # Clean up
        s3_utils.delete_bucket(test_bucket_name, delete_objects=True)

    def test_delete_object(self, s3_utils, test_bucket_name):
        """Test object deletion."""
        s3_utils.create_bucket(test_bucket_name)

        test_data = "Test data for deletion"
        key = "test/delete_me.txt"

        # Put object
        s3_utils.put_object(test_bucket_name, key, test_data)

        # Verify object exists
        assert s3_utils.get_object(test_bucket_name, key, "string") == test_data

        # Delete object
        assert s3_utils.delete_object(test_bucket_name, key)

        # Verify object is gone
        assert s3_utils.get_object(test_bucket_name, key, "string") is None

        # Clean up
        s3_utils.delete_bucket(test_bucket_name)

    def test_list_objects(self, s3_utils, test_bucket_name):
        """Test listing objects in bucket."""
        s3_utils.create_bucket(test_bucket_name)

        # Put multiple objects
        test_objects = [
            ("test/file1.txt", "Content 1"),
            ("test/file2.txt", "Content 2"),
            ("other/file3.txt", "Content 3"),
        ]

        for key, content in test_objects:
            s3_utils.put_object(test_bucket_name, key, content)

        # List all objects
        all_objects = s3_utils.list_objects(test_bucket_name)
        assert len(all_objects) == 3

        # List objects with prefix
        test_objects = s3_utils.list_objects(test_bucket_name, "test/")
        assert len(test_objects) == 2

        # Clean up
        s3_utils.delete_bucket(test_bucket_name, delete_objects=True)

    def test_setup_medallion_buckets(self, s3_utils):
        """Test medallion architecture bucket setup."""
        project_name = "test-medallion"

        # Setup buckets
        buckets = s3_utils.setup_medallion_buckets(project_name)

        # Verify bucket names
        expected_buckets = {
            "bronze": f"{project_name}-bronze",
            "silver": f"{project_name}-silver",
            "gold": f"{project_name}-gold",
        }
        assert buckets == expected_buckets

        # Verify buckets exist
        for bucket_name in buckets.values():
            assert s3_utils.bucket_exists(bucket_name)

        # Clean up
        for bucket_name in buckets.values():
            s3_utils.delete_bucket(bucket_name, delete_objects=True)

    def test_cleanup_test_buckets(self, s3_utils):
        """Test cleanup of test buckets."""
        # Create test buckets
        test_buckets = ["test-bucket-1", "test-bucket-2", "prod-bucket-3"]

        for bucket_name in test_buckets:
            s3_utils.create_bucket(bucket_name)

        # Cleanup only test buckets
        s3_utils.cleanup_test_buckets("test-")

        # Verify only test buckets are deleted
        assert not s3_utils.bucket_exists("test-bucket-1")
        assert not s3_utils.bucket_exists("test-bucket-2")
        assert s3_utils.bucket_exists("prod-bucket-3")

        # Clean up remaining bucket
        s3_utils.delete_bucket("prod-bucket-3")
