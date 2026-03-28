"""
CloudWatch Logs Insights queries for pipeline telemetry aggregation.

Queries the /hoopstat-haus/data-pipeline log group for Bronze, Silver, and Gold
pipeline execution outcomes across a rolling window of days.
"""

import time
from datetime import UTC, datetime, timedelta
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from hoopstat_observability import get_logger

logger = get_logger(__name__)

# Log group shared by all pipeline Lambdas per ADR-018
LOG_GROUP = "/hoopstat-haus/data-pipeline"

# Maximum seconds to wait for a CloudWatch Insights query to complete
QUERY_TIMEOUT_SECONDS = 60

# Polling interval while waiting for query results
QUERY_POLL_INTERVAL_SECONDS = 2

# CloudWatch Insights query to retrieve daily pipeline stage outcomes
# Returns one row per (date, stage) with the terminal status for that stage.
PIPELINE_STATUS_QUERY = """
fields @timestamp, stage, status, records_ingested, records_processed,
       records_quarantined, artifacts_written
| filter ispresent(stage) and ispresent(status)
| stats
    latest(status) as status,
    max(coalesce(records_ingested, 0)) as records_ingested,
    max(coalesce(records_processed, 0)) as records_processed,
    max(coalesce(records_quarantined, 0)) as records_quarantined,
    max(coalesce(artifacts_written, 0)) as artifacts_written
  by datefloor(@timestamp, 1d) as execution_date, stage
| sort execution_date desc
"""


class CloudWatchQueryError(Exception):
    """Raised when a CloudWatch Logs Insights query fails or times out."""


class CloudWatchClient:
    """
    Client for querying CloudWatch Logs Insights.

    Encapsulates start_query / get_query_results polling so callers receive
    a clean list of result rows without dealing with the async lifecycle.
    """

    def __init__(
        self,
        aws_region: str = "us-east-1",
        logs_client: Any = None,
    ) -> None:
        """
        Initialise the CloudWatch client.

        Args:
            aws_region: AWS region for the CloudWatch Logs client.
            logs_client: Optional pre-built boto3 logs client (useful in tests).
        """
        self.aws_region = aws_region
        self._client = logs_client or boto3.client("logs", region_name=aws_region)

    def query_pipeline_status(self, lookback_days: int = 7) -> list[dict[str, str]]:
        """
        Query the pipeline log group for execution status over the last N days.

        Args:
            lookback_days: Number of days to look back (default 7).

        Returns:
            List of result rows.  Each row is a dict mapping field name to
            string value as returned by CloudWatch Logs Insights.

        Raises:
            CloudWatchQueryError: If the query fails or times out.
        """
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=lookback_days)

        logger.info(
            f"Querying CloudWatch Logs Insights: log_group={LOG_GROUP} "
            f"start={start_time.isoformat()} end={end_time.isoformat()}"
        )

        try:
            response = self._client.start_query(
                logGroupName=LOG_GROUP,
                startTime=int(start_time.timestamp()),
                endTime=int(end_time.timestamp()),
                queryString=PIPELINE_STATUS_QUERY,
            )
        except (BotoCoreError, ClientError) as exc:
            raise CloudWatchQueryError(
                f"Failed to start CloudWatch Logs Insights query: {exc}"
            ) from exc

        query_id = response["queryId"]
        logger.info(f"Started CloudWatch query: query_id={query_id}")

        return self._wait_for_results(query_id)

    def _wait_for_results(self, query_id: str) -> list[dict[str, str]]:
        """
        Poll CloudWatch until the query finishes, then return parsed rows.

        Args:
            query_id: The CloudWatch Logs Insights query ID.

        Returns:
            List of result rows as dicts.

        Raises:
            CloudWatchQueryError: If the query fails, is cancelled, or times out.
        """
        elapsed = 0.0

        while elapsed < QUERY_TIMEOUT_SECONDS:
            try:
                result = self._client.get_query_results(queryId=query_id)
            except (BotoCoreError, ClientError) as exc:
                raise CloudWatchQueryError(
                    f"Failed to retrieve CloudWatch query results: {exc}"
                ) from exc

            status = result.get("status", "")

            if status == "Complete":
                raw_results = result.get("results", [])
                parsed = _parse_query_results(raw_results)
                logger.info(
                    f"CloudWatch query complete: query_id={query_id} rows={len(parsed)}"
                )
                return parsed

            if status in ("Failed", "Cancelled", "Timeout"):
                raise CloudWatchQueryError(
                    f"CloudWatch query ended with status '{status}': "
                    f"query_id={query_id}"
                )

            # Query is still running — wait and retry
            time.sleep(QUERY_POLL_INTERVAL_SECONDS)
            elapsed += QUERY_POLL_INTERVAL_SECONDS

        raise CloudWatchQueryError(
            f"CloudWatch query timed out after {QUERY_TIMEOUT_SECONDS}s: "
            f"query_id={query_id}"
        )


def _parse_query_results(
    raw_results: list[list[dict[str, str]]],
) -> list[dict[str, str]]:
    """
    Flatten the nested CloudWatch Logs Insights result format into plain dicts.

    CloudWatch returns results as::

        [
            [
                {"field": "stage", "value": "bronze"},
                {"field": "status", "value": "success"},
            ],
            ...
        ]

    This function converts each inner list into a ``{field: value}`` dict.

    Args:
        raw_results: Nested list of ``{field, value}`` pairs from CloudWatch.

    Returns:
        List of flat ``{field_name: value}`` dicts.
    """
    rows = []
    for record in raw_results:
        row = {item["field"]: item["value"] for item in record}
        rows.append(row)
    return rows
