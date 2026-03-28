"""
Tests for the CloudWatch Logs Insights client.

Validates that the client correctly starts queries, polls for results,
parses rows, and raises CloudWatchQueryError on failure/timeout conditions.
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.cloudwatch import CloudWatchClient, CloudWatchQueryError, _parse_query_results


class TestParseQueryResults:
    """Unit tests for the _parse_query_results helper."""

    def test_empty_results(self):
        assert _parse_query_results([]) == []

    def test_single_row(self):
        raw = [
            [
                {"field": "stage", "value": "bronze"},
                {"field": "status", "value": "success"},
            ]
        ]
        result = _parse_query_results(raw)
        assert result == [{"stage": "bronze", "status": "success"}]

    def test_multiple_rows(self):
        raw = [
            [
                {"field": "stage", "value": "bronze"},
                {"field": "status", "value": "success"},
            ],
            [
                {"field": "stage", "value": "silver"},
                {"field": "status", "value": "failed"},
            ],
        ]
        result = _parse_query_results(raw)
        assert len(result) == 2
        assert result[0]["stage"] == "bronze"
        assert result[1]["stage"] == "silver"


class TestCloudWatchClient:
    """Tests for the CloudWatchClient class."""

    def _make_client(self, logs_mock):
        return CloudWatchClient(aws_region="us-east-1", logs_client=logs_mock)

    def test_query_pipeline_status_success(self):
        """Happy-path: query starts, completes, returns parsed rows."""
        logs_mock = MagicMock()
        logs_mock.start_query.return_value = {"queryId": "qid-123"}
        logs_mock.get_query_results.return_value = {
            "status": "Complete",
            "results": [
                [
                    {"field": "stage", "value": "bronze"},
                    {"field": "status", "value": "success"},
                    {"field": "execution_date", "value": "2024-01-15 00:00:00.000"},
                ]
            ],
        }

        client = self._make_client(logs_mock)
        rows = client.query_pipeline_status(lookback_days=7)

        logs_mock.start_query.assert_called_once()
        assert len(rows) == 1
        assert rows[0]["stage"] == "bronze"
        assert rows[0]["status"] == "success"

    def test_query_pipeline_status_polls_until_complete(self):
        """Client should poll until status is Complete."""
        logs_mock = MagicMock()
        logs_mock.start_query.return_value = {"queryId": "qid-456"}
        # First call returns Running, second returns Complete
        logs_mock.get_query_results.side_effect = [
            {"status": "Running", "results": []},
            {"status": "Complete", "results": []},
        ]

        client = self._make_client(logs_mock)
        with patch("app.cloudwatch.time.sleep"):
            rows = client.query_pipeline_status(lookback_days=7)

        assert logs_mock.get_query_results.call_count == 2
        assert rows == []

    def test_query_pipeline_status_failed(self):
        """CloudWatchQueryError is raised when query status is Failed."""
        logs_mock = MagicMock()
        logs_mock.start_query.return_value = {"queryId": "qid-789"}
        logs_mock.get_query_results.return_value = {"status": "Failed", "results": []}

        client = self._make_client(logs_mock)
        with pytest.raises(CloudWatchQueryError, match="Failed"):
            client.query_pipeline_status()

    def test_query_pipeline_status_cancelled(self):
        """CloudWatchQueryError is raised when query status is Cancelled."""
        logs_mock = MagicMock()
        logs_mock.start_query.return_value = {"queryId": "qid-abc"}
        logs_mock.get_query_results.return_value = {
            "status": "Cancelled",
            "results": [],
        }

        client = self._make_client(logs_mock)
        with pytest.raises(CloudWatchQueryError, match="Cancelled"):
            client.query_pipeline_status()

    def test_query_pipeline_status_timeout(self):
        """CloudWatchQueryError is raised when the query exceeds the timeout."""
        logs_mock = MagicMock()
        logs_mock.start_query.return_value = {"queryId": "qid-timeout"}
        # Always return Running
        logs_mock.get_query_results.return_value = {"status": "Running", "results": []}

        client = self._make_client(logs_mock)
        # Patch both sleep and the timeout constant to keep the test fast
        with (
            patch("app.cloudwatch.time.sleep"),
            patch("app.cloudwatch.QUERY_TIMEOUT_SECONDS", 4),
            patch("app.cloudwatch.QUERY_POLL_INTERVAL_SECONDS", 2),
        ):
            with pytest.raises(CloudWatchQueryError, match="timed out"):
                client.query_pipeline_status()

    def test_start_query_client_error(self):
        """CloudWatchQueryError is raised when start_query raises ClientError."""
        logs_mock = MagicMock()
        logs_mock.start_query.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Denied"}},
            "StartQuery",
        )

        client = self._make_client(logs_mock)
        with pytest.raises(CloudWatchQueryError, match="Failed to start"):
            client.query_pipeline_status()

    def test_get_query_results_client_error(self):
        """CloudWatchQueryError is raised when get_query_results raises ClientError."""
        logs_mock = MagicMock()
        logs_mock.start_query.return_value = {"queryId": "qid-err"}
        logs_mock.get_query_results.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ServiceUnavailableException",
                    "Message": "Unavailable",
                }
            },
            "GetQueryResults",
        )

        client = self._make_client(logs_mock)
        with pytest.raises(CloudWatchQueryError, match="Failed to retrieve"):
            client.query_pipeline_status()
