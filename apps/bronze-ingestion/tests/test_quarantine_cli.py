"""Tests for the quarantine CLI commands."""

import json
from datetime import date
from unittest.mock import Mock, patch

from click.testing import CliRunner

from app.main import cli
from app.quarantine_cli import (
    _format_classification,
    _format_inspect,
    _format_summary,
    _format_table,
    _is_transient,
    _parse_data_type_from_key,
    _parse_date_from_key,
)


class TestClassificationFormatting:
    """Test error classification display formatting."""

    def test_format_transient(self):
        """Transient errors are labeled replay-safe."""
        result = _format_classification("transient")
        assert result == "[REPLAY-SAFE] TRANSIENT"

    def test_format_rounding_mismatch(self):
        """Rounding mismatches are labeled for investigation."""
        result = _format_classification("rounding_mismatch")
        assert result == "[INVESTIGATE] ROUNDING_MISMATCH"

    def test_format_schema_change(self):
        """Schema changes are labeled for investigation."""
        result = _format_classification("schema_change")
        assert result == "[INVESTIGATE] SCHEMA_CHANGE"

    def test_format_data_quality(self):
        """Data quality issues are labeled for investigation."""
        result = _format_classification("data_quality")
        assert result == "[INVESTIGATE] DATA_QUALITY"

    def test_format_unknown(self):
        """Unknown errors are labeled for investigation."""
        result = _format_classification("unknown")
        assert result == "[INVESTIGATE] UNKNOWN"

    def test_format_invalid_classification(self):
        """Invalid classification values are handled gracefully."""
        result = _format_classification("something_else")
        assert "[INVESTIGATE]" in result
        assert "SOMETHING_ELSE" in result

    def test_is_transient_true(self):
        """Transient classification is detected correctly."""
        assert _is_transient("transient") is True

    def test_is_transient_false(self):
        """Non-transient classifications return False."""
        assert _is_transient("schema_change") is False
        assert _is_transient("rounding_mismatch") is False
        assert _is_transient("data_quality") is False
        assert _is_transient("unknown") is False


class TestKeyParsing:
    """Test S3 key parsing helpers."""

    def test_parse_date_from_key(self):
        """Date is correctly extracted from S3 key."""
        key = "quarantine/year=2023/month=12/day=25/schedule/file.json"
        assert _parse_date_from_key(key) == "2023-12-25"

    def test_parse_date_from_key_missing_parts(self):
        """Missing date parts use placeholder."""
        key = "quarantine/some/other/path.json"
        result = _parse_date_from_key(key)
        assert "?" in result

    def test_parse_data_type_from_key(self):
        """Data type is correctly extracted from S3 key."""
        key = "quarantine/year=2023/month=12/day=25/schedule/file.json"
        assert _parse_data_type_from_key(key) == "schedule"

    def test_parse_data_type_box_score(self):
        """Box score data type is correctly extracted."""
        key = "quarantine/year=2023/month=12/day=25/box_score/file.json"
        assert _parse_data_type_from_key(key) == "box_score"

    def test_parse_data_type_short_key(self):
        """Short keys return unknown data type."""
        key = "quarantine/file.json"
        assert _parse_data_type_from_key(key) == "unknown"


class TestTableFormatting:
    """Test table output formatting."""

    def test_format_table_empty(self):
        """Empty items produce a no-items message."""
        result = _format_table([])
        assert "No quarantined items found." in result

    def test_format_table_with_items(self):
        """Items are formatted as a readable table."""
        items = [
            {
                "date": "2023-12-25",
                "data_type": "schedule",
                "error_classification": "transient",
                "issues_count": 2,
                "key": "quarantine/year=2023/month=12/day=25/schedule/file.json",
            },
        ]
        result = _format_table(items)
        assert "Date" in result
        assert "Data Type" in result
        assert "Classification" in result
        assert "Issues" in result
        assert "S3 Key" in result
        assert "schedule" in result
        assert "[REPLAY-SAFE] TRANSIENT" in result

    def test_format_table_multiple_items(self):
        """Multiple items each get their own row."""
        items = [
            {
                "date": "2023-12-25",
                "data_type": "schedule",
                "error_classification": "transient",
                "issues_count": 1,
                "key": "quarantine/year=2023/month=12/day=25/schedule/f1.json",
            },
            {
                "date": "2023-12-25",
                "data_type": "box_score",
                "error_classification": "schema_change",
                "issues_count": 3,
                "key": "quarantine/year=2023/month=12/day=25/box_score/f2.json",
            },
        ]
        result = _format_table(items)
        assert "schedule" in result
        assert "box_score" in result
        assert "[REPLAY-SAFE] TRANSIENT" in result
        assert "[INVESTIGATE] SCHEMA_CHANGE" in result


