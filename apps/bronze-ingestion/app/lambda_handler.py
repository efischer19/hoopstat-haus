"""
Lambda handler for bronze-ingestion application.

This module provides a Lambda-compatible entry point that bridges Lambda
invocation events to the existing CLI-based bronze ingestion application.
It parses the Lambda event payload and converts parameters to invoke the
appropriate CLI commands.
"""

import json
from datetime import datetime
from typing import Any

from hoopstat_observability import get_logger

from .ingestion import DateScopedIngestion

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    AWS Lambda handler for bronze layer ingestion.

    Expected event format:
    {
        "source": "github-actions-daily",
        "trigger_type": "workflow_dispatch" | "schedule",
        "parameters": {
            "date": "YYYY-MM-DD",
            "dry_run": boolean,
            "force_run": boolean
        },
        "metadata": {
            "workflow_run_id": "string",
            "workflow_run_number": "string",
            "repository": "string",
            "triggered_at": "ISO timestamp"
        }
    }

    Args:
        event: Lambda event containing ingestion parameters
        context: Lambda context object

    Returns:
        Dict containing execution status and results
    """
    correlation_id = context.aws_request_id
    start_time = datetime.utcnow()

    logger.info(
        "Bronze ingestion Lambda handler started",
        correlation_id=correlation_id,
        function_name=context.function_name,
        event_source=event.get("source", "unknown"),
        trigger_type=event.get("trigger_type", "unknown"),
    )

    try:
        # Extract parameters from event
        parameters = event.get("parameters", {})
        date_str = parameters.get("date")
        dry_run = parameters.get("dry_run", False)
        force_run = parameters.get("force_run", False)

        # Parse and validate date
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError as e:
                raise ValueError(
                    f"Invalid date format '{date_str}'. Expected YYYY-MM-DD"
                ) from e
        else:
            # Default to today (UTC) if no date provided
            target_date = datetime.utcnow().date()

        logger.info(
            "Starting bronze layer ingestion",
            target_date=target_date.isoformat(),
            dry_run=dry_run,
            force_run=force_run,
            correlation_id=correlation_id,
        )

        if dry_run:
            logger.info("Dry run mode - no data will be written")

        # Create and run ingestion
        ingestion = DateScopedIngestion()
        success = ingestion.run(target_date=target_date, dry_run=dry_run)

        # Calculate execution time
        end_time = datetime.utcnow()
        duration_seconds = (end_time - start_time).total_seconds()

        if success:
            logger.info(
                "Bronze layer ingestion completed successfully",
                duration_in_seconds=duration_seconds,
                records_processed=0,  # TODO: Add actual record count from ingestion
                job_name="bronze_ingestion",
                correlation_id=correlation_id,
                target_date=target_date.isoformat(),
            )

            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "status": "success",
                        "message": "Bronze layer ingestion completed successfully",
                        "target_date": target_date.isoformat(),
                        "dry_run": dry_run,
                        "duration_seconds": round(duration_seconds, 3),
                        "correlation_id": correlation_id,
                    }
                ),
            }
        else:
            logger.error(
                "Bronze layer ingestion failed",
                duration_in_seconds=duration_seconds,
                records_processed=0,
                job_name="bronze_ingestion",
                correlation_id=correlation_id,
                target_date=target_date.isoformat(),
            )

            return {
                "statusCode": 500,
                "body": json.dumps(
                    {
                        "status": "error",
                        "message": "Bronze layer ingestion failed",
                        "target_date": target_date.isoformat(),
                        "dry_run": dry_run,
                        "duration_seconds": round(duration_seconds, 3),
                        "correlation_id": correlation_id,
                    }
                ),
            }

    except Exception as e:
        # Calculate duration for failed execution
        end_time = datetime.utcnow()
        duration_seconds = (end_time - start_time).total_seconds()

        logger.error(
            f"Bronze layer ingestion failed with exception: {str(e)}",
            duration_in_seconds=duration_seconds,
            records_processed=0,
            job_name="bronze_ingestion",
            correlation_id=correlation_id,
            error_type=type(e).__name__,
            error_message=str(e),
        )

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "status": "error",
                    "message": f"Bronze layer ingestion failed: {str(e)}",
                    "error_type": type(e).__name__,
                    "duration_seconds": round(duration_seconds, 3),
                    "correlation_id": correlation_id,
                }
            ),
        }


def status_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda handler for checking bronze ingestion status.

    Args:
        event: Lambda event (unused for status checks)
        context: Lambda context object

    Returns:
        Dict containing status check results
    """
    correlation_id = context.aws_request_id

    logger.info(
        "Bronze ingestion status check started",
        correlation_id=correlation_id,
        function_name=context.function_name,
    )

    try:
        # Check if we can create ingestion instance (validates config)
        DateScopedIngestion()

        logger.info(
            "Bronze layer ingestion pipeline is ready", correlation_id=correlation_id
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "status": "healthy",
                    "message": "Bronze layer ingestion pipeline is ready",
                    "correlation_id": correlation_id,
                }
            ),
        }

    except Exception as e:
        logger.error(
            f"Bronze ingestion status check failed: {str(e)}",
            correlation_id=correlation_id,
            error_type=type(e).__name__,
            error_message=str(e),
        )

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "status": "unhealthy",
                    "message": f"Status check failed: {str(e)}",
                    "error_type": type(e).__name__,
                    "correlation_id": correlation_id,
                }
            ),
        }
