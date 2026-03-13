"""Tests for quarantine replay transforms."""

import pytest

from app.quarantine import ErrorClassification
from app.transforms import (
    IdentityTransform,
    ReplayTransform,
    RoundingToleranceTransform,
    SchemaRemapTransform,
    TransformError,
    get_transform_for_classification,
)

# -- Fixtures -----------------------------------------------------------------


def _make_quarantine_record(data, classification=None, issues=None):
    """Create a realistic quarantine record for testing."""
    if classification is None:
        classification = ErrorClassification.UNKNOWN.value
    return {
        "data": data,
        "validation_result": {
            "valid": False,
            "issues": issues or ["Test issue"],
        },
        "metadata": {
            "data_type": "box_score",
            "target_date": "2024-01-15",
            "quarantine_timestamp": "2024-01-15T04:30:25",
            "error_classification": classification,
            "issues_count": len(issues) if issues else 1,
            "validation_valid": False,
            "context": {},
        },
    }


def _make_box_score_data(
    home_players=None,
    away_players=None,
    home_team_stats=None,
    away_team_stats=None,
):
    """Create a realistic V3 box score data payload."""
    default_home_players = [
        {
            "personId": 203935,
            "firstName": "Jayson",
            "familyName": "Tatum",
            "statistics": {"points": 28, "rebounds": 10, "assists": 5},
        },
        {
            "personId": 203542,
            "firstName": "Jaylen",
            "familyName": "Brown",
            "statistics": {"points": 22, "rebounds": 6, "assists": 3},
        },
    ]
    default_away_players = [
        {
            "personId": 201566,
            "firstName": "Russell",
            "familyName": "Westbrook",
            "statistics": {"points": 20, "rebounds": 8, "assists": 10},
        },
    ]

    return {
        "boxScoreTraditional": {
            "gameId": "0022400001",
            "homeTeam": {
                "teamId": 1610612738,
                "teamName": "Celtics",
                "players": home_players or default_home_players,
                "statistics": home_team_stats
                or {"points": 50, "rebounds": 16, "assists": 8},
            },
            "awayTeam": {
                "teamId": 1610612747,
                "teamName": "Lakers",
                "players": away_players or default_away_players,
                "statistics": away_team_stats
                or {"points": 20, "rebounds": 8, "assists": 10},
            },
        }
    }


# -- ReplayTransform ABC Tests -----------------------------------------------