class TestSummaryFormatting:
    """Test summary output formatting."""

    def test_format_summary_basic(self):
        """Summary includes totals and classification breakdown."""
        summary = {
            "total_quarantined": 3,
            "by_data_type": {"schedule": 1, "box_score": 2},
            "summary_date": "2023-12-25T10:00:00",
            "recent_items": [],
        }
        enriched = [
            {"error_classification": "transient"},
            {"error_classification": "schema_change"},
            {"error_classification": "schema_change"},
        ]
        result = _format_summary(summary, enriched)

        assert "Quarantine Summary" in result
        assert "Total quarantined: 3" in result
        assert "Replay-safe (transient): 1" in result
        assert "Requires investigation:  2" in result
        assert "schedule: 1" in result
        assert "box_score: 2" in result

    def test_format_summary_no_transient(self):
        """Summary shows zero transient count when none exist."""
        summary = {
            "total_quarantined": 1,
            "by_data_type": {"schedule": 1},
            "summary_date": "2023-12-25T10:00:00",
            "recent_items": [],
        }
        enriched = [{"error_classification": "data_quality"}]
        result = _format_summary(summary, enriched)
        assert "Replay-safe (transient): 0" in result
        assert "Requires investigation:  1" in result


class TestInspectFormatting:
    """Test inspect output formatting."""

    def test_format_inspect_basic(self):
        """Inspect output includes all metadata fields."""
        record = {
            "data": {"test": "payload"},
            "validation_result": {
                "valid": False,
                "issues": ["Schema validation failed", "Missing field: name"],
            },
            "metadata": {
                "data_type": "schedule",
                "target_date": "2023-12-25",
                "quarantine_timestamp": "2023-12-25T10:30:00",
                "error_classification": "schema_change",
                "issues_count": 2,
                "validation_valid": False,
                "context": {"api_endpoint": "get_games"},
            },
        }
        result = _format_inspect(record, full=False)

        assert "Quarantine Record Details" in result
        assert "schedule" in result
        assert "2023-12-25" in result
        assert "[INVESTIGATE] SCHEMA_CHANGE" in result
        assert "Schema validation failed" in result
        assert "Missing field: name" in result
        assert "api_endpoint" in result

    def test_format_inspect_truncated_payload(self):
        """Large payloads are truncated by default."""
        large_data = {"field": "x" * 1000}
        record = {
            "data": large_data,
            "validation_result": {"valid": False, "issues": ["Error"]},
            "metadata": {
                "data_type": "box_score",
                "target_date": "2023-12-25",
                "quarantine_timestamp": "2023-12-25T10:30:00",
                "error_classification": "transient",
                "issues_count": 1,
                "validation_valid": False,
                "context": {},
            },
        }
        result = _format_inspect(record, full=False)
        assert "truncated" in result
        assert "--full" in result

    def test_format_inspect_full_payload(self):
        """Full flag shows complete payload."""
        large_data = {"field": "x" * 1000}
        record = {
            "data": large_data,
            "validation_result": {"valid": False, "issues": ["Error"]},
            "metadata": {
                "data_type": "box_score",
                "target_date": "2023-12-25",
                "quarantine_timestamp": "2023-12-25T10:30:00",
                "error_classification": "transient",
                "issues_count": 1,
                "validation_valid": False,
                "context": {},
            },
        }
        result = _format_inspect(record, full=True)
        assert "truncated" not in result
        assert "x" * 1000 in result

    def test_format_inspect_no_data(self):
        """Missing payload data is handled."""
        record = {
            "data": None,
            "validation_result": {"valid": False, "issues": []},
            "metadata": {
                "data_type": "schedule",
                "target_date": "2023-12-25",
                "quarantine_timestamp": "2023-12-25T10:30:00",
                "error_classification": "unknown",
                "issues_count": 0,
                "validation_valid": False,
                "context": {},
            },
        }
        result = _format_inspect(record, full=False)
        assert "No payload data recorded." in result

    def test_format_inspect_no_issues(self):
        """Empty issues list is handled."""
        record = {
            "data": {"test": "data"},
            "validation_result": {"valid": True, "issues": []},
            "metadata": {
                "data_type": "schedule",
                "target_date": "2023-12-25",
                "quarantine_timestamp": "2023-12-25T10:30:00",
                "error_classification": "unknown",
                "issues_count": 0,
                "validation_valid": True,
                "context": {},
            },
        }
        result = _format_inspect(record, full=False)
        assert "No issues recorded." in result


