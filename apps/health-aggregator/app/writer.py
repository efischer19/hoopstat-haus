"""
S3 writer for the pipeline_health.json artifact.

Serialises the validated PipelineHealthReport Pydantic model to JSON and
writes it to the Gold bucket with the Cache-Control header mandated by
ADR-038 / ADR-040 (public, max-age=3600).
"""

import json
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from hoopstat_data.health_models import PipelineHealthReport
from hoopstat_observability import get_logger

logger = get_logger(__name__)

# Destination key in the Gold bucket per ADR-040
HEALTH_ARTIFACT_KEY = "served/health/pipeline_health.json"

# Cache-Control header: 1-hour TTL matching frontend asset caching per ADR-038
CACHE_CONTROL = "public, max-age=3600"


class HealthReportWriter:
    """
    Writes the validated PipelineHealthReport to S3.

    Serialises the Pydantic model to a UTF-8 JSON string and uploads it with
    the correct content-type and cache-control metadata.
    """

    def __init__(
        self,
        gold_bucket: str,
        aws_region: str = "us-east-1",
        s3_client: Any = None,
    ) -> None:
        """
        Initialise the writer.

        Args:
            gold_bucket: S3 bucket name for the Gold layer.
            aws_region: AWS region for the S3 client.
            s3_client: Optional pre-built boto3 S3 client (useful in tests).
        """
        self.gold_bucket = gold_bucket
        self.aws_region = aws_region
        self._client = s3_client or boto3.client("s3", region_name=aws_region)

    def write(self, report: PipelineHealthReport) -> None:
        """
        Serialise *report* to JSON and write it to the Gold S3 bucket.

        Uses Pydantic's ``model_dump(mode="json")`` to ensure all types
        (datetimes, enums, dates) are serialised to JSON-safe primitives
        before encoding.

        Args:
            report: Validated PipelineHealthReport to write.

        Raises:
            RuntimeError: If the S3 put_object call fails.
        """
        payload = report.model_dump(mode="json")
        body = json.dumps(payload, indent=2).encode("utf-8")

        logger.info(
            f"Writing pipeline_health.json: "
            f"bucket={self.gold_bucket} key={HEALTH_ARTIFACT_KEY} "
            f"size_bytes={len(body)}"
        )

        try:
            self._client.put_object(
                Bucket=self.gold_bucket,
                Key=HEALTH_ARTIFACT_KEY,
                Body=body,
                ContentType="application/json",
                CacheControl=CACHE_CONTROL,
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(
                f"Failed to write pipeline_health.json to S3: {exc}"
            ) from exc

        logger.info(
            "pipeline_health.json written successfully: "
            f"s3://{self.gold_bucket}/{HEALTH_ARTIFACT_KEY}"
        )
