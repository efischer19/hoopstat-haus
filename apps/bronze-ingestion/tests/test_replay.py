"""Tests for the quarantine replay module."""

import json
from datetime import date
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from app.main import cli
from app.quarantine_cli import (
    _format_batch_summary,
    _format_replay_result,
)
from app.replay import (
    _DATA_TYPE_TO_ENTITY,
    _TRANSFORM_NAMES,
    BatchReplayResult,
    ReplayOrchestrator,
    ReplayResult,
    get_transform_by_name,
)
from app.transforms import IdentityTransform, RoundingToleranceTransform

# -- Fixtures -----------------------------------------------------------------


def _make_quarantine_record(
    data=None,
    classification="transient",
    data_type="box_score",
    target_date="2024-01-15",
    game_id=None,
    issues=None,
    retry_count=0,
    status=None,
):
    """Create a realistic quarantine record for replay testing."""
    if data is None:
        data = {"boxScoreTraditional": {"gameId": "0022400001"}}
    context = {}
    if game_id:
        context["game_id"] = game_id
    record = {
        "data": data,
        "validation_result": {
            "valid": False,
            "issues": issues or ["Connection timeout occurred"],
        },
        "metadata": {
            "data_type": data_type,
            "target_date": target_date,
            "quarantine_timestamp": "2024-01-15T04:30:25",
            "error_classification": classification,
            "issues_count": len(issues) if issues else 1,
            "validation_valid": False,
            "context": context,
            "retry_count": retry_count,
        },
    }
    if status:
        record["metadata"]["status"] = status
    return record


def _mock_s3_manager(bucket_name="test-bronze-bucket"):
    """Create a mock S3 manager."""
    manager = Mock()
    manager.bucket_name = bucket_name
    manager.s3_client = Mock()
    return manager


def _mock_quarantine(s3_manager=None):
    """Create a mock DataQuarantine instance."""
    q = Mock()
    q.s3_manager = s3_manager or _mock_s3_manager()
    return q


def _setup_s3_get_object(s3_manager, record):
    """Set up mock S3 get_object to return a quarantine record."""
    s3_manager.s3_client.get_object.return_value = {
        "Body": Mock(read=Mock(return_value=json.dumps(record).encode("utf-8")))
    }


def _get_stored_record(s3_manager_mock) -> dict:
    """Extract the last stored quarantine record from mock put_object calls."""
    put_calls = s3_manager_mock.s3_client.put_object.call_args_list
    assert len(put_calls) >= 1, "No put_object calls recorded"
    return json.loads(put_calls[-1].kwargs["Body"].decode("utf-8"))


# -- get_transform_by_name Tests ---------------------------------------------


class TestGetTransformByName:
    """Test the transform name resolution helper."""

    def test_identity_transform(self):
        """'identity' resolves to IdentityTransform."""
        t = get_transform_by_name("identity")
        assert isinstance(t, IdentityTransform)

    def test_rounding_tolerance_transform(self):
        """'rounding_tolerance' resolves to RoundingToleranceTransform."""
        t = get_transform_by_name("rounding_tolerance")
        assert isinstance(t, RoundingToleranceTransform)

    def test_unknown_name_raises(self):
        """Unknown names raise ValueError with valid options."""
        with pytest.raises(ValueError, match="Unknown transform name"):
            get_transform_by_name("nonexistent")

    def test_all_registered_names(self):
        """All registered names resolve without error."""
        for name in _TRANSFORM_NAMES:
            t = get_transform_by_name(name)
            assert t is not None


# -- ReplayResult / BatchReplayResult -----------------------------------------


class TestReplayResult:
    """Test replay result dataclasses."""

    def test_success_result(self):
        """Successful result has correct fields."""
        r = ReplayResult(s3_key="key.json", success=True, transform_applied="identity")
        assert r.success is True
        assert r.error is None
        assert r.dry_run is False

    def test_failure_result(self):
        """Failed result includes error message."""
        r = ReplayResult(s3_key="key.json", success=False, error="Transform failed")
        assert r.success is False
        assert r.error == "Transform failed"

    def test_dry_run_result(self):
        """Dry-run result is flagged."""
        r = ReplayResult(s3_key="key.json", success=True, dry_run=True)
        assert r.dry_run is True

    def test_batch_result_defaults(self):
        """Batch result has sensible defaults."""
        br = BatchReplayResult()
        assert br.total == 0
        assert br.succeeded == 0
        assert br.failed == 0
        assert br.results == []


# -- ReplayOrchestrator._fetch_record ----------------------------------------


class TestFetchRecord:
    """Test quarantine record fetching."""

    def test_fetch_success(self):
        """Successfully fetched record is returned as dict."""
        s3_mgr = _mock_s3_manager()
        record = _make_quarantine_record()
        _setup_s3_get_object(s3_mgr, record)

        orchestrator = ReplayOrchestrator(s3_mgr, _mock_quarantine(s3_mgr))
        result = orchestrator._fetch_record("quarantine/key.json")
        assert result is not None
        assert result["metadata"]["data_type"] == "box_score"

    def test_fetch_failure_returns_none(self):
        """Failed fetch returns None."""
        s3_mgr = _mock_s3_manager()
        s3_mgr.s3_client.get_object.side_effect = Exception("NoSuchKey")

        orchestrator = ReplayOrchestrator(s3_mgr, _mock_quarantine(s3_mgr))
        result = orchestrator._fetch_record("nonexistent/key.json")
        assert result is None