class TestQuarantineListCommand:
    """Test the quarantine list CLI command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("app.quarantine_cli._get_quarantine")
    def test_list_no_items(self, mock_get_q):
        """List command with no quarantined items."""
        mock_q = Mock()
        mock_q.list_quarantined_data.return_value = []
        mock_get_q.return_value = mock_q

        result = self.runner.invoke(cli, ["quarantine", "list"])
        assert result.exit_code == 0
        assert "No quarantined items found." in result.output

    @patch("app.quarantine_cli._get_quarantine")
    def test_list_with_items(self, mock_get_q):
        """List command displays items in table format."""
        mock_q = Mock()
        mock_q.list_quarantined_data.return_value = [
            {
                "key": "quarantine/year=2023/month=12/day=25/schedule/file1.json",
                "size": 1024,
                "last_modified": "2023-12-25T10:00:00",
                "metadata": {},
            },
        ]
        # Mock the S3 get_object for enrichment
        mock_q.s3_manager.s3_client.get_object.return_value = {
            "Body": Mock(
                read=Mock(
                    return_value=json.dumps(
                        {
                            "data": {},
                            "metadata": {
                                "error_classification": "transient",
                                "issues_count": 2,
                            },
                        }
                    ).encode("utf-8")
                )
            )
        }
        mock_get_q.return_value = mock_q

        result = self.runner.invoke(cli, ["quarantine", "list"])
        assert result.exit_code == 0
        assert "schedule" in result.output
        assert "[REPLAY-SAFE] TRANSIENT" in result.output

    @patch("app.quarantine_cli._get_quarantine")
    def test_list_with_date_filter(self, mock_get_q):
        """List command passes date filter to quarantine."""
        mock_q = Mock()
        mock_q.list_quarantined_data.return_value = []
        mock_get_q.return_value = mock_q

        result = self.runner.invoke(cli, ["quarantine", "list", "--date", "2023-12-25"])
        assert result.exit_code == 0

        # Verify date filter was passed
        mock_q.list_quarantined_data.assert_called_once_with(
            target_date=date(2023, 12, 25), data_type=None
        )

    @patch("app.quarantine_cli._get_quarantine")
    def test_list_with_type_filter(self, mock_get_q):
        """List command passes type filter to quarantine."""
        mock_q = Mock()
        mock_q.list_quarantined_data.return_value = []
        mock_get_q.return_value = mock_q

        result = self.runner.invoke(cli, ["quarantine", "list", "--type", "schedule"])
        assert result.exit_code == 0

        mock_q.list_quarantined_data.assert_called_once_with(
            target_date=None, data_type="schedule"
        )

    @patch("app.quarantine_cli._get_quarantine")
    def test_list_with_classification_filter(self, mock_get_q):
        """List command filters items by classification post-fetch."""
        mock_q = Mock()
        mock_q.list_quarantined_data.return_value = [
            {
                "key": "quarantine/year=2023/month=12/day=25/schedule/f1.json",
                "size": 1024,
                "last_modified": "2023-12-25T10:00:00",
                "metadata": {},
            },
            {
                "key": "quarantine/year=2023/month=12/day=25/box_score/f2.json",
                "size": 2048,
                "last_modified": "2023-12-25T11:00:00",
                "metadata": {},
            },
        ]
        # First item is transient, second is schema_change
        mock_q.s3_manager.s3_client.get_object.side_effect = [
            {
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(
                            {
                                "data": {},
                                "metadata": {
                                    "error_classification": "transient",
                                    "issues_count": 1,
                                },
                            }
                        ).encode("utf-8")
                    )
                )
            },
            {
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(
                            {
                                "data": {},
                                "metadata": {
                                    "error_classification": "schema_change",
                                    "issues_count": 3,
                                },
                            }
                        ).encode("utf-8")
                    )
                )
            },
        ]
        mock_get_q.return_value = mock_q

        result = self.runner.invoke(
            cli, ["quarantine", "list", "--classification", "transient"]
        )
        assert result.exit_code == 0
        assert "[REPLAY-SAFE] TRANSIENT" in result.output
        assert "schema_change" not in result.output.lower().replace(
            "[replay-safe] transient", ""
        ).replace("[investigate] schema_change", "")

    @patch("app.quarantine_cli._get_quarantine")
    def test_list_json_output(self, mock_get_q):
        """List command supports JSON output format."""
        mock_q = Mock()
        mock_q.list_quarantined_data.return_value = [
            {
                "key": "quarantine/year=2023/month=12/day=25/schedule/file1.json",
                "size": 1024,
                "last_modified": "2023-12-25T10:00:00",
                "metadata": {},
            },
        ]
        mock_q.s3_manager.s3_client.get_object.return_value = {
            "Body": Mock(
                read=Mock(
                    return_value=json.dumps(
                        {
                            "data": {},
                            "metadata": {
                                "error_classification": "transient",
                                "issues_count": 2,
                            },
                        }
                    ).encode("utf-8")
                )
            )
        }
        mock_get_q.return_value = mock_q

        result = self.runner.invoke(cli, ["quarantine", "list", "--output", "json"])
        assert result.exit_code == 0

        # Output should be valid JSON
        parsed = json.loads(result.output)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["error_classification"] == "transient"

    @patch("app.quarantine_cli._get_quarantine")
    def test_list_s3_error(self, mock_get_q):
        """List command handles S3 connectivity failures."""
        mock_get_q.side_effect = Exception("S3 connection failed")

        result = self.runner.invoke(cli, ["quarantine", "list"])
        assert result.exit_code == 1
        assert "Error" in result.output or "S3 connection failed" in result.output

    def test_list_help(self):
        """List command has help documentation."""
        result = self.runner.invoke(cli, ["quarantine", "list", "--help"])
        assert result.exit_code == 0
        assert "List quarantined payloads" in result.output
        assert "--date" in result.output
        assert "--type" in result.output
        assert "--classification" in result.output
        assert "--output" in result.output


class TestQuarantineSummaryCommand:
    """Test the quarantine summary CLI command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("app.quarantine_cli._get_quarantine")
    def test_summary_basic(self, mock_get_q):
        """Summary command displays aggregate counts."""
        mock_q = Mock()
        mock_q.get_quarantine_summary.return_value = {
            "total_quarantined": 3,
            "by_data_type": {"schedule": 1, "box_score": 2},
            "summary_date": "2023-12-25T10:00:00",
            "recent_items": [],
        }
        mock_q.list_quarantined_data.return_value = [
            {
                "key": "quarantine/year=2023/month=12/day=25/schedule/f1.json",
                "size": 1024,
                "last_modified": "2023-12-25T10:00:00",
                "metadata": {},
            },
            {
                "key": "quarantine/year=2023/month=12/day=25/box_score/f2.json",
                "size": 2048,
                "last_modified": "2023-12-25T11:00:00",
                "metadata": {},
            },
            {
                "key": "quarantine/year=2023/month=12/day=25/box_score/f3.json",
                "size": 1536,
                "last_modified": "2023-12-25T12:00:00",
                "metadata": {},
            },
        ]
        mock_q.s3_manager.s3_client.get_object.side_effect = [
            {
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(
                            {
                                "data": {},
                                "metadata": {
                                    "error_classification": "transient",
                                    "issues_count": 1,
                                },
                            }
                        ).encode("utf-8")
                    )
                )
            },
            {
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(
                            {
                                "data": {},
                                "metadata": {
                                    "error_classification": "schema_change",
                                    "issues_count": 2,
                                },
                            }
                        ).encode("utf-8")
                    )
                )
            },
            {
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(
                            {
                                "data": {},
                                "metadata": {
                                    "error_classification": "schema_change",
                                    "issues_count": 3,
                                },
                            }
                        ).encode("utf-8")
                    )
                )
            },
        ]
        mock_get_q.return_value = mock_q

        result = self.runner.invoke(cli, ["quarantine", "summary"])
        assert result.exit_code == 0
        assert "Quarantine Summary" in result.output
        assert "Total quarantined: 3" in result.output
        assert "Replay-safe (transient): 1" in result.output
        assert "Requires investigation:  2" in result.output

    @patch("app.quarantine_cli._get_quarantine")
    def test_summary_error(self, mock_get_q):
        """Summary command handles errors gracefully."""
        mock_get_q.side_effect = Exception("S3 connection failed")

        result = self.runner.invoke(cli, ["quarantine", "summary"])
        assert result.exit_code == 1

    @patch("app.quarantine_cli._get_quarantine")
    def test_summary_with_error_in_response(self, mock_get_q):
        """Summary command handles error in summary response."""
        mock_q = Mock()
        mock_q.get_quarantine_summary.return_value = {
            "total_quarantined": 0,
            "by_data_type": {},
            "summary_date": "2023-12-25T10:00:00",
            "recent_items": [],
            "error": "Failed to access S3",
        }
        mock_get_q.return_value = mock_q

        result = self.runner.invoke(cli, ["quarantine", "summary"])
        assert result.exit_code == 1

    def test_summary_help(self):
        """Summary command has help documentation."""
        result = self.runner.invoke(cli, ["quarantine", "summary", "--help"])
        assert result.exit_code == 0
        assert "aggregate counts" in result.output.lower()


