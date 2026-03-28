"""
Tests for the Lambda handler entry point (app/main.py).

Validates environment variable handling, successful aggregation flow,
and graceful error handling.
"""

from unittest.mock import MagicMock, patch

from app.main import lambda_handler


class TestLambdaHandler:
    """Tests for the lambda_handler function."""

    def test_missing_bronze_bucket_returns_500(self, monkeypatch):
        """Returns 500 when BRONZE_BUCKET is not set."""
        monkeypatch.delenv("BRONZE_BUCKET", raising=False)
        monkeypatch.delenv("GOLD_BUCKET", raising=False)

        response = lambda_handler({}, MagicMock())

        assert response["statusCode"] == 500
        assert "BRONZE_BUCKET" in response["body"]["error"]

    def test_missing_gold_bucket_returns_500(self, monkeypatch):
        """Returns 500 when GOLD_BUCKET is not set."""
        monkeypatch.setenv("BRONZE_BUCKET", "test-bronze")
        monkeypatch.delenv("GOLD_BUCKET", raising=False)

        response = lambda_handler({}, MagicMock())

        assert response["statusCode"] == 500
        assert "GOLD_BUCKET" in response["body"]["error"]

    @patch("app.main.HealthAggregator")
    @patch("app.main.HealthReportWriter")
    @patch("app.main.S3Reader")
    @patch("app.main.CloudWatchClient")
    def test_successful_aggregation_returns_200(
        self,
        mock_cw_class,
        mock_s3_class,
        mock_writer_class,
        mock_aggregator_class,
        monkeypatch,
    ):
        """Returns 200 with report metadata on successful aggregation."""
        import datetime as dt

        from hoopstat_data.health_models import OverallSystemStatus

        monkeypatch.setenv("BRONZE_BUCKET", "test-bronze")
        monkeypatch.setenv("GOLD_BUCKET", "test-gold")

        # Mock the report returned by aggregate()
        mock_report = MagicMock()
        mock_report.overall_status = OverallSystemStatus.OPERATIONAL
        mock_report.generated_at = dt.datetime(2024, 1, 15, 12, 0, 0, tzinfo=dt.UTC)

        mock_aggregator = MagicMock()
        mock_aggregator.aggregate.return_value = mock_report
        mock_aggregator_class.return_value = mock_aggregator

        mock_writer = MagicMock()
        mock_writer_class.return_value = mock_writer

        response = lambda_handler({}, MagicMock())

        assert response["statusCode"] == 200
        assert "message" in response["body"]
        assert response["body"]["overall_status"] == OverallSystemStatus.OPERATIONAL
        mock_writer.write.assert_called_once_with(mock_report)

    @patch("app.main.HealthAggregator")
    @patch("app.main.HealthReportWriter")
    @patch("app.main.S3Reader")
    @patch("app.main.CloudWatchClient")
    def test_unexpected_exception_returns_500(
        self,
        mock_cw_class,
        mock_s3_class,
        mock_writer_class,
        mock_aggregator_class,
        monkeypatch,
    ):
        """Returns 500 when an unexpected exception occurs."""
        monkeypatch.setenv("BRONZE_BUCKET", "test-bronze")
        monkeypatch.setenv("GOLD_BUCKET", "test-gold")

        mock_aggregator = MagicMock()
        mock_aggregator.aggregate.side_effect = RuntimeError("Unexpected failure")
        mock_aggregator_class.return_value = mock_aggregator

        response = lambda_handler({}, MagicMock())

        assert response["statusCode"] == 500
        assert "error" in response["body"]
        assert "Unexpected failure" in response["body"]["error"]

    @patch("app.main.HealthAggregator")
    @patch("app.main.HealthReportWriter")
    @patch("app.main.S3Reader")
    @patch("app.main.CloudWatchClient")
    def test_uses_aws_region_env_var(
        self,
        mock_cw_class,
        mock_s3_class,
        mock_writer_class,
        mock_aggregator_class,
        monkeypatch,
    ):
        """CloudWatchClient and S3Reader receive the AWS_REGION from env."""
        import datetime as dt

        from hoopstat_data.health_models import OverallSystemStatus

        monkeypatch.setenv("BRONZE_BUCKET", "test-bronze")
        monkeypatch.setenv("GOLD_BUCKET", "test-gold")
        monkeypatch.setenv("AWS_REGION", "eu-west-1")

        mock_report = MagicMock()
        mock_report.overall_status = OverallSystemStatus.OPERATIONAL
        mock_report.generated_at = dt.datetime(2024, 1, 15, tzinfo=dt.UTC)

        mock_aggregator = MagicMock()
        mock_aggregator.aggregate.return_value = mock_report
        mock_aggregator_class.return_value = mock_aggregator
        mock_writer_class.return_value = MagicMock()

        lambda_handler({}, MagicMock())

        mock_cw_class.assert_called_once_with(aws_region="eu-west-1")
        mock_s3_class.assert_called_once_with(
            bronze_bucket="test-bronze",
            gold_bucket="test-gold",
            aws_region="eu-west-1",
        )
