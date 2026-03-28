"""
Fetcher module for Gold artifact discovery and download.

Supports loading Gold JSON artifacts from:
  1. A local directory (mirrors the S3 served/ key structure)
  2. An AWS S3 bucket (uses paginated list + direct download)

The returned GoldDataset holds all data in memory ready for the
two-phase compile step (DuckDB + SQLite).
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column lists — the subset of each JSON artifact that maps to the DB schema.
# Any extra fields in the JSON (e.g. `lineage`, `partition_key`) are ignored.
# ---------------------------------------------------------------------------

PLAYER_DAILY_COLUMNS: list[str] = [
    "player_id",
    "player_name",
    "team",
    "position",
    "game_id",
    "game_date",
    "season",
    "points",
    "rebounds",
    "assists",
    "steals",
    "blocks",
    "turnovers",
    "field_goals_made",
    "field_goals_attempted",
    "three_pointers_made",
    "three_pointers_attempted",
    "free_throws_made",
    "free_throws_attempted",
    "minutes_played",
    "efficiency_rating",
    "true_shooting_percentage",
    "usage_rate",
    "plus_minus",
]

TEAM_DAILY_COLUMNS: list[str] = [
    "team_id",
    "team_name",
    "game_id",
    "game_date",
    "season",
    "points",
    "field_goals_made",
    "field_goals_attempted",
    "three_pointers_made",
    "three_pointers_attempted",
    "free_throws_made",
    "free_throws_attempted",
    "rebounds",
    "assists",
    "steals",
    "blocks",
    "turnovers",
    "fouls",
    "offensive_rating",
    "defensive_rating",
    "pace",
    "true_shooting_percentage",
    "opponent_team_id",
    "home_game",
    "win",
]

PLAYER_SEASON_COLUMNS: list[str] = [
    "player_id",
    "player_name",
    "season",
    "team",
    "total_games",
    "total_minutes",
    "points_per_game",
    "rebounds_per_game",
    "assists_per_game",
    "steals_per_game",
    "blocks_per_game",
    "turnovers_per_game",
    "field_goal_percentage",
    "three_point_percentage",
    "free_throw_percentage",
    "efficiency_rating",
    "true_shooting_percentage",
    "usage_rate",
    "scoring_trend",
    "efficiency_trend",
]

TEAM_SEASON_COLUMNS: list[str] = [
    "team_id",
    "team_name",
    "season",
    "season_type",
    "total_games",
    "total_points",
    "total_points_allowed",
    "points_per_game",
    "points_allowed_per_game",
    "assists_per_game",
    "total_rebounds_per_game",
    "turnovers_per_game",
    "field_goal_percentage",
    "three_point_percentage",
    "free_throw_percentage",
    "true_shooting_percentage",
    "effective_field_goal_percentage",
    "offensive_rating",
    "defensive_rating",
    "net_rating",
    "pace",
    "turnover_percentage",
    "offensive_rebound_percentage",
    "free_throw_rate",
    "data_quality_score",
]

# Columns produced by _parse_top_list() — matches the top_lists schema table.
TOP_LISTS_COLUMNS: list[str] = [
    "metric",
    "list_date",
    "rank",
    "player_id",
    "player_name",
    "team",
    "value",
]


# ---------------------------------------------------------------------------
# In-memory dataset
# ---------------------------------------------------------------------------


@dataclass
class GoldDataset:
    """In-memory representation of all Gold layer artifacts.

    Each field is a list of plain dicts with keys matching the corresponding
    DB schema column names.  The top_lists list is pre-flattened so that each
    entry represents one player row in the top_lists table.
    """

    player_daily_stats: list[dict] = field(default_factory=list)
    team_daily_stats: list[dict] = field(default_factory=list)
    player_season_summary: list[dict] = field(default_factory=list)
    team_season_summary: list[dict] = field(default_factory=list)
    top_lists: list[dict] = field(default_factory=list)

    def summary(self) -> str:
        """Return a human-readable summary of dataset row counts."""
        return (
            f"GoldDataset("
            f"player_daily={len(self.player_daily_stats)}, "
            f"team_daily={len(self.team_daily_stats)}, "
            f"player_season={len(self.player_season_summary)}, "
            f"team_season={len(self.team_season_summary)}, "
            f"top_list_rows={len(self.top_lists)})"
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_fields(data: dict, columns: list[str]) -> dict:
    """Return a new dict containing only the keys in *columns*.

    Missing keys default to None so that every returned dict has exactly
    the same set of keys regardless of which optional fields the source
    JSON omitted (due to exclude_none serialisation).
    """
    return {col: data.get(col) for col in columns}


def _parse_top_list(data: dict) -> list[dict]:
    """Flatten a top-list JSON artifact into one row per player entry.

    The source JSON format is::

        {
          "metric": "Points Leaders",
          "date": "2024-01-15",
          "players": [
            {"rank": 1, "player_id": "2544", "player_name": "...",
             "team": "LAL", "value": 38.0},
            ...
          ]
        }

    Each player entry becomes a row in the top_lists table with the
    ``list_date`` column sourced from the top-level ``date`` field.
    """
    metric = data.get("metric", "")
    list_date = data.get("date", "")
    rows = []
    for player in data.get("players", []):
        rows.append(
            {
                "metric": metric,
                "list_date": list_date,
                "rank": player.get("rank"),
                "player_id": player.get("player_id"),
                "player_name": player.get("player_name"),
                "team": player.get("team"),
                "value": player.get("value"),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Public loaders
# ---------------------------------------------------------------------------


def load_from_local_dir(local_dir: str) -> GoldDataset:
    """Load Gold artifacts from a local directory.

    The directory must mirror the S3 served/ key structure::

        {local_dir}/player_daily/{date}/{player_id}.json
        {local_dir}/team_daily/{date}/{team_id}.json
        {local_dir}/top_lists/{date}/{metric}.json
        {local_dir}/season_player/{season}/{player_id}.json
        {local_dir}/season_team/{season}/{team_id}.json   (optional)

    Files that cannot be parsed are skipped with a warning.

    Args:
        local_dir: Root directory containing Gold JSON artifacts.

    Returns:
        GoldDataset populated from all discovered files.
    """
    base = Path(local_dir)
    dataset = GoldDataset()

    def _load_glob(pattern: str, columns: list[str]) -> list[dict]:
        rows = []
        for json_file in sorted(base.glob(pattern)):
            try:
                data = json.loads(json_file.read_text())
                rows.append(_extract_fields(data, columns))
            except Exception as exc:
                logger.warning("Skipping %s: %s", json_file, exc)
        return rows

    dataset.player_daily_stats = _load_glob(
        "player_daily/**/*.json", PLAYER_DAILY_COLUMNS
    )
    dataset.team_daily_stats = _load_glob("team_daily/**/*.json", TEAM_DAILY_COLUMNS)
    dataset.player_season_summary = _load_glob(
        "season_player/**/*.json", PLAYER_SEASON_COLUMNS
    )
    dataset.team_season_summary = _load_glob(
        "season_team/**/*.json", TEAM_SEASON_COLUMNS
    )

    # Top lists require special flattening
    for json_file in sorted(base.glob("top_lists/**/*.json")):
        try:
            data = json.loads(json_file.read_text())
            dataset.top_lists.extend(_parse_top_list(data))
        except Exception as exc:
            logger.warning("Skipping %s: %s", json_file, exc)

    logger.info("Loaded from local dir: %s", dataset.summary())
    return dataset


def load_from_s3(
    bucket: str,
    served_prefix: str = "served",
    season: str | None = None,
    aws_region: str = "us-east-1",
) -> GoldDataset:
    """Load Gold artifacts from an S3 bucket using paginated listing.

    Lists all objects under the relevant served/ sub-prefixes and downloads
    each JSON file.  Optionally narrows season summaries to a specific season.

    Args:
        bucket: S3 bucket name containing the Gold artifacts.
        served_prefix: Top-level S3 key prefix (default: ``"served"``).
        season: Optional season filter for season-level artifacts
            (e.g. ``"2024-25"``).  Daily artifacts are always loaded in full.
        aws_region: AWS region for the S3 client.

    Returns:
        GoldDataset populated from all discovered S3 objects.
    """
    import boto3
    from botocore.exceptions import ClientError

    s3 = boto3.client("s3", region_name=aws_region)
    dataset = GoldDataset()

    def _list_keys(prefix: str) -> list[str]:
        keys: list[str] = []
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        return keys

    def _download(key: str) -> dict | None:
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            return json.loads(response["Body"].read().decode("utf-8"))
        except ClientError as exc:
            logger.warning("Failed to download s3://%s/%s: %s", bucket, key, exc)
            return None

    def _load_prefix(prefix: str, columns: list[str]) -> list[dict]:
        rows = []
        for key in _list_keys(prefix):
            if not key.endswith(".json"):
                continue
            data = _download(key)
            if data is not None:
                rows.append(_extract_fields(data, columns))
        return rows

    dataset.player_daily_stats = _load_prefix(
        f"{served_prefix}/player_daily/", PLAYER_DAILY_COLUMNS
    )
    dataset.team_daily_stats = _load_prefix(
        f"{served_prefix}/team_daily/", TEAM_DAILY_COLUMNS
    )

    # Narrow season summaries to a specific season when requested
    player_season_prefix = f"{served_prefix}/season_player/"
    team_season_prefix = f"{served_prefix}/season_team/"
    if season:
        player_season_prefix = f"{player_season_prefix}{season}/"
        team_season_prefix = f"{team_season_prefix}{season}/"

    dataset.player_season_summary = _load_prefix(
        player_season_prefix, PLAYER_SEASON_COLUMNS
    )
    dataset.team_season_summary = _load_prefix(team_season_prefix, TEAM_SEASON_COLUMNS)

    # Top lists need flattening
    for key in _list_keys(f"{served_prefix}/top_lists/"):
        if not key.endswith(".json"):
            continue
        data = _download(key)
        if data is not None:
            dataset.top_lists.extend(_parse_top_list(data))

    logger.info("Loaded from S3 bucket '%s': %s", bucket, dataset.summary())
    return dataset