class TestQuarantineInspectCommand:
    """Test the quarantine inspect CLI command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("app.quarantine_cli._get_quarantine")
    def test_inspect_success(self, mock_get_q):
        """Inspect command displays full quarantine record."""
        record = {
            "data": {"test": "payload"},
            "validation_result": {
                "valid": False,
                "issues": ["Schema validation failed"],
            },
            "metadata": {
                "data_type": "schedule",
                "target_date": "2023-12-25",
                "quarantine_timestamp": "2023-12-25T10:30:00",
                "error_classification": "schema_change",
                "issues_count": 1,
                "validation_valid": False,
                "context": {},
            },
        }
        mock_q = Mock()
        mock_q.s3_manager.s3_client.get_object.return_value = {
            "Body": Mock(read=Mock(return_value=json.dumps(record).encode("utf-8")))
        }
        mock_get_q.return_value = mock_q

        s3_key = "quarantine/year=2023/month=12/day=25/schedule/file.json"
        result = self.runner.invoke(cli, ["quarantine", "inspect", s3_key])
        assert result.exit_code == 0
        assert "Quarantine Record Details" in result.output
        assert "schedule" in result.output
        assert "[INVESTIGATE] SCHEMA_CHANGE" in result.output
        assert "Schema validation failed" in result.output

    @patch("app.quarantine_cli._get_quarantine")
    def test_inspect_with_full_flag(self, mock_get_q):
        """Inspect command with --full shows complete payload."""
        record = {
            "data": {"field": "x" * 1000},
            "validation_result": {"valid": False, "issues": ["Error"]},
            "metadata": {
                "data_type": "box_score",
                "target_date": "2023-12-25",
                "quarantine_timestamp": "2023-12-25T10:30:00",
                "error_classification": "transient",
                "issues_count": 1,
                "validation_valid": False,
                "context": {},
            },
        }
        mock_q = Mock()
        mock_q.s3_manager.s3_client.get_object.return_value = {
            "Body": Mock(read=Mock(return_value=json.dumps(record).encode("utf-8")))
        }
        mock_get_q.return_value = mock_q

        s3_key = "quarantine/year=2023/month=12/day=25/box_score/file.json"
        result = self.runner.invoke(cli, ["quarantine", "inspect", "--full", s3_key])
        assert result.exit_code == 0
        assert "truncated" not in result.output

    @patch("app.quarantine_cli._get_quarantine")
    def test_inspect_not_found(self, mock_get_q):
        """Inspect command handles missing records."""
        mock_q = Mock()
        mock_q.s3_manager.s3_client.get_object.side_effect = Exception("NoSuchKey")
        mock_get_q.return_value = mock_q

        result = self.runner.invoke(
            cli, ["quarantine", "inspect", "nonexistent/key.json"]
        )
        assert result.exit_code == 1

    @patch("app.quarantine_cli._get_quarantine")
    def test_inspect_s3_error(self, mock_get_q):
        """Inspect command handles S3 connectivity failures."""
        mock_get_q.side_effect = Exception("S3 connection failed")

        result = self.runner.invoke(cli, ["quarantine", "inspect", "some/key.json"])
        assert result.exit_code == 1

    def test_inspect_help(self):
        """Inspect command has help documentation."""
        result = self.runner.invoke(cli, ["quarantine", "inspect", "--help"])
        assert result.exit_code == 0
        assert "S3 key" in result.output or "S3_KEY" in result.output

    def test_inspect_missing_argument(self):
        """Inspect command requires S3 key argument."""
        result = self.runner.invoke(cli, ["quarantine", "inspect"])
        assert result.exit_code != 0


class TestQuarantineGroupHelp:
    """Test the quarantine command group help."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_quarantine_help(self):
        """Quarantine group has help documentation."""
        result = self.runner.invoke(cli, ["quarantine", "--help"])
        assert result.exit_code == 0
        assert "quarantine" in result.output.lower()
        assert "list" in result.output
        assert "summary" in result.output
        assert "inspect" in result.output

    def test_quarantine_in_cli_help(self):
        """Quarantine command appears in top-level CLI help."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "quarantine" in result.output
