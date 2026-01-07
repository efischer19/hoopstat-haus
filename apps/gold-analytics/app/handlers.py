"""
AWS Lambda event handlers for Gold layer analytics processing.

This module provides handlers for S3 events that trigger Gold layer processing
when new Silver layer data arrives.
"""

from typing import Any

from hoopstat_observability import get_logger

from .config import load_config
from .performance import performance_context
from .processors import GoldProcessor
from .s3_discovery import parse_s3_event_key

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    AWS Lambda entry point for S3-triggered Gold analytics processing.

    Processes silver-ready marker files (ADR-028 daily trigger) to run Gold
    analytics exactly once per day after Silver processing completes.

    Args:
        event: S3 event that triggered the Lambda
        context: Lambda runtime context

    Returns:
        Response dict with processing results
    """
    logger.info("Gold analytics Lambda triggered")
    logger.info(f"Event: {event}")

    try:
        # Load configuration
        config = load_config()

        # Initialize processor
        processor = GoldProcessor(
            silver_bucket=config.silver_bucket,
            gold_bucket=config.gold_bucket,
            config=config,
        )

        # Extract and process S3 event records
        records_processed = 0
        dates_to_process = set()
        processing_results = {}

        if "Records" in event:
            with performance_context("lambda_s3_event_processing") as ctx:
                for record in event["Records"]:
                    try:
                        # Extract S3 information from the event
                        s3_info = record.get("s3", {})
                        bucket_name = s3_info.get("bucket", {}).get("name", "")
                        object_key = s3_info.get("object", {}).get("key", "")

                        if not object_key:
                            logger.warning("S3 event record missing object key")
                            continue

                        # Parse S3 key to extract processing metadata
                        parsed = parse_s3_event_key(object_key)
                        if not parsed:
                            logger.warning(f"Could not parse S3 key: {object_key}")
                            continue

                        # Check if this is a silver-ready marker
                        if parsed.get("is_marker", False):
                            logger.info(
                                "Detected silver-ready marker for date: "
                                f"{parsed['date']}"
                            )
                        else:
                            logger.info(
                                f"Detected Silver data file (non-marker): "
                                f"bucket={bucket_name}, "
                                f"file_type={parsed['file_type']}, "
                                f"date={parsed['date']}"
                            )

                        # Add to dates to process
                        # (works for both markers and direct files)
                        target_date = parsed["date"]
                        dates_to_process.add(target_date)

                    except Exception as e:
                        logger.error(f"Failed to process S3 event record: {e}")
                        continue

                # Process each unique date (idempotent - safe under retries)
                for target_date in dates_to_process:
                    try:
                        logger.info(
                            f"Processing Gold analytics for date: {target_date}"
                        )
                        success = processor.process_date(target_date, dry_run=False)
                        processing_results[str(target_date)] = success

                        if success:
                            records_processed += 1

                    except Exception as e:
                        logger.error(f"Failed to process date {target_date}: {e}")
                        processing_results[str(target_date)] = False

                ctx["records_processed"] = records_processed

        successful_dates = sum(1 for success in processing_results.values() if success)
        total_dates = len(processing_results)

        return {
            "statusCode": 200,
            "body": {
                "message": (
                    f"Gold analytics processing completed: "
                    f"{successful_dates}/{total_dates} dates successful"
                ),
                "dates_processed": list(processing_results.keys()),
                "records_processed": records_processed,
                "processing_results": processing_results,
            },
        }

    except Exception as e:
        logger.error(f"Gold analytics Lambda failed: {e}")
        return {
            "statusCode": 500,
            "body": {"error": str(e)},
        }