class TestReplayTransformABC:
    """Test the ReplayTransform abstract base class."""

    def test_cannot_instantiate_abc(self):
        """Test that ReplayTransform cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ReplayTransform()

    def test_subclass_must_implement_transform(self):
        """Test that subclasses must implement the transform method."""

        class IncompleteTransform(ReplayTransform):
            pass

        with pytest.raises(TypeError):
            IncompleteTransform()

    def test_subclass_with_transform_is_valid(self):
        """Test that a properly implemented subclass can be instantiated."""

        class ValidTransform(ReplayTransform):
            def transform(self, quarantine_record: dict) -> dict:
                return {"data": {}, "transform_metadata": {}}

        t = ValidTransform()
        assert isinstance(t, ReplayTransform)


# -- IdentityTransform Tests -------------------------------------------------


class TestIdentityTransform:
    """Test the IdentityTransform."""

    def setup_method(self):
        """Set up test fixtures."""
        self.transform = IdentityTransform()

    def test_returns_original_data_unchanged(self):
        """Test that identity transform returns data as-is."""
        data = {"key": "value", "nested": {"inner": 42}}
        record = _make_quarantine_record(data)
        result = self.transform.transform(record)

        assert result["data"] == data

    def test_returns_transform_metadata(self):
        """Test that identity transform includes metadata."""
        record = _make_quarantine_record({"key": "value"})
        result = self.transform.transform(record)

        assert result["transform_metadata"]["transform_type"] == "identity"
        assert result["transform_metadata"]["changes_applied"] == []

    def test_deep_copies_data(self):
        """Test that returned data is a deep copy, not a reference."""
        data = {"nested": {"mutable": [1, 2, 3]}}
        record = _make_quarantine_record(data)
        result = self.transform.transform(record)

        result["data"]["nested"]["mutable"].append(4)
        assert data["nested"]["mutable"] == [1, 2, 3]

    def test_handles_empty_data(self):
        """Test identity transform with empty data."""
        record = _make_quarantine_record({})
        result = self.transform.transform(record)

        assert result["data"] == {}

    def test_handles_missing_data_key(self):
        """Test identity transform when data key is missing."""
        record = {"validation_result": {}, "metadata": {}}
        result = self.transform.transform(record)

        assert result["data"] == {}

    def test_with_realistic_box_score(self):
        """Test identity transform with a realistic box score payload."""
        data = _make_box_score_data()
        record = _make_quarantine_record(
            data,
            classification="transient",
            issues=["Connection timeout occurred"],
        )
        result = self.transform.transform(record)

        assert result["data"] == data
        assert result["data"]["boxScoreTraditional"]["gameId"] == "0022400001"


# -- RoundingToleranceTransform Tests -----------------------------------------


class TestRoundingToleranceTransform:
    """Test the RoundingToleranceTransform."""

    def setup_method(self):
        """Set up test fixtures."""
        self.transform = RoundingToleranceTransform(tolerance=0.01)

    def test_no_adjustment_when_sums_match(self):
        """Test that no changes are made when player sums already match team totals."""
        data = _make_box_score_data()
        record = _make_quarantine_record(data)
        result = self.transform.transform(record)

        assert result["transform_metadata"]["changes_applied"] == []

    def test_adjusts_within_tolerance(self):
        """Test that player stats are adjusted when discrepancy is within tolerance."""
        home_team_stats = {"points": 50.005, "rebounds": 16, "assists": 8}
        data = _make_box_score_data(home_team_stats=home_team_stats)
        record = _make_quarantine_record(data)
        result = self.transform.transform(record)

        changes = result["transform_metadata"]["changes_applied"]
        assert len(changes) == 1
        assert changes[0]["stat"] == "points"
        assert changes[0]["player"] == "Jaylen Brown"
        assert changes[0]["old_value"] == 22
        assert abs(changes[0]["delta"] - 0.005) < 1e-10

    def test_raises_when_exceeds_tolerance(self):
        """Test that TransformError is raised when discrepancy exceeds tolerance."""
        home_team_stats = {"points": 60, "rebounds": 16, "assists": 8}
        data = _make_box_score_data(home_team_stats=home_team_stats)
        record = _make_quarantine_record(data)

        with pytest.raises(TransformError, match="exceeds tolerance"):
            self.transform.transform(record)

    def test_custom_tolerance(self):
        """Test with a larger custom tolerance."""
        transform = RoundingToleranceTransform(tolerance=1.0)
        home_team_stats = {"points": 50.5, "rebounds": 16, "assists": 8}
        data = _make_box_score_data(home_team_stats=home_team_stats)
        record = _make_quarantine_record(data)
        result = transform.transform(record)

        changes = result["transform_metadata"]["changes_applied"]
        assert len(changes) == 1
        assert changes[0]["delta"] == 0.5

    def test_adjusts_multiple_stats(self):
        """Test adjustments across multiple stat categories."""
        home_team_stats = {"points": 50.005, "rebounds": 16.005, "assists": 8}
        data = _make_box_score_data(home_team_stats=home_team_stats)
        record = _make_quarantine_record(data)
        result = self.transform.transform(record)

        changes = result["transform_metadata"]["changes_applied"]
        stats_adjusted = {c["stat"] for c in changes}
        assert stats_adjusted == {"points", "rebounds"}

    def test_adjusts_both_teams(self):
        """Test that adjustments are applied to both home and away teams."""
        home_team_stats = {"points": 50.005, "rebounds": 16, "assists": 8}
        away_team_stats = {"points": 20.005, "rebounds": 8, "assists": 10}
        data = _make_box_score_data(
            home_team_stats=home_team_stats,
            away_team_stats=away_team_stats,
        )
        record = _make_quarantine_record(data)
        result = self.transform.transform(record)

        changes = result["transform_metadata"]["changes_applied"]
        teams_adjusted = {c["team"] for c in changes}
        assert teams_adjusted == {"homeTeam", "awayTeam"}

    def test_raises_for_non_v3_format(self):
        """Test that TransformError is raised for non-V3 format data."""
        data = {"resultSets": [{"name": "PlayerStats"}]}
        record = _make_quarantine_record(data)

        with pytest.raises(TransformError, match="boxScoreTraditional"):
            self.transform.transform(record)

    def test_transform_metadata_includes_tolerance(self):
        """Test that transform metadata includes the tolerance value."""
        data = _make_box_score_data()
        record = _make_quarantine_record(data)
        result = self.transform.transform(record)

        assert result["transform_metadata"]["transform_type"] == "rounding_tolerance"
        assert result["transform_metadata"]["tolerance"] == 0.01

    def test_deep_copies_data(self):
        """Test that returned data is a deep copy."""
        data = _make_box_score_data()
        record = _make_quarantine_record(data)
        result = self.transform.transform(record)

        original_points = data["boxScoreTraditional"]["homeTeam"]["players"][0][
            "statistics"
        ]["points"]
        result["data"]["boxScoreTraditional"]["homeTeam"]["players"][0]["statistics"][
            "points"
        ] = 999
        assert (
            data["boxScoreTraditional"]["homeTeam"]["players"][0]["statistics"][
                "points"
            ]
            == original_points
        )

    def test_skips_teams_without_players(self):
        """Test that teams without players are skipped gracefully."""
        data = _make_box_score_data()
        data["boxScoreTraditional"]["homeTeam"]["players"] = []
        record = _make_quarantine_record(data)
        result = self.transform.transform(record)

        assert result["transform_metadata"]["changes_applied"] == []

    def test_skips_teams_without_statistics(self):
        """Test that teams without statistics are skipped gracefully."""
        data = _make_box_score_data()
        data["boxScoreTraditional"]["homeTeam"]["statistics"] = {}
        record = _make_quarantine_record(data)
        result = self.transform.transform(record)

        # Only away team changes could potentially happen
        home_changes = [
            c
            for c in result["transform_metadata"]["changes_applied"]
            if c["team"] == "homeTeam"
        ]
        assert home_changes == []

    def test_negative_delta_adjustment(self):
        """Test adjustment when player sum exceeds team total."""
        home_team_stats = {"points": 49.995, "rebounds": 16, "assists": 8}
        data = _make_box_score_data(home_team_stats=home_team_stats)
        record = _make_quarantine_record(data)
        result = self.transform.transform(record)

        changes = result["transform_metadata"]["changes_applied"]
        assert len(changes) == 1
        assert changes[0]["delta"] < 0


# -- SchemaRemapTransform Tests ----------------------------------------------


class TestSchemaRemapTransform:
    """Test the SchemaRemapTransform."""

    def test_simple_key_remap(self):
        """Test simple key renaming."""
        field_map = {"oldKey": "newKey"}
        transform = SchemaRemapTransform(field_map)
        record = _make_quarantine_record({"oldKey": "value"})
        result = transform.transform(record)

        assert "newKey" in result["data"]
        assert "oldKey" not in result["data"]
        assert result["data"]["newKey"] == "value"

    def test_recursive_key_remap(self):
        """Test that key renaming is applied recursively."""
        field_map = {"old": "new"}
        transform = SchemaRemapTransform(field_map)
        data = {"old": {"old": "inner_value"}}
        record = _make_quarantine_record(data)
        result = transform.transform(record)

        assert result["data"] == {"new": {"new": "inner_value"}}

    def test_remap_in_lists(self):
        """Test that key renaming works inside list elements."""
        field_map = {"name": "playerName"}
        transform = SchemaRemapTransform(field_map)
        data = {"players": [{"name": "LeBron"}, {"name": "AD"}]}
        record = _make_quarantine_record(data)
        result = transform.transform(record)

        assert result["data"]["players"][0]["playerName"] == "LeBron"
        assert result["data"]["players"][1]["playerName"] == "AD"

    def test_unmapped_keys_preserved(self):
        """Test that keys not in the field_map are preserved."""
        field_map = {"old": "new"}
        transform = SchemaRemapTransform(field_map)
        data = {"old": "remapped", "keep": "preserved"}
        record = _make_quarantine_record(data)
        result = transform.transform(record)

        assert result["data"]["new"] == "remapped"
        assert result["data"]["keep"] == "preserved"

    def test_multiple_key_remaps(self):
        """Test remapping multiple keys at once."""
        field_map = {"firstName": "first_name", "lastName": "last_name"}
        transform = SchemaRemapTransform(field_map)
        data = {"firstName": "Jayson", "lastName": "Tatum", "team": "Celtics"}
        record = _make_quarantine_record(data)
        result = transform.transform(record)

        assert result["data"] == {
            "first_name": "Jayson",
            "last_name": "Tatum",
            "team": "Celtics",
        }

    def test_transform_metadata(self):
        """Test that transform metadata documents the field map."""
        field_map = {"old": "new"}
        transform = SchemaRemapTransform(field_map)
        record = _make_quarantine_record({"old": "value"})
        result = transform.transform(record)

        meta = result["transform_metadata"]
        assert meta["transform_type"] == "schema_remap"
        assert meta["field_map"] == {"old": "new"}
        assert len(meta["changes_applied"]) == 1

    def test_empty_field_map_raises(self):
        """Test that an empty field_map raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            SchemaRemapTransform({})

    def test_deep_copies_data(self):
        """Test that returned data is a deep copy."""
        field_map = {"a": "b"}
        transform = SchemaRemapTransform(field_map)
        data = {"a": [1, 2, 3]}
        record = _make_quarantine_record(data)
        result = transform.transform(record)

        result["data"]["b"].append(4)
        assert data["a"] == [1, 2, 3]

    def test_realistic_api_version_remap(self):
        """Test remapping from legacy API field names to V3 names."""
        field_map = {
            "resultSets": "boxScoreTraditional",
            "PLAYER_NAME": "playerName",
            "PTS": "points",
        }
        transform = SchemaRemapTransform(field_map)
        data = {"resultSets": {"players": [{"PLAYER_NAME": "LeBron", "PTS": 30}]}}
        record = _make_quarantine_record(data)
        result = transform.transform(record)

        assert "boxScoreTraditional" in result["data"]
        player = result["data"]["boxScoreTraditional"]["players"][0]
        assert player["playerName"] == "LeBron"
        assert player["points"] == 30


