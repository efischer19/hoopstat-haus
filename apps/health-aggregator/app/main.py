"""
Lambda handler entry point for the health aggregator.

Invoked once daily (EventBridge schedule) after Gold processing completes.
Aggregates pipeline telemetry from CloudWatch Logs and S3, then writes
pipeline_health.json to the Gold S3 bucket.
"""

import os
from typing import Any

from hoopstat_observability import get_logger

from .aggregator import HealthAggregator
from .cloudwatch import CloudWatchClient
from .s3_reader import S3Reader
from .writer import HealthReportWriter

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    AWS Lambda entry point for the health aggregator.

    Reads configuration from environment variables, runs the aggregation
    pipeline, and writes pipeline_health.json to S3.  Handles failures
    gracefully: on CloudWatch query errors a degraded-status report is
    written rather than leaving the artifact stale or absent.

    Environment variables:
        BRONZE_BUCKET: S3 bucket name for the Bronze layer.
        GOLD_BUCKET: S3 bucket name for the Gold layer.
        AWS_REGION: AWS region (default: us-east-1).

    Args:
        event: EventBridge scheduled event (contents not used).
        context: Lambda runtime context (not used).

    Returns:
        Response dict with statusCode and body.
    """
    logger.info("Health aggregator Lambda triggered")

    aws_region = os.getenv("AWS_REGION", "us-east-1")
    bronze_bucket = os.getenv("BRONZE_BUCKET")
    gold_bucket = os.getenv("GOLD_BUCKET")

    if not bronze_bucket:
        error = "BRONZE_BUCKET environment variable is not set"
        logger.error(error)
        return {"statusCode": 500, "body": {"error": error}}

    if not gold_bucket:
        error = "GOLD_BUCKET environment variable is not set"
        logger.error(error)
        return {"statusCode": 500, "body": {"error": error}}

    try:
        cw_client = CloudWatchClient(aws_region=aws_region)
        s3_reader = S3Reader(
            bronze_bucket=bronze_bucket,
            gold_bucket=gold_bucket,
            aws_region=aws_region,
        )
        writer = HealthReportWriter(gold_bucket=gold_bucket, aws_region=aws_region)
        aggregator = HealthAggregator(cw_client=cw_client, s3_reader=s3_reader)

        report = aggregator.aggregate()
        writer.write(report)

        return {
            "statusCode": 200,
            "body": {
                "message": "pipeline_health.json written successfully",
                "overall_status": report.overall_status,
                "generated_at": report.generated_at.isoformat(),
            },
        }

    except Exception as exc:
        logger.error(f"Health aggregator Lambda failed: {exc}")
        return {"statusCode": 500, "body": {"error": str(exc)}}
