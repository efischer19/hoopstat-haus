"""Tests for quarantine error classification."""

import json
from datetime import date, datetime
from unittest.mock import Mock, patch

from app.quarantine import (
    DataQuarantine,
    ErrorClassification,
    classify_quarantine_error,
)


class TestErrorClassification:
    """Test the ErrorClassification enum."""

    def test_enum_values(self):
        """Test that all required classification values exist."""
        assert ErrorClassification.TRANSIENT.value == "transient"
        assert ErrorClassification.ROUNDING_MISMATCH.value == "rounding_mismatch"
        assert ErrorClassification.SCHEMA_CHANGE.value == "schema_change"
        assert ErrorClassification.DATA_QUALITY.value == "data_quality"
        assert ErrorClassification.UNKNOWN.value == "unknown"

    def test_enum_has_exactly_five_members(self):
        """Test that the enum has exactly the five required members."""
        assert len(ErrorClassification) == 5


class TestClassifyQuarantineError:
    """Test the classify_quarantine_error function."""

    def test_transient_timeout(self):
        """Test classification of timeout errors as TRANSIENT."""
        result = {"issues": ["Request timeout after 30 seconds"]}
        assert classify_quarantine_error(result) == ErrorClassification.TRANSIENT

    def test_transient_connection(self):
        """Test classification of connection errors as TRANSIENT."""
        result = {"issues": ["Connection refused by remote host"]}
        assert classify_quarantine_error(result) == ErrorClassification.TRANSIENT

    def test_transient_rate_limit(self):
        """Test classification of rate limit errors as TRANSIENT."""
        result = {"issues": ["Rate limit exceeded, please retry later"]}
        assert classify_quarantine_error(result) == ErrorClassification.TRANSIENT

    def test_transient_503(self):
        """Test classification of 503 errors as TRANSIENT."""
        result = {"issues": ["HTTP 503 Service Unavailable"]}
        assert classify_quarantine_error(result) == ErrorClassification.TRANSIENT

    def test_transient_502(self):
        """Test classification of 502 errors as TRANSIENT."""
        result = {"issues": ["HTTP 502 Bad Gateway"]}
        assert classify_quarantine_error(result) == ErrorClassification.TRANSIENT

    def test_transient_retry(self):
        """Test classification of retry-related errors as TRANSIENT."""
        result = {"issues": ["Failed after retry attempts"]}
        assert classify_quarantine_error(result) == ErrorClassification.TRANSIENT

    def test_rounding_mismatch_rounding(self):
        """Test classification of rounding errors as ROUNDING_MISMATCH."""
        result = {"issues": ["Rounding error in player stats"]}
        assert (
            classify_quarantine_error(result) == ErrorClassification.ROUNDING_MISMATCH
        )

    def test_rounding_mismatch_sum(self):
        """Test classification of sum errors as ROUNDING_MISMATCH."""
        result = {"issues": ["Player stats sum does not equal team total"]}
        assert (
            classify_quarantine_error(result) == ErrorClassification.ROUNDING_MISMATCH
        )

    def test_rounding_mismatch_mismatch(self):
        """Test classification of mismatch errors as ROUNDING_MISMATCH."""
        result = {"issues": ["Points mismatch between player and team aggregates"]}
        assert (
            classify_quarantine_error(result) == ErrorClassification.ROUNDING_MISMATCH
        )

    def test_rounding_mismatch_tolerance(self):
        """Test classification of tolerance errors as ROUNDING_MISMATCH."""
        result = {"issues": ["Value exceeds tolerance threshold"]}
        assert (
            classify_quarantine_error(result) == ErrorClassification.ROUNDING_MISMATCH
        )

    def test_rounding_mismatch_aggregate(self):
        """Test classification of aggregate errors as ROUNDING_MISMATCH."""
        result = {"issues": ["Aggregate stats inconsistency detected"]}
        assert (
            classify_quarantine_error(result) == ErrorClassification.ROUNDING_MISMATCH
        )

    def test_schema_change_schema(self):
        """Test classification of schema errors as SCHEMA_CHANGE."""
        result = {"issues": ["Schema validation failed: missing key"]}
        assert classify_quarantine_error(result) == ErrorClassification.SCHEMA_CHANGE

    def test_schema_change_unexpected_field(self):
        """Test classification of unexpected field errors as SCHEMA_CHANGE."""
        result = {"issues": ["Unexpected field 'newField' in response"]}
        assert classify_quarantine_error(result) == ErrorClassification.SCHEMA_CHANGE

    def test_schema_change_missing_required(self):
        """Test classification of missing required field errors as SCHEMA_CHANGE."""
        result = {"issues": ["Missing required field 'gameId'"]}
        assert classify_quarantine_error(result) == ErrorClassification.SCHEMA_CHANGE

    def test_schema_change_format_change(self):
        """Test classification of format change errors as SCHEMA_CHANGE."""
        result = {"issues": ["Detected format change in API response"]}
        assert classify_quarantine_error(result) == ErrorClassification.SCHEMA_CHANGE

    def test_data_quality_missing(self):
        """Test classification of missing data as DATA_QUALITY."""
        result = {"issues": ["Missing player name in record"]}
        assert classify_quarantine_error(result) == ErrorClassification.DATA_QUALITY

    def test_data_quality_invalid(self):
        """Test classification of invalid data as DATA_QUALITY."""
        result = {"issues": ["Invalid game ID format: abc"]}
        assert classify_quarantine_error(result) == ErrorClassification.DATA_QUALITY

    def test_data_quality_out_of_range(self):
        """Test classification of out of range errors as DATA_QUALITY."""
        result = {"issues": ["Score out of range: 999"]}
        assert classify_quarantine_error(result) == ErrorClassification.DATA_QUALITY

    def test_data_quality_null(self):
        """Test classification of null value errors as DATA_QUALITY."""
        result = {"issues": ["Null value found for required field"]}
        assert classify_quarantine_error(result) == ErrorClassification.DATA_QUALITY

    def test_unknown_no_issues(self):
        """Test UNKNOWN classification when no issues are present."""
        result = {"issues": []}
        assert classify_quarantine_error(result) == ErrorClassification.UNKNOWN

    def test_unknown_missing_issues_key(self):
        """Test UNKNOWN classification when issues key is missing."""
        result = {}
        assert classify_quarantine_error(result) == ErrorClassification.UNKNOWN

    def test_unknown_unrecognized_issue(self):
        """Test UNKNOWN classification for unrecognized issue strings."""
        result = {"issues": ["Something completely unexpected happened"]}
        assert classify_quarantine_error(result) == ErrorClassification.UNKNOWN

    def test_case_insensitive_matching(self):
        """Test that keyword matching is case-insensitive."""
        result = {"issues": ["SCHEMA validation FAILED"]}
        assert classify_quarantine_error(result) == ErrorClassification.SCHEMA_CHANGE

    def test_multiple_issues_most_severe_wins(self):
        """Test that the most severe classification wins with multiple issues."""
        result = {
            "issues": [
                "Request timeout after 30 seconds",  # TRANSIENT
                "Schema validation failed",  # SCHEMA_CHANGE
            ]
        }
        assert classify_quarantine_error(result) == ErrorClassification.SCHEMA_CHANGE

    def test_multiple_issues_data_quality_over_transient(self):
        """Test DATA_QUALITY is more severe than TRANSIENT."""
        result = {
            "issues": [
                "Connection error occurred",  # TRANSIENT
                "Invalid game ID format",  # DATA_QUALITY
            ]
        }
        assert classify_quarantine_error(result) == ErrorClassification.DATA_QUALITY

    def test_multiple_issues_data_quality_over_rounding(self):
        """Test DATA_QUALITY is more severe than ROUNDING_MISMATCH."""
        result = {
            "issues": [
                "Rounding error in stats",  # ROUNDING_MISMATCH
                "Invalid value detected",  # DATA_QUALITY
            ]
        }
        assert classify_quarantine_error(result) == ErrorClassification.DATA_QUALITY

    def test_multiple_issues_rounding_over_transient(self):
        """Test ROUNDING_MISMATCH is more severe than TRANSIENT."""
        result = {
            "issues": [
                "Request timeout",  # TRANSIENT
                "Sum of player stats does not match team total",  # ROUNDING_MISMATCH
            ]
        }
        assert (
            classify_quarantine_error(result) == ErrorClassification.ROUNDING_MISMATCH
        )

    def test_multiple_issues_schema_over_data_quality(self):
        """Test SCHEMA_CHANGE is more severe than DATA_QUALITY."""
        result = {
            "issues": [
                "Missing field in response",  # DATA_QUALITY
                "Schema structure changed",  # SCHEMA_CHANGE
            ]
        }
        assert classify_quarantine_error(result) == ErrorClassification.SCHEMA_CHANGE

    def test_mixed_known_and_unknown_issues(self):
        """Test that known issues are classified even alongside unknown ones."""
        result = {
            "issues": [
                "Something completely unknown",
                "Connection refused",  # TRANSIENT
            ]
        }
        assert classify_quarantine_error(result) == ErrorClassification.TRANSIENT

    def test_all_severity_levels_present(self):
        """Test that SCHEMA_CHANGE wins when all severity levels are present."""
        result = {
            "issues": [
                "Request timeout",  # TRANSIENT
                "Sum mismatch detected",  # ROUNDING_MISMATCH
                "Invalid value",  # DATA_QUALITY
                "Schema validation failed",  # SCHEMA_CHANGE
            ]
        }
        assert classify_quarantine_error(result) == ErrorClassification.SCHEMA_CHANGE