# -- Factory Function Tests ---------------------------------------------------


class TestGetTransformForClassification:
    """Test the get_transform_for_classification factory function."""

    def test_transient_returns_identity(self):
        """Test that TRANSIENT classification returns IdentityTransform."""
        t = get_transform_for_classification(ErrorClassification.TRANSIENT)
        assert isinstance(t, IdentityTransform)

    def test_rounding_mismatch_returns_rounding_transform(self):
        """Test that ROUNDING_MISMATCH returns RoundingToleranceTransform."""
        t = get_transform_for_classification(ErrorClassification.ROUNDING_MISMATCH)
        assert isinstance(t, RoundingToleranceTransform)

    def test_schema_change_returns_schema_remap(self):
        """Test SCHEMA_CHANGE returns SchemaRemapTransform with field_map."""
        t = get_transform_for_classification(
            ErrorClassification.SCHEMA_CHANGE,
            field_map={"old": "new"},
        )
        assert isinstance(t, SchemaRemapTransform)

    def test_schema_change_without_field_map_falls_back(self):
        """Test SCHEMA_CHANGE without field_map falls back gracefully."""
        t = get_transform_for_classification(ErrorClassification.SCHEMA_CHANGE)
        assert isinstance(t, IdentityTransform)

    def test_data_quality_returns_identity(self):
        """Test that DATA_QUALITY classification returns IdentityTransform."""
        t = get_transform_for_classification(ErrorClassification.DATA_QUALITY)
        assert isinstance(t, IdentityTransform)

    def test_unknown_returns_identity(self):
        """Test that UNKNOWN classification returns IdentityTransform."""
        t = get_transform_for_classification(ErrorClassification.UNKNOWN)
        assert isinstance(t, IdentityTransform)

    def test_custom_override_takes_precedence(self):
        """Test that a custom override is returned regardless of classification."""

        class CustomTransform(ReplayTransform):
            def transform(self, quarantine_record: dict) -> dict:
                return {"data": {}, "transform_metadata": {"custom": True}}

        custom = CustomTransform()
        t = get_transform_for_classification(
            ErrorClassification.TRANSIENT, override=custom
        )
        assert t is custom

    def test_rounding_mismatch_with_custom_tolerance(self):
        """Test passing custom tolerance to RoundingToleranceTransform."""
        t = get_transform_for_classification(
            ErrorClassification.ROUNDING_MISMATCH,
            tolerance=0.5,
        )
        assert isinstance(t, RoundingToleranceTransform)
        assert t.tolerance == 0.5
