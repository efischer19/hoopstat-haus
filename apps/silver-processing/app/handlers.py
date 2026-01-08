"""
AWS Lambda event handlers for Silver layer processing.

This module provides handlers for S3 events that trigger Silver layer processing
when new Bronze layer data arrives.
"""

from datetime import date, datetime, timedelta
from typing import Any

from hoopstat_observability import get_logger
from hoopstat_s3 import SilverS3Manager

from .processors import SilverProcessor

logger = get_logger(__name__)


def _parse_yyyy_mm_dd(value: str) -> date:
    """
    Parse a date string in YYYY-MM-DD format.

    Args:
        value: Date string in YYYY-MM-DD format (e.g., "2024-01-15")

    Returns:
        Parsed date object

    Raises:
        ValueError: If the date string is not in valid YYYY-MM-DD format
    """
    return datetime.strptime(value, "%Y-%m-%d").date()


def _iter_inclusive_dates(start: date, end: date) -> list[date]:
    """
    Generate a list of dates from start to end (inclusive).

    Args:
        start: Start date of the range
        end: End date of the range (inclusive)

    Returns:
        List of date objects from start to end (inclusive)

    Raises:
        ValueError: If start_date is greater than end_date
    """
    if start > end:
        raise ValueError("start_date must be <= end_date")

    dates: list[date] = []
    current = start
    while current <= end:
        dates.append(current)
        current = current + timedelta(days=1)
    return dates


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
        # Get bucket names from environment
        import os

        bronze_bucket = os.getenv("BRONZE_BUCKET")
        if not bronze_bucket:
            logger.error("BRONZE_BUCKET environment variable not set")
            return {"statusCode": 400, "message": "No bronze bucket configured"}

        silver_bucket = os.getenv("SILVER_BUCKET")
        if not silver_bucket:
            logger.error("SILVER_BUCKET environment variable not set")
            return {"statusCode": 400, "message": "No silver bucket configured"}

        # Manual invocation mode (e.g., GitHub Actions) to reprocess specific dates
        parameters = event.get("parameters") if isinstance(event, dict) else None
        if isinstance(parameters, dict):
            dry_run = bool(parameters.get("dry_run", False))

            # Handle single date parameter
            if parameters.get("date"):
                try:
                    target_date = _parse_yyyy_mm_dd(str(parameters["date"]))
                except ValueError as e:
                    return {
                        "statusCode": 400,
                        "message": (
                            f"Invalid date format: {e}. Expected YYYY-MM-DD format."
                        ),
                    }

                logger.info(
                    f"Manual trigger: processing date {target_date} (dry_run={dry_run})"
                )

                processor = SilverProcessor(
                    bronze_bucket=bronze_bucket, silver_bucket=silver_bucket
                )
                success = processor.process_date(target_date, dry_run=dry_run)
                if success:
                    return {
                        "statusCode": 200,
                        "message": f"Successfully processed data for {target_date}",
                    }
                return {
                    "statusCode": 500,
                    "message": f"Processing failed for {target_date}",
                }

            # Handle date range parameters
            if "start_date" in parameters and "end_date" in parameters:
                # Validate that both dates are provided and non-empty
                if not parameters.get("start_date") or not parameters.get("end_date"):
                    return {
                        "statusCode": 400,
                        "message": (
                            "Invalid manual parameters: provide 'date' or "
                            "both 'start_date' and 'end_date'"
                        ),
                    }

                try:
                    start_date = _parse_yyyy_mm_dd(str(parameters["start_date"]))
                    end_date = _parse_yyyy_mm_dd(str(parameters["end_date"]))
                    target_dates = _iter_inclusive_dates(start_date, end_date)
                except ValueError as e:
                    return {
                        "statusCode": 400,
                        "message": (
                            f"Invalid date format or range: {e}. "
                            "Expected YYYY-MM-DD format and "
                            "start_date <= end_date."
                        ),
                    }

                logger.info(
                    f"Manual trigger: processing date range {start_date}..{end_date} "
                    f"({len(target_dates)} days, dry_run={dry_run})"
                )

                processor = SilverProcessor(
                    bronze_bucket=bronze_bucket, silver_bucket=silver_bucket
                )

                failures: list[str] = []
                for target_date in target_dates:
                    if not processor.process_date(target_date, dry_run=dry_run):
                        failures.append(str(target_date))

                if failures:
                    return {
                        "statusCode": 500,
                        "message": "Processing failed for some dates",
                        "failures": failures,
                    }

                return {
                    "statusCode": 200,
                    "message": (
                        f"Successfully processed data for {len(target_dates)} dates"
                    ),
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                }

            return {
                "statusCode": 400,
                "message": (
                    "Invalid manual parameters: provide 'date' or "
                    "both 'start_date' and 'end_date'"
                ),
            }

        # Initialize S3 manager with both buckets (S3-triggered mode)
        s3_manager = SilverS3Manager(
            bronze_bucket=bronze_bucket, silver_bucket=silver_bucket
        )

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
                summary_data = s3_manager.read_summary_json()

                if not summary_data:
                    logger.warning("Summary file not found or could not be read")
                    return {
                        "statusCode": 404,
                        "message": "Summary file not found",
                    }

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

                # Process the date with both buckets specified
                processor = SilverProcessor(
                    bronze_bucket=bronze_bucket, silver_bucket=silver_bucket
                )
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