class TestQuarantineDataWithClassification:
    """Test that quarantine_data includes error classification in metadata."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_s3_manager = Mock()
        self.mock_s3_manager.bucket_name = "test-bucket"
        self.mock_s3_manager.s3_client = Mock()
        self.quarantine = DataQuarantine(self.mock_s3_manager)

    def test_quarantine_data_includes_classification(self):
        """Test that quarantine record metadata includes error_classification."""
        test_data = {"invalid": "data"}
        validation_result = {
            "valid": False,
            "issues": ["Schema validation failed"],
        }

        with patch("app.quarantine.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 12, 25, 10, 30, 0)

            self.quarantine.quarantine_data(
                test_data, validation_result, "schedule", date(2023, 12, 25)
            )

        # Extract the stored JSON body
        call_args = self.mock_s3_manager.s3_client.put_object.call_args
        body = json.loads(call_args[1]["Body"].decode("utf-8"))

        assert body["metadata"]["error_classification"] == "schema_change"

    def test_quarantine_data_transient_classification(self):
        """Test classification for transient errors in quarantine record."""
        test_data = {"response": "error"}
        validation_result = {
            "valid": False,
            "issues": ["Connection timeout occurred"],
        }

        with patch("app.quarantine.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 12, 25, 10, 30, 0)

            self.quarantine.quarantine_data(
                test_data, validation_result, "box_score", date(2023, 12, 25)
            )

        call_args = self.mock_s3_manager.s3_client.put_object.call_args
        body = json.loads(call_args[1]["Body"].decode("utf-8"))

        assert body["metadata"]["error_classification"] == "transient"

    def test_quarantine_data_unknown_classification(self):
        """Test classification defaults to unknown for unrecognized issues."""
        test_data = {"data": "something"}
        validation_result = {
            "valid": False,
            "issues": ["Completely unrecognized problem"],
        }

        with patch("app.quarantine.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 12, 25, 10, 30, 0)

            self.quarantine.quarantine_data(
                test_data, validation_result, "schedule", date(2023, 12, 25)
            )

        call_args = self.mock_s3_manager.s3_client.put_object.call_args
        body = json.loads(call_args[1]["Body"].decode("utf-8"))

        assert body["metadata"]["error_classification"] == "unknown"

    def test_quarantine_data_multi_issue_severity(self):
        """Test that multi-issue records get the most severe classification."""
        test_data = {"data": "mixed"}
        validation_result = {
            "valid": False,
            "issues": [
                "Connection timeout",  # TRANSIENT
                "Invalid field value",  # DATA_QUALITY
            ],
        }

        with patch("app.quarantine.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 12, 25, 10, 30, 0)

            self.quarantine.quarantine_data(
                test_data, validation_result, "schedule", date(2023, 12, 25)
            )

        call_args = self.mock_s3_manager.s3_client.put_object.call_args
        body = json.loads(call_args[1]["Body"].decode("utf-8"))

        assert body["metadata"]["error_classification"] == "data_quality"
