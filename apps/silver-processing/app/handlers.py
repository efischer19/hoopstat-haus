"""
AWS Lambda event handlers for Silver layer processing.

This module provides handlers for S3 events that trigger Silver layer processing
when new Bronze layer data arrives.
"""

from typing import Any

from hoopstat_observability import get_logger

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
        # Parse S3 events
        s3_records = parse_s3_events(event)

        if not s3_records:
            logger.warning("No S3 records found in event")
            return {"statusCode": 200, "message": "No records to process"}

        # Process each S3 record
        processor = SilverProcessor()
        results = []

        for record in s3_records:
            try:
                result = process_s3_record(processor, record)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process S3 record {record}: {e}")
                results.append({"record": record, "success": False, "error": str(e)})

        # Summarize results
        success_count = sum(1 for r in results if r.get("success", False))
        total_count = len(results)

        logger.info(f"Processed {success_count}/{total_count} records successfully")

        return {
            "statusCode": 200,
            "message": f"Processed {success_count}/{total_count} records",
            "results": results,
        }

    except Exception as e:
        logger.error(f"Lambda handler failed: {e}")
        return {"statusCode": 500, "message": f"Processing failed: {e}"}


def parse_s3_events(event: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Parse S3 event records from Lambda event.

    Args:
        event: Lambda event containing S3 records

    Returns:
        List of S3 record dictionaries
    """
    try:
        records = event.get("Records", [])
        s3_records = []

        for record in records:
            if record.get("eventSource") == "aws:s3":
                s3_records.append(record)

        logger.info(f"Found {len(s3_records)} S3 records")
        return s3_records

    except Exception as e:
        logger.error(f"Failed to parse S3 events: {e}")
        return []


def process_s3_record(
    processor: SilverProcessor, record: dict[str, Any]
) -> dict[str, Any]:
    """
    Process a single S3 event record.

    Args:
        processor: The Silver processor instance
        record: S3 event record

    Returns:
        Processing result dictionary
    """
    try:
        # Extract S3 bucket and key
        s3_info = record.get("s3", {})
        bucket = s3_info.get("bucket", {}).get("name")
        key = s3_info.get("object", {}).get("key")

        if not bucket or not key:
            raise ValueError("Missing S3 bucket or key in record")

        logger.info(f"Processing S3 object: s3://{bucket}/{key}")

        # TODO: Implement S3-specific processing logic in next PR
        # This will include:
        # 1. Determine if this is Bronze layer data we should process
        # 2. Extract date/game info from S3 key
        # 3. Trigger appropriate processing method

        return {
            "record": {"bucket": bucket, "key": key},
            "success": True,
            "message": "Skeleton processing completed",
        }

    except Exception as e:
        logger.error(f"S3 record processing failed: {e}")
        raise