# -- ReplayOrchestrator._extract_game_id -------------------------------------


class TestExtractGameId:
    """Test game_id extraction from data and metadata."""

    def setup_method(self):
        """Set up orchestrator."""
        self.s3_mgr = _mock_s3_manager()
        self.orchestrator = ReplayOrchestrator(
            self.s3_mgr, _mock_quarantine(self.s3_mgr)
        )

    def test_from_context_game_id(self):
        """game_id is extracted from context directly."""
        metadata = {"context": {"game_id": "0022400001"}}
        result = self.orchestrator._extract_game_id({}, metadata)
        assert result == "0022400001"

    def test_from_request_params(self):
        """game_id is extracted from context.request_params."""
        metadata = {"context": {"request_params": {"game_id": "0022400002"}}}
        result = self.orchestrator._extract_game_id({}, metadata)
        assert result == "0022400002"

    def test_from_box_score_data(self):
        """game_id is extracted from boxScoreTraditional data."""
        data = {"boxScoreTraditional": {"gameId": "0022400003"}}
        metadata = {"context": {}}
        result = self.orchestrator._extract_game_id(data, metadata)
        assert result == "0022400003"

    def test_returns_none_when_absent(self):
        """None is returned when game_id cannot be found."""
        result = self.orchestrator._extract_game_id({}, {"context": {}})
        assert result is None

    def test_context_takes_priority(self):
        """Context game_id takes priority over data game_id."""
        data = {"boxScoreTraditional": {"gameId": "from_data"}}
        metadata = {"context": {"game_id": "from_context"}}
        result = self.orchestrator._extract_game_id(data, metadata)
        assert result == "from_context"


# -- ReplayOrchestrator._write_to_bronze -------------------------------------


class TestWriteToBronze:
    """Test writing transformed data to Bronze location."""

    def setup_method(self):
        """Set up orchestrator with mock S3."""
        self.s3_mgr = _mock_s3_manager()
        self.s3_mgr.store_json = Mock(return_value="raw/box/2024-01-15/0022400001.json")
        self.orchestrator = ReplayOrchestrator(
            self.s3_mgr, _mock_quarantine(self.s3_mgr)
        )

    def test_write_box_score(self):
        """Box score data is written to correct Bronze path."""
        data = {"boxScoreTraditional": {"gameId": "0022400001"}}
        metadata = {
            "data_type": "box_score",
            "target_date": "2024-01-15",
            "context": {"game_id": "0022400001"},
        }
        self.orchestrator._write_to_bronze(data, metadata)
        self.s3_mgr.store_json.assert_called_once_with(
            data,
            entity="box",
            target_date=date(2024, 1, 15),
            game_id="0022400001",
        )

    def test_write_schedule(self):
        """Schedule data is written with correct entity type."""
        self.s3_mgr.store_json.return_value = "raw/schedule/2024-01-15/data.json"
        data = [{"GAME_ID": "001"}]
        metadata = {
            "data_type": "schedule",
            "target_date": "2024-01-15",
            "context": {},
        }
        self.orchestrator._write_to_bronze(data, metadata)
        self.s3_mgr.store_json.assert_called_once_with(
            data,
            entity="schedule",
            target_date=date(2024, 1, 15),
            game_id=None,
        )

    def test_invalid_date_raises(self):
        """Invalid target_date in metadata raises ValueError."""
        with pytest.raises(ValueError, match="Invalid target_date"):
            self.orchestrator._write_to_bronze(
                {},
                {"data_type": "box_score", "target_date": "not-a-date", "context": {}},
            )


# -- ReplayOrchestrator.replay_single ----------------------------------------


