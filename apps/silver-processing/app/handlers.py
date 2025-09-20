"""
AWS Lambda event handlers for Silver layer processing.

This module provides handlers for S3 events that trigger Silver layer processing
when new Bronze layer data arrives. Supports both direct S3 events and 
SQS-wrapped S3 events for reliable processing.
"""

import json
from typing import Any

from hoopstat_observability import get_logger
from hoopstat_s3 import SilverS3Manager

from .processors import SilverProcessor

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
    AWS Lambda entry point for S3-triggered Silver processing.
    
    Supports both direct S3 events and SQS-wrapped S3 events for reliable processing.

    Args:
        event: S3 event or SQS event containing S3 events that triggered the Lambda
        context: Lambda runtime context

    Returns:
        Response dict with processing results
    """
    logger.info("Silver processing Lambda triggered")
    logger.info(f"Event: {event}")

    try:
        # Normalize event structure to handle both S3 and SQS events
        normalized_event = normalize_event(event)
        
        # Get bucket name from environment or use default
        import os

        bucket_name = os.getenv("BRONZE_BUCKET")
        if not bucket_name:
            logger.error("BRONZE_BUCKET environment variable not set")
            return {"statusCode": 400, "message": "No bucket configured"}

        # Initialize S3 manager for event parsing
        s3_manager = SilverS3Manager(bucket_name)

        # Parse S3 events using SilverS3Manager
        bronze_events = s3_manager.parse_s3_event(normalized_event)

        if not bronze_events:
            logger.warning("No Bronze trigger events found in S3 event")
            return {"statusCode": 200, "message": "No Bronze triggers to process"}

        # Process each Bronze event
        processor = SilverProcessor(bronze_bucket=bucket_name)
        results = []

        for bronze_event in bronze_events:
            try:
                result = process_bronze_event(processor, bronze_event)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process Bronze event {bronze_event}: {e}")
                results.append(
                    {"bronze_event": bronze_event, "success": False, "error": str(e)}
                )

        # Summarize results
        success_count = sum(1 for r in results if r.get("success", False))
        total_count = len(results)

        logger.info(
            f"Processed {success_count}/{total_count} Bronze events successfully"
        )

        return {
            "statusCode": 200,
            "message": f"Processed {success_count}/{total_count} Bronze events",
            "results": results,
        }

    except Exception as e:
        logger.error(f"Lambda handler failed: {e}")
        return {"statusCode": 500, "message": f"Processing failed: {e}"}


def process_bronze_event(
    processor: SilverProcessor, bronze_event: dict[str, Any]
) -> dict[str, Any]:
    """
    Process a single Bronze event from S3.

    Args:
        processor: The Silver processor instance
        bronze_event: Bronze event information from SilverS3Manager

    Returns:
        Processing result dictionary
    """
    try:
        # Extract information from Bronze event
        bucket = bronze_event.get("bucket")
        key = bronze_event.get("key")
        entity = bronze_event.get("entity")
        target_date = bronze_event.get("date")

        if not all([bucket, key, entity, target_date]):
            raise ValueError("Missing required Bronze event information")

        logger.info(
            f"Processing Bronze event: entity={entity}, date={target_date}, "
            f"s3://{bucket}/{key}"
        )

        # Process the date using the Silver processor
        success = processor.process_date(target_date, dry_run=False)

        if success:
            return {
                "bronze_event": {
                    "bucket": bucket,
                    "key": key,
                    "entity": entity,
                    "date": target_date.isoformat(),
                },
                "success": True,
                "message": f"Successfully processed {entity} data for {target_date}",
            }
        else:
            return {
                "bronze_event": {
                    "bucket": bucket,
                    "key": key,
                    "entity": entity,
                    "date": target_date.isoformat(),
                },
                "success": False,
                "message": f"Processing failed for {entity} data on {target_date}",
            }

    except Exception as e:
        logger.error(f"Bronze event processing failed: {e}")
        raise
