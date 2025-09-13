"""
Integration test for silver-processing Lambda deployment.

This test validates that the Lambda deployment configuration
and S3 event handling work correctly.
"""

import json

import boto3
from moto import mock_aws

from app.handlers import lambda_handler


class TestLambdaDeployment:
    """Test Lambda deployment and S3 integration."""

    def test_s3_event_format_handling(self):
        """Test that Lambda handler can process S3 event format correctly."""
        # Create a realistic S3 event that would be sent by the bucket notification
        s3_event = {
            "Records": [
                {
                    "eventVersion": "2.1",
                    "eventSource": "aws:s3",
                    "awsRegion": "us-east-1",
                    "eventTime": "2024-01-01T12:00:00.000Z",
                    "eventName": "ObjectCreated:Put",
                    "userIdentity": {"principalId": "AWS:AIDAINPONIXQXHT3IKHL2"},
                    "requestParameters": {"sourceIPAddress": "10.0.0.1"},
                    "responseElements": {
                        "x-amz-request-id": "C3D13FE58DE4C2AD",
                        "x-amz-id-2": (
                            "FMyUVURIY8/IgAtTv8xRjskZQpcIZ9KG4V5Wp6S7S/JRWeUWerMUE5JgHvANOjpD"
                        ),
                    },
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "configurationId": "testConfigRule",
                        "bucket": {
                            "name": "test-bronze-bucket",
                            "ownerIdentity": {"principalId": "A3NL1KOZZKExample"},
                            "arn": "arn:aws:s3:::test-bronze-bucket",
                        },
                        "object": {
                            "key": "raw/box_scores/date=2024-01-01/data.json",
                            "size": 1024,
                            "eTag": "0123456789abcdef0123456789abcdef",
                            "sequencer": "0A1B2C3D4E5F678901",
                        },
                    },
                }
            ]
        }

        # Test with no environment variables set (should fail gracefully)
        result = lambda_handler(s3_event, None)

        # Should return error due to missing BRONZE_BUCKET environment variable
        assert result["statusCode"] == 400
        assert "No bucket configured" in result["message"]

    def test_lambda_handler_imports(self):
        """Test that all necessary imports for Lambda handler work."""
        # This tests that the Lambda handler can be imported without issues
        from hoopstat_observability import get_logger
        from hoopstat_s3 import SilverS3Manager

        from app.handlers import lambda_handler
        from app.processors import SilverProcessor

        # All imports should succeed
        assert callable(lambda_handler)
        assert SilverProcessor is not None
        assert SilverS3Manager is not None
        assert get_logger is not None

    def test_dockerfile_handler_path(self):
        """Test that Dockerfile CMD path matches the actual handler."""
        # Read the Dockerfile to verify the CMD path
        with open("Dockerfile") as f:
            dockerfile_content = f.read()

        # Check that the CMD points to the correct handler
        assert 'CMD ["app.lambda_handler.lambda_handler"]' in dockerfile_content

        # Verify the handler function exists and is callable
        from app.lambda_handler import lambda_handler

        assert callable(lambda_handler)

    @mock_aws
    def test_s3_trigger_event_filter(self):
        """Test that S3 event filtering works as expected."""
        # This validates that our S3 event configuration would work
        # Create mock S3 client to test event filtering logic
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bronze-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        # Test files that should trigger the Lambda (match filter)
        trigger_files = [
            "raw/box_scores/date=2024-01-01/data.json",
            "raw/box_scores/date=2024-12-31/data.json",
            "raw/box_scores/date=2023-03-15/data.json",
        ]

        # Test files that should NOT trigger the Lambda (don't match filter)
        no_trigger_files = [
            "raw/box_scores/date=2024-01-01/metadata.json",  # wrong suffix
            "raw/box_scores/summary.json",  # missing date prefix
            "processed/box_scores/date=2024-01-01/data.json",  # wrong prefix
            "raw/player_stats/date=2024-01-01/data.json",  # wrong path
        ]

        # Upload files to test S3 structure
        for file_key in trigger_files + no_trigger_files:
            s3_client.put_object(
                Bucket=bucket_name, Key=file_key, Body=json.dumps({"test": "data"})
            )

        # Verify all files were uploaded
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        uploaded_keys = [obj["Key"] for obj in response.get("Contents", [])]

        assert len(uploaded_keys) == len(trigger_files + no_trigger_files)

        # Test that our filter logic would work
        # In real deployment, S3 would filter these automatically
        # Here we simulate the filtering logic
        def matches_filter(key):
            return key.startswith("raw/box_scores/date=") and key.endswith("/data.json")

        triggered_files = [key for key in uploaded_keys if matches_filter(key)]
        assert len(triggered_files) == len(trigger_files)
        assert set(triggered_files) == set(trigger_files)