class TestReplaySingle:
    """Test single-file replay."""

    def setup_method(self):
        """Set up orchestrator with mocks."""
        self.s3_mgr = _mock_s3_manager()
        self.s3_mgr.store_json = Mock(return_value="raw/box/2024-01-15/0022400001.json")
        self.quarantine_mock = _mock_quarantine(self.s3_mgr)
        self.orchestrator = ReplayOrchestrator(self.s3_mgr, self.quarantine_mock)

    def _setup_record(self, record=None, **kwargs):
        """Set up a quarantine record in mock S3."""
        if record is None:
            record = _make_quarantine_record(**kwargs)
        _setup_s3_get_object(self.s3_mgr, record)
        return record

    def test_successful_replay(self):
        """Successful replay returns success with transform info."""
        self._setup_record(classification="transient", game_id="0022400001")

        result = self.orchestrator.replay_single("quarantine/key.json")

        assert result.success is True
        assert result.transform_applied == "identity"
        assert result.error is None
        # Verify Bronze write was called
        self.s3_mgr.store_json.assert_called_once()

    def test_record_not_found(self):
        """Missing record returns failure."""
        self.s3_mgr.s3_client.get_object.side_effect = Exception("NoSuchKey")

        result = self.orchestrator.replay_single("nonexistent/key.json")

        assert result.success is False
        assert "Could not fetch" in result.error

    def test_transform_error_marks_failed(self):
        """TransformError updates record to failed status."""
        record = _make_quarantine_record(
            classification="rounding_mismatch",
            data={"no_box_score": True},
            issues=["Rounding mismatch in sum"],
        )
        self._setup_record(record=record)

        result = self.orchestrator.replay_single("quarantine/key.json")

        assert result.success is False
        assert "Transform failed" in result.error
        # Verify quarantine record was updated to failed
        stored_record = _get_stored_record(self.s3_mgr)
        assert stored_record["metadata"]["status"] == "failed"
        assert stored_record["metadata"]["retry_count"] == 1

    def test_dry_run_skips_write(self):
        """Dry-run mode does not write to Bronze or invoke Silver."""
        self._setup_record(classification="transient", game_id="0022400001")

        result = self.orchestrator.replay_single("quarantine/key.json", dry_run=True)

        assert result.success is True
        assert result.dry_run is True
        # Verify no S3 writes happened
        self.s3_mgr.store_json.assert_not_called()

    def test_transform_override(self):
        """Custom transform override is used instead of default."""
        self._setup_record(
            classification="rounding_mismatch",
            game_id="0022400001",
        )

        identity = IdentityTransform()
        result = self.orchestrator.replay_single(
            "quarantine/key.json", transform_override=identity
        )

        assert result.success is True
        assert result.transform_applied == "identity"

    def test_bronze_write_failure(self):
        """Bronze write failure updates record to failed."""
        self._setup_record(classification="transient", game_id="0022400001")
        self.s3_mgr.store_json.side_effect = Exception("S3 write error")

        result = self.orchestrator.replay_single("quarantine/key.json")

        assert result.success is False
        assert "Failed to write to Bronze" in result.error

    def test_silver_processing_failure(self):
        """Silver processing failure updates record to failed."""
        self._setup_record(classification="transient", game_id="0022400001")

        # Create orchestrator with a silver processing dir
        orchestrator = ReplayOrchestrator(
            self.s3_mgr,
            self.quarantine_mock,
            silver_processing_dir="/nonexistent/silver-processing",
        )

        with patch("app.replay.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stderr="Processing error")
            # Need the silver dir to exist for subprocess to be called
            with patch("app.replay.Path.exists", return_value=True):
                result = orchestrator.replay_single("quarantine/key.json")

        assert result.success is False
        assert "Silver processing failed" in result.error

    def test_resolved_status_metadata(self):
        """Resolved record includes replay_timestamp and transform_applied."""
        self._setup_record(classification="transient", game_id="0022400001")

        self.orchestrator.replay_single("quarantine/key.json")

        stored_record = _get_stored_record(self.s3_mgr)
        assert stored_record["metadata"]["status"] == "resolved"
        assert "replay_timestamp" in stored_record["metadata"]
        assert stored_record["metadata"]["transform_applied"] == "identity"

    def test_failed_status_increments_retry_count(self):
        """Failed replay increments retry_count on record."""
        record = _make_quarantine_record(
            classification="rounding_mismatch",
            data={"no_box_score": True},
            issues=["Rounding mismatch in sum"],
            retry_count=2,
        )
        self._setup_record(record=record)

        self.orchestrator.replay_single("quarantine/key.json")

        stored_record = _get_stored_record(self.s3_mgr)
        assert stored_record["metadata"]["retry_count"] == 3

    def test_unknown_classification_uses_identity(self):
        """Unknown classification falls back to IdentityTransform."""
        self._setup_record(
            classification="something_weird",
            game_id="0022400001",
        )

        result = self.orchestrator.replay_single("quarantine/key.json")

        assert result.success is True
        assert result.transform_applied == "identity"


# -- ReplayOrchestrator.replay_batch -----------------------------------------


class TestReplayBatch:
    """Test batch replay operations."""

    def setup_method(self):
        """Set up orchestrator with mocks."""
        self.s3_mgr = _mock_s3_manager()
        self.s3_mgr.store_json = Mock(return_value="raw/box/2024-01-15/0022400001.json")
        self.quarantine_mock = _mock_quarantine(self.s3_mgr)
        self.orchestrator = ReplayOrchestrator(self.s3_mgr, self.quarantine_mock)

    def test_batch_all_succeed(self):
        """Batch replay with all items succeeding."""
        record1 = _make_quarantine_record(game_id="001")
        record2 = _make_quarantine_record(game_id="002")

        self.s3_mgr.s3_client.get_object.side_effect = [
            {"Body": Mock(read=Mock(return_value=json.dumps(record1).encode("utf-8")))},
            {"Body": Mock(read=Mock(return_value=json.dumps(record2).encode("utf-8")))},
        ]

        items = [{"key": "key1.json"}, {"key": "key2.json"}]
        result = self.orchestrator.replay_batch(items)

        assert result.total == 2
        assert result.succeeded == 2
        assert result.failed == 0

    def test_batch_partial_failure(self):
        """Batch replay reports partial failures."""
        record_good = _make_quarantine_record(game_id="001")
        record_bad = _make_quarantine_record(
            classification="rounding_mismatch",
            data={"no_box_score": True},
            issues=["Rounding mismatch in sum"],
        )

        self.s3_mgr.s3_client.get_object.side_effect = [
            {
                "Body": Mock(
                    read=Mock(return_value=json.dumps(record_good).encode("utf-8"))
                )
            },
            {
                "Body": Mock(
                    read=Mock(return_value=json.dumps(record_bad).encode("utf-8"))
                )
            },
        ]

        items = [{"key": "good.json"}, {"key": "bad.json"}]
        result = self.orchestrator.replay_batch(items)

        assert result.total == 2
        assert result.succeeded == 1
        assert result.failed == 1

    def test_batch_empty_list(self):
        """Batch replay with empty list returns zeros."""
        result = self.orchestrator.replay_batch([])
        assert result.total == 0
        assert result.succeeded == 0
        assert result.failed == 0

    def test_batch_dry_run(self):
        """Batch dry-run validates all items without writing."""
        record = _make_quarantine_record(game_id="001")
        self.s3_mgr.s3_client.get_object.return_value = {
            "Body": Mock(read=Mock(return_value=json.dumps(record).encode("utf-8")))
        }

        items = [{"key": "key1.json"}, {"key": "key2.json"}]
        result = self.orchestrator.replay_batch(items, dry_run=True)

        assert result.total == 2
        assert result.succeeded == 2
        assert result.failed == 0
        for r in result.results:
            assert r.dry_run is True
        # No S3 writes
        self.s3_mgr.store_json.assert_not_called()

    def test_batch_with_transform_override(self):
        """Batch replay applies transform override to all items."""
        record = _make_quarantine_record(
            classification="rounding_mismatch", game_id="001"
        )
        self.s3_mgr.s3_client.get_object.return_value = {
            "Body": Mock(read=Mock(return_value=json.dumps(record).encode("utf-8")))
        }

        identity = IdentityTransform()
        items = [{"key": "key1.json"}]
        result = self.orchestrator.replay_batch(items, transform_override=identity)

        assert result.succeeded == 1
        assert result.results[0].transform_applied == "identity"


# -- Silver Processing Invocation Tests ---------------------------------------


class TestSilverProcessing:
    """Test Silver processing invocation."""

    def setup_method(self):
        """Set up orchestrator."""
        self.s3_mgr = _mock_s3_manager()
        self.orchestrator = ReplayOrchestrator(
            self.s3_mgr, _mock_quarantine(self.s3_mgr)
        )

    def test_no_silver_dir_skips(self):
        """When no silver_processing_dir is configured, invocation succeeds."""
        result = self.orchestrator._invoke_silver_processing("2024-01-15")
        assert result is True

    def test_nonexistent_dir_skips(self):
        """When silver dir doesn't exist on disk, invocation succeeds."""
        orchestrator = ReplayOrchestrator(
            self.s3_mgr,
            _mock_quarantine(self.s3_mgr),
            silver_processing_dir="/nonexistent/path",
        )
        result = orchestrator._invoke_silver_processing("2024-01-15")
        assert result is True

    @patch("app.replay.Path.exists", return_value=True)
    @patch("app.replay.subprocess.run")
    def test_successful_invocation(self, mock_run, _mock_exists):
        """Subprocess returning 0 means success."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        orchestrator = ReplayOrchestrator(
            self.s3_mgr,
            _mock_quarantine(self.s3_mgr),
            silver_processing_dir="/apps/silver-processing",
        )
        result = orchestrator._invoke_silver_processing("2024-01-15")
        assert result is True

    @patch("app.replay.Path.exists", return_value=True)
    @patch("app.replay.subprocess.run")
    def test_failed_invocation(self, mock_run, _mock_exists):
        """Subprocess returning non-zero means failure."""
        mock_run.return_value = Mock(returncode=1, stderr="Error")
        orchestrator = ReplayOrchestrator(
            self.s3_mgr,
            _mock_quarantine(self.s3_mgr),
            silver_processing_dir="/apps/silver-processing",
        )
        result = orchestrator._invoke_silver_processing("2024-01-15")
        assert result is False

    @patch("app.replay.Path.exists", return_value=True)
    @patch("app.replay.subprocess.run")
    def test_timeout(self, mock_run, _mock_exists):
        """Subprocess timeout is handled gracefully."""
        import subprocess as sp

        mock_run.side_effect = sp.TimeoutExpired("cmd", 300)
        orchestrator = ReplayOrchestrator(
            self.s3_mgr,
            _mock_quarantine(self.s3_mgr),
            silver_processing_dir="/apps/silver-processing",
        )
        result = orchestrator._invoke_silver_processing("2024-01-15")
        assert result is False


# -- CLI Formatting Tests -----------------------------------------------------


class TestReplayFormatting:
    """Test replay result formatting helpers."""

    def test_format_success_result(self):
        """Successful result formatted with OK status."""
        r = ReplayResult(
            s3_key="quarantine/key.json",
            success=True,
            transform_applied="identity",
        )
        output = _format_replay_result(r)
        assert "[OK]" in output
        assert "quarantine/key.json" in output
        assert "identity" in output

    def test_format_failure_result(self):
        """Failed result formatted with error details."""
        r = ReplayResult(
            s3_key="quarantine/key.json",
            success=False,
            error="Transform failed",
            transform_applied="rounding_tolerance",
        )
        output = _format_replay_result(r)
        assert "[FAILED]" in output
        assert "Transform failed" in output

    def test_format_dry_run_result(self):
        """Dry-run result formatted with DRY-RUN OK status."""
        r = ReplayResult(
            s3_key="quarantine/key.json",
            success=True,
            dry_run=True,
            transform_applied="identity",
        )
        output = _format_replay_result(r)
        assert "[DRY-RUN OK]" in output

    def test_format_batch_summary(self):
        """Batch summary includes totals and individual results."""
        br = BatchReplayResult(
            total=3,
            succeeded=2,
            failed=1,
            results=[
                ReplayResult(
                    s3_key="k1.json", success=True, transform_applied="identity"
                ),
                ReplayResult(
                    s3_key="k2.json", success=True, transform_applied="identity"
                ),
                ReplayResult(s3_key="k3.json", success=False, error="Failed"),
            ],
        )
        output = _format_batch_summary(br)
        assert "Replay Summary" in output
        assert "Total:     3" in output
        assert "Succeeded: 2" in output
        assert "Failed:    1" in output
        assert "k1.json" in output
        assert "k3.json" in output

    def test_format_batch_summary_empty(self):
        """Empty batch summary shows zeros."""
        br = BatchReplayResult()
        output = _format_batch_summary(br)
        assert "Total:     0" in output


# -- CLI Command Tests --------------------------------------------------------


class TestQuarantineReplayCommand:
    """Test the quarantine replay CLI command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_replay_help(self):
        """Replay command has help documentation."""
        result = self.runner.invoke(cli, ["quarantine", "replay", "--help"])
        assert result.exit_code == 0
        assert "Replay quarantined data" in result.output
        assert "--dry-run" in result.output
        assert "--transform" in result.output
        assert "--classification" in result.output
        assert "--date" in result.output

    def test_replay_in_quarantine_help(self):
        """Replay command appears in quarantine group help."""
        result = self.runner.invoke(cli, ["quarantine", "--help"])
        assert result.exit_code == 0
        assert "replay" in result.output

    def test_replay_no_arguments(self):
        """Replay command requires at least one selection criterion."""
        result = self.runner.invoke(cli, ["quarantine", "replay"])
        assert result.exit_code != 0
        assert "Provide an S3 key" in result.output

    @patch("app.quarantine_cli._get_replay_orchestrator")
    def test_replay_single_file(self, mock_get_orch):
        """Single-file replay with S3 key argument."""
        mock_orch = Mock()
        mock_orch.replay_single.return_value = ReplayResult(
            s3_key="quarantine/key.json",
            success=True,
            transform_applied="identity",
        )
        mock_get_orch.return_value = mock_orch

        result = self.runner.invoke(
            cli, ["quarantine", "replay", "quarantine/key.json"]
        )
        assert result.exit_code == 0
        assert "[OK]" in result.output
        mock_orch.replay_single.assert_called_once()

    @patch("app.quarantine_cli._get_replay_orchestrator")
    def test_replay_single_file_failure(self, mock_get_orch):
        """Single-file replay failure exits with error code."""
        mock_orch = Mock()
        mock_orch.replay_single.return_value = ReplayResult(
            s3_key="quarantine/key.json",
            success=False,
            error="Transform failed",
        )
        mock_get_orch.return_value = mock_orch

        result = self.runner.invoke(
            cli, ["quarantine", "replay", "quarantine/key.json"]
        )
        assert result.exit_code == 1

    @patch("app.quarantine_cli._get_replay_orchestrator")
    def test_replay_dry_run(self, mock_get_orch):
        """Dry-run flag is passed through to orchestrator."""
        mock_orch = Mock()
        mock_orch.replay_single.return_value = ReplayResult(
            s3_key="quarantine/key.json",
            success=True,
            dry_run=True,
            transform_applied="identity",
        )
        mock_get_orch.return_value = mock_orch

        result = self.runner.invoke(
            cli, ["quarantine", "replay", "--dry-run", "quarantine/key.json"]
        )
        assert result.exit_code == 0
        assert "[DRY-RUN OK]" in result.output
        _, kwargs = mock_orch.replay_single.call_args
        assert kwargs["dry_run"] is True

    @patch("app.quarantine_cli._get_replay_orchestrator")
    def test_replay_with_transform_override(self, mock_get_orch):
        """Transform override is resolved and passed through."""
        mock_orch = Mock()
        mock_orch.replay_single.return_value = ReplayResult(
            s3_key="quarantine/key.json",
            success=True,
            transform_applied="identity",
        )
        mock_get_orch.return_value = mock_orch

        result = self.runner.invoke(
            cli,
            ["quarantine", "replay", "--transform", "identity", "quarantine/key.json"],
        )
        assert result.exit_code == 0
        _, kwargs = mock_orch.replay_single.call_args
        assert isinstance(kwargs["transform_override"], IdentityTransform)

    def test_replay_invalid_transform_name(self):
        """Invalid transform name shows error."""
        result = self.runner.invoke(
            cli,
            ["quarantine", "replay", "--transform", "bogus", "quarantine/key.json"],
        )
        assert result.exit_code != 0
        assert "Unknown transform name" in result.output

    @patch("app.quarantine_cli._enrich_items")
    @patch("app.quarantine_cli._get_replay_orchestrator")
    def test_replay_by_classification(self, mock_get_orch, mock_enrich):
        """Batch replay by classification filters and processes items."""
        mock_q = Mock()
        mock_q.list_quarantined_data.return_value = [
            {"key": "k1.json"},
            {"key": "k2.json"},
        ]
        mock_enrich.return_value = [
            {"key": "k1.json", "error_classification": "transient"},
            {"key": "k2.json", "error_classification": "schema_change"},
        ]
        mock_orch = Mock()
        mock_orch.quarantine = mock_q
        mock_orch.replay_batch.return_value = BatchReplayResult(
            total=1,
            succeeded=1,
            failed=0,
            results=[
                ReplayResult(
                    s3_key="k1.json", success=True, transform_applied="identity"
                )
            ],
        )
        mock_get_orch.return_value = mock_orch

        result = self.runner.invoke(
            cli, ["quarantine", "replay", "--classification", "transient"]
        )
        assert result.exit_code == 0
        assert "Replay Summary" in result.output
        # Only transient items should be passed to replay_batch
        call_args = mock_orch.replay_batch.call_args
        items = call_args[0][0]
        assert len(items) == 1
        assert items[0]["key"] == "k1.json"

    @patch("app.quarantine_cli._get_replay_orchestrator")
    def test_replay_by_date(self, mock_get_orch):
        """Batch replay by date passes date filter."""
        mock_q = Mock()
        mock_q.list_quarantined_data.return_value = [{"key": "k1.json"}]
        mock_orch = Mock()
        mock_orch.quarantine = mock_q
        mock_orch.replay_batch.return_value = BatchReplayResult(
            total=1,
            succeeded=1,
            failed=0,
            results=[
                ReplayResult(
                    s3_key="k1.json", success=True, transform_applied="identity"
                )
            ],
        )
        mock_get_orch.return_value = mock_orch

        result = self.runner.invoke(
            cli, ["quarantine", "replay", "--date", "2024-01-15"]
        )
        assert result.exit_code == 0
        mock_q.list_quarantined_data.assert_called_once_with(
            target_date=date(2024, 1, 15)
        )

    @patch("app.quarantine_cli._get_replay_orchestrator")
    def test_replay_no_matching_items(self, mock_get_orch):
        """Batch replay with no matching items shows message."""
        mock_q = Mock()
        mock_q.list_quarantined_data.return_value = []
        mock_orch = Mock()
        mock_orch.quarantine = mock_q
        mock_get_orch.return_value = mock_orch

        result = self.runner.invoke(
            cli, ["quarantine", "replay", "--date", "2024-01-15"]
        )
        assert result.exit_code == 0
        assert "No quarantined items found" in result.output

    @patch("app.quarantine_cli._get_replay_orchestrator")
    def test_replay_batch_with_failures_exits_nonzero(self, mock_get_orch):
        """Batch replay with any failures exits with error code."""
        mock_q = Mock()
        mock_q.list_quarantined_data.return_value = [{"key": "k1.json"}]
        mock_orch = Mock()
        mock_orch.quarantine = mock_q
        mock_orch.replay_batch.return_value = BatchReplayResult(
            total=1,
            succeeded=0,
            failed=1,
            results=[ReplayResult(s3_key="k1.json", success=False, error="Failed")],
        )
        mock_get_orch.return_value = mock_orch

        result = self.runner.invoke(
            cli, ["quarantine", "replay", "--date", "2024-01-15"]
        )
        assert result.exit_code == 1


# -- Data Type to Entity Mapping Tests ----------------------------------------


class TestDataTypeMapping:
    """Test data type to entity name mapping."""

    def test_box_score_maps_to_box(self):
        """box_score maps to 'box' entity."""
        assert _DATA_TYPE_TO_ENTITY["box_score"] == "box"

    def test_schedule_maps_to_schedule(self):
        """schedule maps to 'schedule' entity."""
        assert _DATA_TYPE_TO_ENTITY["schedule"] == "schedule"

    def test_api_response_maps_to_box(self):
        """api_response maps to 'box' entity (default for API responses)."""
        assert _DATA_TYPE_TO_ENTITY["api_response"] == "box"


# -- State Machine / Idempotency Tests ----------------------------------------


class TestStatusTransitions:
    """Test quarantine record status transitions and idempotency guards."""

    def setup_method(self):
        """Set up orchestrator with mocks."""
        self.s3_mgr = _mock_s3_manager()
        self.s3_mgr.store_json = Mock(return_value="raw/box/2024-01-15/0022400001.json")
        self.quarantine_mock = _mock_quarantine(self.s3_mgr)
        self.orchestrator = ReplayOrchestrator(self.s3_mgr, self.quarantine_mock)

    def _setup_record(self, record=None, **kwargs):
        """Set up a quarantine record in mock S3."""
        if record is None:
            record = _make_quarantine_record(**kwargs)
        _setup_s3_get_object(self.s3_mgr, record)
        return record

    def test_skip_on_resolved_without_force(self):
        """Resolved record without --force is skipped with warning."""
        self._setup_record(
            status="resolved", classification="transient", game_id="0022400001"
        )

        result = self.orchestrator.replay_single("quarantine/key.json")

        assert result.skipped is True
        assert result.success is True
        assert "already resolved" in result.error
        # No Bronze write should happen
        self.s3_mgr.store_json.assert_not_called()

    def test_skip_on_replaying_status(self):
        """Record in 'replaying' status is skipped (concurrent replay guard)."""
        self._setup_record(
            status="replaying", classification="transient", game_id="0022400001"
        )

        result = self.orchestrator.replay_single("quarantine/key.json")

        assert result.skipped is True
        assert result.success is True
        assert "already in 'replaying' status" in result.error
        self.s3_mgr.store_json.assert_not_called()

    def test_force_replay_resolved_record(self):
        """Resolved record with --force proceeds normally."""
        self._setup_record(
            status="resolved", classification="transient", game_id="0022400001"
        )

        result = self.orchestrator.replay_single("quarantine/key.json", force=True)

        assert result.success is True
        assert result.skipped is False
        assert result.transform_applied == "identity"
        self.s3_mgr.store_json.assert_called_once()

    def test_quarantined_proceeds(self):
        """Record with 'quarantined' status proceeds normally."""
        self._setup_record(
            status="quarantined", classification="transient", game_id="0022400001"
        )

        result = self.orchestrator.replay_single("quarantine/key.json")

        assert result.success is True
        assert result.skipped is False

    def test_failed_proceeds(self):
        """Record with 'failed' status can be retried."""
        self._setup_record(
            status="failed", classification="transient", game_id="0022400001"
        )

        result = self.orchestrator.replay_single("quarantine/key.json")

        assert result.success is True
        assert result.skipped is False

    def test_missing_status_treated_as_quarantined(self):
        """Backward compat: missing status is treated as 'quarantined'."""
        record = _make_quarantine_record(
            classification="transient", game_id="0022400001"
        )
        # Ensure no status field exists (backward compat)
        record["metadata"].pop("status", None)
        self._setup_record(record=record)

        result = self.orchestrator.replay_single("quarantine/key.json")

        assert result.success is True
        assert result.skipped is False

    def test_replaying_status_set_before_processing(self):
        """Status is set to 'replaying' before transform/write happens."""
        self._setup_record(
            status="quarantined", classification="transient", game_id="0022400001"
        )

        self.orchestrator.replay_single("quarantine/key.json")

        # Check that put_object was called multiple times:
        # first for 'replaying', then for 'resolved'
        put_calls = self.s3_mgr.s3_client.put_object.call_args_list
        assert len(put_calls) >= 2

        # First call should set status to 'replaying'
        first_record = json.loads(put_calls[0].kwargs["Body"].decode("utf-8"))
        assert first_record["metadata"]["status"] == "replaying"

        # Last call should set status to 'resolved'
        last_record = json.loads(put_calls[-1].kwargs["Body"].decode("utf-8"))
        assert last_record["metadata"]["status"] == "resolved"

    def test_failed_replay_sets_failed_status(self):
        """Failed replay transitions to 'failed' status."""
        record = _make_quarantine_record(
            classification="rounding_mismatch",
            data={"no_box_score": True},
            issues=["Rounding mismatch in sum"],
            status="quarantined",
        )
        self._setup_record(record=record)

        self.orchestrator.replay_single("quarantine/key.json")

        stored_record = _get_stored_record(self.s3_mgr)
        assert stored_record["metadata"]["status"] == "failed"


# -- Attempts Audit Trail Tests -----------------------------------------------


class TestAttemptsAuditTrail:
    """Test the attempts list audit trail on quarantine records."""

    def setup_method(self):
        """Set up orchestrator with mocks."""
        self.s3_mgr = _mock_s3_manager()
        self.s3_mgr.store_json = Mock(return_value="raw/box/2024-01-15/0022400001.json")
        self.quarantine_mock = _mock_quarantine(self.s3_mgr)
        self.orchestrator = ReplayOrchestrator(self.s3_mgr, self.quarantine_mock)

    def _setup_record(self, record=None, **kwargs):
        """Set up a quarantine record in mock S3."""
        if record is None:
            record = _make_quarantine_record(**kwargs)
        _setup_s3_get_object(self.s3_mgr, record)
        return record

    def test_resolved_attempt_logged(self):
        """Successful replay appends a 'resolved' attempt entry."""
        self._setup_record(
            status="quarantined", classification="transient", game_id="0022400001"
        )

        self.orchestrator.replay_single("quarantine/key.json")

        stored_record = _get_stored_record(self.s3_mgr)
        attempts = stored_record.get("attempts", [])
        assert len(attempts) == 1
        assert attempts[0]["result"] == "resolved"
        assert attempts[0]["transform"] == "identity"
        assert "timestamp" in attempts[0]
        assert "error" not in attempts[0]

    def test_failed_attempt_logged(self):
        """Failed replay appends a 'failed' attempt entry with error."""
        record = _make_quarantine_record(
            classification="rounding_mismatch",
            data={"no_box_score": True},
            issues=["Rounding mismatch in sum"],
            status="quarantined",
        )
        self._setup_record(record=record)

        self.orchestrator.replay_single("quarantine/key.json")

        stored_record = _get_stored_record(self.s3_mgr)
        attempts = stored_record.get("attempts", [])
        assert len(attempts) == 1
        assert attempts[0]["result"] == "failed"
        assert "error" in attempts[0]
        assert "timestamp" in attempts[0]

    def test_missing_attempts_initialized(self):
        """Backward compat: missing 'attempts' is initialized as empty list."""
        record = _make_quarantine_record(
            classification="transient", game_id="0022400001"
        )
        # Remove attempts field to simulate old record
        record.pop("attempts", None)
        self._setup_record(record=record)

        self.orchestrator.replay_single("quarantine/key.json")

        stored_record = _get_stored_record(self.s3_mgr)
        assert "attempts" in stored_record
        assert len(stored_record["attempts"]) == 1

    def test_batch_skipped_tracking(self):
        """Batch replay correctly tracks skipped items."""
        record1 = _make_quarantine_record(game_id="001", status="resolved")
        record2 = _make_quarantine_record(game_id="002")

        self.s3_mgr.s3_client.get_object.side_effect = [
            {"Body": Mock(read=Mock(return_value=json.dumps(record1).encode("utf-8")))},
            {"Body": Mock(read=Mock(return_value=json.dumps(record2).encode("utf-8")))},
        ]

        items = [{"key": "key1.json"}, {"key": "key2.json"}]
        result = self.orchestrator.replay_batch(items)

        assert result.total == 2
        assert result.skipped == 1
        assert result.succeeded == 1
        assert result.failed == 0


# -- CLI --force Flag Tests ---------------------------------------------------


class TestForceFlag:
    """Test the --force CLI flag for replaying resolved records."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_replay_help_shows_force(self):
        """--force flag appears in replay help."""
        result = self.runner.invoke(cli, ["quarantine", "replay", "--help"])
        assert result.exit_code == 0
        assert "--force" in result.output

    @patch("app.quarantine_cli._get_replay_orchestrator")
    def test_force_flag_passed_to_orchestrator(self, mock_get_orch):
        """--force flag is passed through to replay_single."""
        mock_orch = Mock()
        mock_orch.replay_single.return_value = ReplayResult(
            s3_key="quarantine/key.json",
            success=True,
            transform_applied="identity",
        )
        mock_get_orch.return_value = mock_orch

        result = self.runner.invoke(
            cli,
            ["quarantine", "replay", "--force", "quarantine/key.json"],
        )
        assert result.exit_code == 0
        _, kwargs = mock_orch.replay_single.call_args
        assert kwargs["force"] is True

    @patch("app.quarantine_cli._get_replay_orchestrator")
    def test_skipped_result_formatting(self, mock_get_orch):
        """Skipped result is displayed with SKIPPED status."""
        mock_orch = Mock()
        mock_orch.replay_single.return_value = ReplayResult(
            s3_key="quarantine/key.json",
            success=True,
            skipped=True,
            error="Record is already resolved",
        )
        mock_get_orch.return_value = mock_orch

        result = self.runner.invoke(
            cli, ["quarantine", "replay", "quarantine/key.json"]
        )
        assert result.exit_code == 0
        assert "[SKIPPED]" in result.output

    def test_format_batch_summary_with_skipped(self):
        """Batch summary includes skipped count."""
        br = BatchReplayResult(
            total=3,
            succeeded=1,
            failed=0,
            skipped=2,
            results=[
                ReplayResult(
                    s3_key="k1.json", success=True, transform_applied="identity"
                ),
                ReplayResult(
                    s3_key="k2.json",
                    success=True,
                    skipped=True,
                    error="already resolved",
                ),
                ReplayResult(
                    s3_key="k3.json",
                    success=True,
                    skipped=True,
                    error="already resolved",
                ),
            ],
        )
        output = _format_batch_summary(br)
        assert "Skipped:   2" in output
