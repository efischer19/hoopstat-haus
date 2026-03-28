"""
S3 reader utilities for the health aggregator.

Provides two read-only operations:
1. Count quarantine files per day from the Bronze bucket's quarantine/ prefix.
2. Check the Gold latest.json artifact for last-modified timestamp to confirm
   Gold layer completion.
"""

import datetime as dt
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from hoopstat_observability import get_logger

logger = get_logger(__name__)

# Hive-partitioned quarantine prefix pattern: quarantine/year=YYYY/month=MM/day=DD/
QUARANTINE_PREFIX_TEMPLATE = "quarantine/year={year}/month={month:02d}/day={day:02d}/"

# Gold index artifact key
GOLD_INDEX_KEY = "served/index/latest.json"


class S3Reader:
    """
    Read-only S3 accessor for the health aggregator.

    Provides methods to count quarantine files and check Gold artifact freshness.
    All operations are read-only; no writes are performed here.
    """

    def __init__(
        self,
        bronze_bucket: str,
        gold_bucket: str,
        aws_region: str = "us-east-1",
        s3_client: Any = None,
    ) -> None:
        """
        Initialise the S3 reader.

        Args:
            bronze_bucket: S3 bucket name for the Bronze (ingestion) layer.
            gold_bucket: S3 bucket name for the Gold (analytics) layer.
            aws_region: AWS region for the S3 client.
            s3_client: Optional pre-built boto3 S3 client (useful in tests).
        """
        self.bronze_bucket = bronze_bucket
        self.gold_bucket = gold_bucket
        self.aws_region = aws_region
        self._client = s3_client or boto3.client("s3", region_name=aws_region)

    def count_quarantine_files(self, target_date: dt.date) -> int:
        """
        Count quarantine files for a specific day in the Bronze bucket.

        Handles missing/empty days gracefully — returns 0 if no files are found
        rather than raising an exception.

        Args:
            target_date: The date to count quarantine files for.

        Returns:
            Number of quarantine objects under the day's prefix.
        """
        prefix = QUARANTINE_PREFIX_TEMPLATE.format(
            year=target_date.year,
            month=target_date.month,
            day=target_date.day,
        )

        logger.info(
            f"Counting quarantine files: bucket={self.bronze_bucket} prefix={prefix}"
        )

        total = 0
        paginator = self._client.get_paginator("list_objects_v2")

        try:
            for page in paginator.paginate(Bucket=self.bronze_bucket, Prefix=prefix):
                total += page.get("KeyCount", 0)
        except (BotoCoreError, ClientError) as exc:
            # Log and treat as zero — a missing/inaccessible prefix should not
            # cause the entire aggregation run to fail.
            logger.warning(f"Could not list quarantine files for {target_date}: {exc}")
            return 0

        logger.info(f"Quarantine file count for {target_date}: {total}")
        return total

    def get_gold_index_last_modified(self) -> dt.datetime | None:
        """
        Retrieve the last-modified timestamp of the Gold index artifact.

        Checks whether ``served/index/latest.json`` exists in the Gold bucket
        and returns its last-modified time as a UTC-aware datetime.

        Returns:
            UTC-aware datetime of the last modification, or ``None`` if the
            artifact does not exist or is not accessible.
        """
        logger.info(
            f"Checking Gold index artifact: "
            f"bucket={self.gold_bucket} key={GOLD_INDEX_KEY}"
        )

        try:
            response = self._client.head_object(
                Bucket=self.gold_bucket, Key=GOLD_INDEX_KEY
            )
            last_modified: dt.datetime = response["LastModified"]
            # boto3 returns timezone-aware datetimes for LastModified
            logger.info(f"Gold index last modified: {last_modified.isoformat()}")
            return last_modified
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey"):
                logger.warning(
                    "Gold index artifact not found — Gold layer may not have run yet"
                )
            else:
                logger.warning(f"Could not check Gold index artifact: {exc}")
            return None
        except BotoCoreError as exc:
            logger.warning(f"Could not check Gold index artifact: {exc}")
            return None
