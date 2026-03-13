"""
Quarantine patch transforms for replaying quarantined data.

Provides a pluggable transformation layer that can patch or adjust
quarantined data before replaying it through the Silver validation
pipeline. Transforms are pure functions with no side effects -- they
only modify and return data.

Design follows the Strategy pattern for clean extensibility.
"""

import copy
import logging
from abc import ABC, abstractmethod
from typing import Any

from .quarantine import ErrorClassification

logger = logging.getLogger(__name__)


class TransformError(Exception):
    """Raised when a transform cannot be applied to the given data."""


class ReplayTransform(ABC):
    """
    Abstract base class for quarantine replay transforms.

    Each transform takes a quarantine record and returns a transformed
    payload ready for Silver validation, along with metadata documenting
    what changes were applied.
    """

    @abstractmethod
    def transform(self, quarantine_record: dict) -> dict:
        """
        Transform a quarantine record for replay.

        Args:
            quarantine_record: The quarantine record dict containing
                'data', 'validation_result', and 'metadata' keys.

        Returns:
            A new dict with the transformed 'data' and a
            'transform_metadata' dict documenting changes applied.
        """


class IdentityTransform(ReplayTransform):
    """
    Returns the original data unchanged.

    Used for transient error replays where the original payload is
    valid but failed due to external factors (timeouts, rate limits).
    """

    def transform(self, quarantine_record: dict) -> dict:
        """Return the original data unchanged."""
        return {
            "data": copy.deepcopy(quarantine_record.get("data", {})),
            "transform_metadata": {
                "transform_type": "identity",
                "changes_applied": [],
                "description": "No changes applied -- original data returned as-is.",
            },
        }


class RoundingToleranceTransform(ReplayTransform):
    """
    Adjusts player stat sums to reconcile with team totals.

    For each stat category, computes the sum of player values and
    compares to the team total. If the discrepancy is within the
    configurable tolerance, adjusts the last player's value to make
    the sum exact. If the discrepancy exceeds the tolerance, raises
    a TransformError.
    """

    # Stat categories to check for rounding mismatches
    STAT_CATEGORIES = [
        "points",
        "rebounds",
        "assists",
        "steals",
        "blocks",
        "turnovers",
        "fouls",
        "fgm",
        "fga",
        "ftm",
        "fta",
        "fg3m",
        "fg3a",
        "oreb",
        "dreb",
    ]

    def __init__(self, tolerance: float = 0.01):
        """
        Initialize with configurable tolerance.

        Args:
            tolerance: Maximum acceptable discrepancy between player
                sum and team total (default: 0.01 per ADR-028).
        """
        self.tolerance = tolerance

    def transform(self, quarantine_record: dict) -> dict:
        """Adjust player stat sums to match team totals within tolerance."""
        data = copy.deepcopy(quarantine_record.get("data", {}))
        changes: list[dict[str, Any]] = []

        box_score = data.get("boxScoreTraditional")
        if not box_score:
            raise TransformError(
                "RoundingToleranceTransform requires V3 boxScoreTraditional format."
            )

        for team_key in ("homeTeam", "awayTeam"):
            team = box_score.get(team_key, {})
            team_stats = team.get("statistics", {})
            players = team.get("players", [])

            if not players or not team_stats:
                continue

            for stat in self.STAT_CATEGORIES:
                if stat not in team_stats:
                    continue

                team_value = team_stats[stat]
                player_values = [p.get("statistics", {}).get(stat, 0) for p in players]
                player_sum = sum(player_values)
                delta = team_value - player_sum

                if delta == 0:
                    continue

                if abs(delta) > self.tolerance:
                    raise TransformError(
                        f"Discrepancy for {team_key} {stat} exceeds tolerance: "
                        f"player_sum={player_sum}, team_value={team_value}, "
                        f"delta={delta}, tolerance={self.tolerance}"
                    )

                # Adjust the last player's value to make the sum exact
                last_player = players[-1]
                last_stats = last_player.get("statistics", {})
                old_value = last_stats.get(stat, 0)
                new_value = old_value + delta

                last_stats[stat] = new_value

                player_name = (
                    f"{last_player.get('firstName', '')} "
                    f"{last_player.get('familyName', '')}"
                ).strip()

                change_record = {
                    "team": team_key,
                    "player": player_name,
                    "stat": stat,
                    "old_value": old_value,
                    "new_value": new_value,
                    "delta": delta,
                }
                changes.append(change_record)

                logger.info(
                    f"Adjusted player {player_name} {stat} "
                    f"from {old_value} to {new_value} (delta: {delta})"
                )

        return {
            "data": data,
            "transform_metadata": {
                "transform_type": "rounding_tolerance",
                "tolerance": self.tolerance,
                "changes_applied": changes,
                "description": (
                    f"Adjusted {len(changes)} stat value(s) to reconcile "
                    f"player sums with team totals within tolerance "
                    f"{self.tolerance}."
                ),
            },
        }


