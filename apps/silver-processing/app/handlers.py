"""
AWS Lambda event handlers for Silver layer processing.

This module provides handlers for S3 events that trigger Silver layer processing
when new Bronze layer data arrives.
"""

import json
from datetime import datetime
from typing import Any

from hoopstat_observability import get_logger
from hoopstat_s3 import SilverS3Manager

from .processors import SilverProcessor

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    AWS Lambda entry point for S3-triggered Silver processing.

    Args:
        event: S3 event that triggered the Lambda
        context: Lambda runtime context

    Returns:
        Response dict with processing results
    """
    logger.info("Silver processing Lambda triggered")
    logger.info(f"Event: {event}")

    try:
        # Get bucket name from environment or use default
        import os

        bucket_name = os.getenv("BRONZE_BUCKET")
        if not bucket_name:
            logger.error("BRONZE_BUCKET environment variable not set")
            return {"statusCode": 400, "message": "No bucket configured"}

        # Initialize S3 manager
        s3_manager = SilverS3Manager(bucket_name)

        # Check if this is a summary.json update
        is_summary_update = False
        for record in event.get("Records", []):
            if record.get("eventSource") == "aws:s3":
                key = record.get("s3", {}).get("object", {}).get("key", "")
                if key.endswith("summary.json"):
                    is_summary_update = True
                    break

        if is_summary_update:
            logger.info("Detected summary.json update, checking for new data")
            try:
                # Read summary file to get the last ingestion date
                response = s3_manager.s3_client.get_object(
                    Bucket=bucket_name, Key="_metadata/summary.json"
                )
                summary_content = response["Body"].read().decode("utf-8")
                summary_data = json.loads(summary_content)

                # Extract date from summary
                # Structure: bronze_layer_stats -> last_ingestion_date
                last_ingestion_date_str = summary_data.get(
                    "bronze_layer_stats", {}
                ).get("last_ingestion_date")

                if not last_ingestion_date_str:
                    logger.warning("No last_ingestion_date found in summary")
                    return {
                        "statusCode": 200,
                        "message": "No date found in summary to process",
                    }

                # Parse date (YYYY-MM-DD)
                target_date = datetime.strptime(
                    last_ingestion_date_str, "%Y-%m-%d"
                ).date()

                logger.info(f"Triggering processing for date: {target_date}")

                # Process the date
                processor = SilverProcessor(bronze_bucket=bucket_name)
                success = processor.process_date(target_date, dry_run=False)

                if success:
                    return {
                        "statusCode": 200,
                        "message": f"Successfully processed data for {target_date}",
                    }
                else:
                    return {
                        "statusCode": 500,
                        "message": f"Processing failed for {target_date}",
                    }

            except Exception as e:
                logger.error(f"Failed to process summary update: {e}")
                return {
                    "statusCode": 500,
                    "message": f"Failed to process summary update: {e}",
                }

        logger.warning("Event is not a summary.json update, ignoring")
        return {"statusCode": 200, "message": "Event ignored (not summary.json)"}

    except Exception as e:
        logger.error(f"Lambda handler failed: {e}")
        return {"statusCode": 500, "message": f"Processing failed: {e}"}
