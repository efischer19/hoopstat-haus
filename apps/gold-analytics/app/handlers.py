"""
AWS Lambda event handlers for Gold layer analytics processing.

This module provides handlers for S3 events that trigger Gold layer processing
when new Silver layer data arrives. Supports both direct S3 events and 
SQS-wrapped S3 events for reliable processing.
"""

import json
from typing import Any

from hoopstat_observability import get_logger

from .config import load_config
from .performance import performance_context
from .processors import GoldProcessor
from .s3_discovery import parse_s3_event_key

logger = get_logger(__name__)


def normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize event structure to handle both direct S3 events and SQS events.
    
    When events come through SQS, each SQS record contains an S3 event in its body.
    This function extracts and normalizes the event structure.
    
    Args:
        event: Raw Lambda event (either S3 or SQS)
        
    Returns:
        Normalized event with S3 Records structure
    """
    # Check if this is an SQS event
    if "Records" in event and event["Records"]:
        first_record = event["Records"][0]
        
        # SQS events have eventSource "aws:sqs"
        if first_record.get("eventSource") == "aws:sqs":
            logger.info("Processing SQS-wrapped S3 events")
            normalized_records = []
            
            for sqs_record in event["Records"]:
                try:
                    # Parse the S3 event from SQS message body
                    message_body = sqs_record.get("body", "{}")
                    if isinstance(message_body, str):
                        s3_event = json.loads(message_body)
                    else:
                        s3_event = message_body
                    
                    # Extract S3 records from the parsed event
                    if "Records" in s3_event:
                        normalized_records.extend(s3_event["Records"])
                        
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Failed to parse SQS message body: {e}")
                    continue
            
            return {"Records": normalized_records}
        
        # Direct S3 events have eventSource "aws:s3"
        elif first_record.get("eventSource") == "aws:s3":
            logger.info("Processing direct S3 events")
            return event
    
    logger.warning(f"Unknown event structure: {event}")
    return event


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    AWS Lambda entry point for S3-triggered Gold analytics processing.
    
    Supports both direct S3 events and SQS-wrapped S3 events for reliable processing.

    Args:
        event: S3 event or SQS event containing S3 events that triggered the Lambda
        context: Lambda runtime context

    Returns:
        Response dict with processing results
    """
    logger.info("Gold analytics Lambda triggered")
    logger.info(f"Event: {event}")

    try:
        # Normalize event structure to handle both S3 and SQS events
        normalized_event = normalize_event(event)
        
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

        if "Records" in normalized_event:
            with performance_context("lambda_s3_event_processing") as ctx:
                for record in normalized_event["Records"]:
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

                        # Add to dates to process
                        target_date = parsed["date"]
                        dates_to_process.add(target_date)

                        logger.info(
                            f"Parsed S3 event: bucket={bucket_name}, "
                            f"file_type={parsed['file_type']}, date={target_date}"
                        )

                    except Exception as e:
                        logger.error(f"Failed to process S3 event record: {e}")
                        continue

                # Process each unique date
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