class SchemaRemapTransform(ReplayTransform):
    """
    Applies a field-mapping dictionary to adapt payloads.

    Useful when the NBA API changes field names between versions
    (e.g., V3 'boxScoreTraditional' vs. legacy 'resultSets').
    Applies key renaming recursively throughout the payload.
    """

    def __init__(self, field_map: dict[str, str]):
        """
        Initialize with a field mapping.

        Args:
            field_map: Dictionary mapping old field names to new field
                names (e.g., {'oldKey': 'newKey'}).
        """
        if not field_map:
            raise ValueError("field_map must be a non-empty dictionary.")
        self.field_map = field_map

    def transform(self, quarantine_record: dict) -> dict:
        """Apply field remapping to the quarantine record data."""
        data = copy.deepcopy(quarantine_record.get("data", {}))
        remapped_data = self._remap_keys(data)
        remapped_fields = [
            {"old_key": old, "new_key": new} for old, new in self.field_map.items()
        ]

        return {
            "data": remapped_data,
            "transform_metadata": {
                "transform_type": "schema_remap",
                "field_map": self.field_map,
                "changes_applied": remapped_fields,
                "description": (
                    f"Remapped {len(self.field_map)} field name(s) "
                    f"to adapt payload to expected schema."
                ),
            },
        }

    def _remap_keys(self, obj: Any) -> Any:
        """Recursively remap keys in a nested structure."""
        if isinstance(obj, dict):
            return {
                self.field_map.get(k, k): self._remap_keys(v) for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [self._remap_keys(item) for item in obj]
        return obj


# -- Factory ------------------------------------------------------------------


# Default transform mapping for each error classification
_DEFAULT_TRANSFORMS: dict[ErrorClassification, type[ReplayTransform]] = {
    ErrorClassification.TRANSIENT: IdentityTransform,
    ErrorClassification.ROUNDING_MISMATCH: RoundingToleranceTransform,
    ErrorClassification.SCHEMA_CHANGE: SchemaRemapTransform,
    ErrorClassification.DATA_QUALITY: IdentityTransform,
    ErrorClassification.UNKNOWN: IdentityTransform,
}


def get_transform_for_classification(
    classification: ErrorClassification,
    override: ReplayTransform | None = None,
    **kwargs: Any,
) -> ReplayTransform:
    """
    Get the default transform for a given error classification.

    Args:
        classification: The error classification to look up.
        override: Optional custom transform to use instead of the
            default. If provided, this takes precedence.
        **kwargs: Additional keyword arguments passed to the transform
            constructor (e.g., tolerance for RoundingToleranceTransform,
            field_map for SchemaRemapTransform).

    Returns:
        A ReplayTransform instance appropriate for the classification.

    Raises:
        ValueError: If the classification requires constructor arguments
            (e.g., SchemaRemapTransform needs field_map) and none are
            provided.
    """
    if override is not None:
        return override

    transform_cls = _DEFAULT_TRANSFORMS.get(classification)
    if transform_cls is None:
        return IdentityTransform()

    try:
        return transform_cls(**kwargs)
    except (TypeError, ValueError):
        return IdentityTransform()
