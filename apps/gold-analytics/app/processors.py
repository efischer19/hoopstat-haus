"""
Gold layer analytics processors for NBA statistics.

This module provides processors for transforming Silver layer data into
advanced analytics metrics and player season aggregations.
"""

from datetime import date
from typing import Any

import pandas as pd
from hoopstat_data.transforms import PlayerSeasonAggregator, TeamSeasonAggregator
from hoopstat_observability import get_logger

from .config import GoldAnalyticsConfig, load_config

# TODO: IcebergS3TablesWriter removed per ADR-028 (S3 Tables out-of-scope for v1)
# Need to implement JSON artifact writing to served/ prefix instead
from .performance import performance_context, performance_monitor
from .s3_discovery import S3DataDiscovery
from .validation import (
    DataValidator,
)

logger = get_logger(__name__)


class GoldProcessor:
    """
    Processor for Gold layer analytics calculations and season aggregations.

    Transforms Silver layer NBA data into advanced analytics metrics
    and season summaries with comprehensive statistical calculations.
    """

    def __init__(
        self,
        silver_bucket: str,
        gold_bucket: str,
        config: GoldAnalyticsConfig | None = None,
    ) -> None:
        """
        Initialize the Gold processor.

        Args:
            silver_bucket: S3 bucket containing Silver layer data
            gold_bucket: S3 bucket for Gold layer data storage
            config: Optional configuration object (will be loaded if not provided)
        """
        # Use provided config or load from environment
        if config is None:
            try:
                self.config = load_config()
            except ValueError:
                # Fall back to basic config if environment variables not set
                self.config = GoldAnalyticsConfig(
                    silver_bucket=silver_bucket, gold_bucket=gold_bucket
                )
        else:
            self.config = config

        self.silver_bucket = silver_bucket
        self.gold_bucket = gold_bucket
        self.season_aggregator = PlayerSeasonAggregator(validation_mode="lenient")
        self.team_aggregator = TeamSeasonAggregator(validation_mode="lenient")

        # Initialize components
        # TODO: Replace with JSON artifact writer per ADR-028
        # self.iceberg_writer = IcebergS3TablesWriter(gold_bucket)
        self.s3_discovery = S3DataDiscovery(self.config)
        self.validator = DataValidator(validation_mode="lenient")

        logger.info(
            f"Initialized GoldProcessor with silver_bucket={silver_bucket}, "
            f"gold_bucket={gold_bucket}"
        )

    def process_season_aggregation(
        self, season: str, player_id: str | None = None, dry_run: bool = False
    ) -> bool:
        """
        Process season-level player statistics aggregation.

        Args:
            season: Season to process (e.g., "2023-24")
            player_id: Specific player to process, or None for all players
            dry_run: If True, log operations without making changes

        Returns:
            True if processing succeeded, False otherwise
        """
        logger.info(f"Processing season aggregation for season: {season}")

        if dry_run:
            logger.info("Dry run mode - no data will be stored")

        try:
            # Load all player game stats for the season
            player_games_data = self._load_season_player_games(
                season, player_id, dry_run
            )

            if not player_games_data:
                logger.warning(f"No player game data found for season {season}")
                return True

            # Group by player and aggregate
            aggregated_seasons = {}
            for player, games in player_games_data.items():
                season_stats = self.season_aggregator.aggregate_season_stats(
                    games, season, "regular"
                )
                if season_stats.get("total_games", 0) > 0:
                    aggregated_seasons[player] = season_stats

            if not dry_run and aggregated_seasons:
                self._store_season_aggregations(aggregated_seasons, season)
            else:
                logger.info(
                    f"Would store season stats for {len(aggregated_seasons)} players"
                )

            logger.info(f"Successfully processed season aggregation for {season}")
            return True

        except Exception as e:
            logger.error(f"Failed to process season aggregation for {season}: {e}")
            return False

    def process_team_season_aggregation(
        self, season: str, team_id: str | None = None, dry_run: bool = False
    ) -> bool:
        """
        Process season-level team statistics aggregation.

        Args:
            season: Season to process (e.g., "2023-24")
            team_id: Specific team to process, or None for all teams
            dry_run: If True, log operations without making changes

        Returns:
            True if processing succeeded, False otherwise
        """
        logger.info(f"Processing team season aggregation for season: {season}")

        if dry_run:
            logger.info("Dry run mode - no data will be stored")

        try:
            # Load all team game stats for the season
            team_games_data = self._load_season_team_games(season, team_id, dry_run)

            if not team_games_data:
                logger.warning(f"No team game data found for season {season}")
                return True

            # Group by team and aggregate
            aggregated_seasons = {}
            for team, games in team_games_data.items():
                season_stats = self.team_aggregator.aggregate_season_stats(
                    games, season, "regular"
                )
                if season_stats.get("total_games", 0) > 0:
                    aggregated_seasons[team] = season_stats

            if not dry_run and aggregated_seasons:
                self._store_team_season_aggregations(aggregated_seasons, season)
            else:
                logger.info(
                    f"Would store team season stats for {len(aggregated_seasons)} teams"
                )

            logger.info(f"Successfully processed team season aggregation for {season}")
            return True

        except Exception as e:
            logger.error(f"Failed to process team season aggregation for {season}: {e}")
            return False

    @performance_monitor("load_season_team_games")
    def _load_season_team_games(
        self, season: str, team_id: str | None = None, dry_run: bool = False
    ) -> dict[str, list[dict]]:
        """
        Load all team game statistics for a season.

        Args:
            season: Season to load data for
            team_id: Specific team to load, or None for all teams
            dry_run: If True, return mock data

        Returns:
            Dictionary mapping team_id to list of game statistics
        """
        if dry_run:
            # Mock season data for testing
            mock_games = [
                {
                    "team_id": "1610612747",  # Lakers
                    "team_name": "Los Angeles Lakers",
                    "points": 110,
                    "points_allowed": 105,
                    "field_goals_made": 42,
                    "field_goals_attempted": 85,
                    "three_pointers_made": 12,
                    "three_pointers_attempted": 35,
                    "free_throws_made": 14,
                    "free_throws_attempted": 18,
                    "offensive_rebounds": 12,
                    "defensive_rebounds": 32,
                    "total_rebounds": 44,
                    "assists": 25,
                    "steals": 8,
                    "blocks": 5,
                    "turnovers": 15,
                    "is_home": True,
                    "win": True,
                    "game_date": "2024-01-15",
                },
                {
                    "team_id": "1610612747",  # Lakers
                    "team_name": "Los Angeles Lakers",
                    "points": 98,
                    "points_allowed": 102,
                    "field_goals_made": 38,
                    "field_goals_attempted": 88,
                    "three_pointers_made": 8,
                    "three_pointers_attempted": 32,
                    "free_throws_made": 14,
                    "free_throws_attempted": 20,
                    "offensive_rebounds": 10,
                    "defensive_rebounds": 35,
                    "total_rebounds": 45,
                    "assists": 22,
                    "steals": 6,
                    "blocks": 3,
                    "turnovers": 18,
                    "is_home": False,
                    "win": False,
                    "game_date": "2024-01-18",
                },
            ]

            if team_id:
                return {team_id: mock_games}
            else:
                return {"1610612747": mock_games, "1610612738": mock_games[:1]}

        logger.info(f"Loading season team games for {season}")

        # Use S3DataDiscovery to find all dates with team data for the season
        from datetime import date as date_class

        # Determine season date range (simplified)
        season_year = int(season.split("-")[0])
        start_date = date_class(season_year, 10, 1)  # October 1st
        end_date = date_class(season_year + 1, 6, 30)  # June 30th

        # Find available dates
        available_dates = self.s3_discovery.discover_dates_to_process(
            start_date, end_date, "team_stats"
        )

        if not available_dates:
            logger.warning(f"No team data found for season {season}")
            return {}

        # Load and aggregate all team games for the season
        all_team_games = {}

        with performance_context("season_team_games_loading") as ctx:
            for process_date in available_dates:
                try:
                    daily_data = self.s3_discovery.load_all_silver_data(
                        process_date, "team_stats"
                    )

                    if daily_data.empty:
                        continue

                    # Group by team_id and add to season data
                    for _, row in daily_data.iterrows():
                        tid = row.get("team_id")
                        if tid and (team_id is None or tid == team_id):
                            if tid not in all_team_games:
                                all_team_games[tid] = []

                            # Convert row to game dict
                            game_dict = row.to_dict()
                            game_dict["game_date"] = process_date.strftime("%Y-%m-%d")
                            all_team_games[tid].append(game_dict)

                    ctx["records_processed"] += len(daily_data)

                except Exception as e:
                    logger.warning(f"Failed to load team data for {process_date}: {e}")
                    continue

        logger.info(f"Loaded season data for {len(all_team_games)} teams in {season}")
        return all_team_games

    @performance_monitor("store_team_season_aggregations")
    def _store_team_season_aggregations(
        self, aggregated_seasons: dict[str, dict], season: str
    ) -> None:
        """
        Store aggregated team season statistics.

        Args:
            aggregated_seasons: Dictionary mapping team_id to season stats
            season: Season being processed
        """
        logger.info(
            f"Storing team season aggregations for {len(aggregated_seasons)} teams "
            f"in season {season}"
        )

        if not aggregated_seasons:
            logger.warning("No team season aggregations to store")
            return

        # Convert aggregated seasons to DataFrame for Iceberg storage
        rows = []
        for team_id, stats in aggregated_seasons.items():
            row = stats.copy()
            row["team_id"] = team_id
            row["season"] = season
            rows.append(row)

        df = pd.DataFrame(rows)

        # Validate the aggregated data
        self.validator.validate_gold_analytics(df, "team")

        # Store using existing team analytics functionality
        # For season aggregations, we use a representative date (season start)
        season_year = int(season.split("-")[0])
        representative_date = date(season_year, 10, 1)

        # TODO: Replace with JSON artifact writing per ADR-028
        # S3 Tables functionality removed - need to write to served/ prefix
        # success = self.iceberg_writer.write_team_analytics(
        #     df, representative_date, season
        # )
        #
        # if not success:
        #     raise RuntimeError(f"Failed to store team season aggregations for {season}")

        logger.warning(
            "S3 Tables write functionality removed - "
            "need to implement JSON artifact writing per ADR-028"
        )
        logger.info(
            f"Would store team season aggregations for "
            f"{len(aggregated_seasons)} teams"
        )

    @performance_monitor("load_season_player_games")
    def _load_season_player_games(
        self, season: str, player_id: str | None = None, dry_run: bool = False
    ) -> dict[str, list[dict]]:
        """
        Load all player game statistics for a season.

        Args:
            season: Season to load data for
            player_id: Specific player to load, or None for all players
            dry_run: If True, return mock data

        Returns:
            Dictionary mapping player_id to list of game statistics
        """
        if dry_run:
            # Mock season data for testing
            mock_games = [
                {
                    "player_id": "player_1",
                    "player_name": "Mock Player 1",
                    "team": "Mock Team",
                    "points": 25,
                    "rebounds": 8,
                    "assists": 5,
                    "steals": 2,
                    "blocks": 1,
                    "turnovers": 3,
                    "field_goals_made": 10,
                    "field_goals_attempted": 18,
                    "three_pointers_made": 3,
                    "three_pointers_attempted": 8,
                    "free_throws_made": 2,
                    "free_throws_attempted": 3,
                    "minutes_played": 35.0,
                },
                {
                    "player_id": "player_1",
                    "player_name": "Mock Player 1",
                    "team": "Mock Team",
                    "points": 18,
                    "rebounds": 6,
                    "assists": 9,
                    "steals": 1,
                    "blocks": 0,
                    "turnovers": 4,
                    "field_goals_made": 7,
                    "field_goals_attempted": 15,
                    "three_pointers_made": 2,
                    "three_pointers_attempted": 6,
                    "free_throws_made": 2,
                    "free_throws_attempted": 2,
                    "minutes_played": 32.0,
                },
            ]

            if player_id:
                return {player_id: mock_games}
            else:
                return {"player_1": mock_games, "player_2": mock_games[:1]}

        logger.info(f"Loading season player games for {season}")

        # Use S3DataDiscovery to find all dates with player data for the season
        # This is a simplified implementation - in production would need more
        # sophisticated date discovery
        from datetime import date as date_class

        # Determine season date range (simplified)
        season_year = int(season.split("-")[0])
        start_date = date_class(season_year, 10, 1)  # October 1st
        end_date = date_class(season_year + 1, 6, 30)  # June 30th

        # Find available dates
        available_dates = self.s3_discovery.discover_dates_to_process(
            start_date, end_date, "player_stats"
        )

        if not available_dates:
            logger.warning(f"No player data found for season {season}")
            return {}

        # Load and aggregate all player games for the season
        all_player_games = {}

        with performance_context("season_player_games_loading") as ctx:
            for process_date in available_dates:
                try:
                    daily_data = self.s3_discovery.load_all_silver_data(
                        process_date, "player_stats"
                    )

                    if daily_data.empty:
                        continue

                    # Group by player_id and add to season data
                    for _, row in daily_data.iterrows():
                        pid = row.get("player_id")
                        if pid and (player_id is None or pid == player_id):
                            if pid not in all_player_games:
                                all_player_games[pid] = []

                            # Convert row to game dict
                            game_dict = row.to_dict()
                            game_dict["game_date"] = process_date.strftime("%Y-%m-%d")
                            all_player_games[pid].append(game_dict)

                    ctx["records_processed"] += len(daily_data)

                except Exception as e:
                    logger.warning(
                        f"Failed to load player data for {process_date}: {e}"
                    )
                    continue

        logger.info(
            f"Loaded season data for {len(all_player_games)} players in {season}"
        )
        return all_player_games

    @performance_monitor("store_season_aggregations")
    def _store_season_aggregations(
        self, aggregated_seasons: dict[str, dict], season: str
    ) -> None:
        """
        Store aggregated season statistics.

        Args:
            aggregated_seasons: Dictionary mapping player_id to season stats
            season: Season being processed
        """
        logger.info(
            f"Storing season aggregations for {len(aggregated_seasons)} players "
            f"in season {season}"
        )

        if not aggregated_seasons:
            logger.warning("No season aggregations to store")
            return

        # Convert aggregated seasons to DataFrame for Iceberg storage
        rows = []
        for player_id, stats in aggregated_seasons.items():
            row = stats.copy()
            row["player_id"] = player_id
            row["season"] = season
            rows.append(row)

        df = pd.DataFrame(rows)

        # Validate the aggregated data
        self.validator.validate_gold_analytics(df, "player")

        # Store using existing player analytics functionality
        # For season aggregations, we use a representative date (season start)
        season_year = int(season.split("-")[0])
        representative_date = date(season_year, 10, 1)

        # TODO: Replace with JSON artifact writing per ADR-028
        # S3 Tables functionality removed - need to write to served/ prefix
        # success = self.iceberg_writer.write_player_analytics(
        #     df, representative_date, season
        # )
        #
        # if not success:
        #     raise RuntimeError(f"Failed to store season aggregations for {season}")

        logger.warning(
            "S3 Tables write functionality removed - "
            "need to implement JSON artifact writing per ADR-028"
        )
        logger.info(
            f"Would store season aggregations for "
            f"{len(aggregated_seasons)} players"
        )

    @performance_monitor("process_date")
    def process_date(self, target_date: date, dry_run: bool = False) -> bool:
        """
        Process Silver layer data for a specific date into Gold analytics.

        Args:
            target_date: Date to process
            dry_run: If True, log operations without making changes

        Returns:
            True if processing succeeded, False otherwise
        """
        logger.info(f"Processing Gold analytics for date: {target_date}")

        if dry_run:
            logger.info("Dry run mode - no data will be modified")

        try:
            with performance_context("end_to_end_processing") as ctx:
                # Check data freshness before processing
                if not dry_run:
                    player_fresh = self.s3_discovery.check_data_freshness(
                        target_date, "player_stats"
                    )
                    team_fresh = self.s3_discovery.check_data_freshness(
                        target_date, "team_stats"
                    )

                    if not player_fresh and not team_fresh:
                        logger.warning(
                            f"No fresh data found for {target_date}, "
                            f"skipping processing"
                        )
                        return True

                # Load Silver data
                player_stats = self._load_silver_player_stats(target_date, dry_run)
                team_stats = self._load_silver_team_stats(target_date, dry_run)

                # Calculate advanced analytics using new functions
                player_analytics = self._calculate_player_analytics_enhanced(
                    player_stats
                )
                team_analytics = self._calculate_team_analytics(team_stats)

                # Validate analytics before storing
                if not player_analytics.empty:
                    self.validator.validate_gold_analytics(player_analytics, "player")
                    # Validate consistency between silver and gold
                    self.validator.validate_data_consistency(
                        player_stats, player_analytics, "player"
                    )

                if not team_analytics.empty:
                    self.validator.validate_gold_analytics(team_analytics, "team")
                    # Validate consistency between silver and gold
                    self.validator.validate_data_consistency(
                        team_stats, team_analytics, "team"
                    )

                # Store results
                if not dry_run:
                    if not player_analytics.empty:
                        self._store_player_analytics(player_analytics, target_date)
                    if not team_analytics.empty:
                        self._store_team_analytics(team_analytics, target_date)
                else:
                    logger.info(f"Would store {len(player_analytics)} player analytics")
                    logger.info(f"Would store {len(team_analytics)} team analytics")

                # Update context with total records processed
                ctx["records_processed"] = len(player_analytics) + len(team_analytics)

            logger.info(f"Successfully processed Gold analytics for {target_date}")
            return True

        except Exception as e:
            logger.error(f"Failed to process Gold analytics for {target_date}: {e}")
            return False

    @performance_monitor("load_silver_player_stats")
    def _load_silver_player_stats(
        self, target_date: date, dry_run: bool
    ) -> pd.DataFrame:
        """
        Load Silver layer player stats for the target date.

        Args:
            target_date: Date to load data for
            dry_run: If True, return mock data

        Returns:
            DataFrame with Silver layer player stats
        """
        if dry_run:
            # Mock data for testing
            return pd.DataFrame(
                {
                    "player_id": ["player_1", "player_2"],
                    "team_id": ["team_1", "team_2"],
                    "points": [25, 18],
                    "rebounds": [8, 6],
                    "assists": [5, 9],
                    "field_goals_made": [10, 7],
                    "field_goals_attempted": [18, 15],
                    "free_throws_made": [3, 2],
                    "free_throws_attempted": [4, 3],
                    "minutes_played": [35, 32],
                }
            )

        logger.info(f"Loading Silver player stats for {target_date}")

        # Use S3DataDiscovery to load actual data
        player_data = self.s3_discovery.load_all_silver_data(
            target_date, "player_stats"
        )

        if player_data.empty:
            logger.warning(f"No player stats found for {target_date}")
            return pd.DataFrame()

        # Validate the loaded data
        self.validator.validate_silver_player_data(player_data, target_date)

        logger.info(
            f"Successfully loaded {len(player_data)} player stat records "
            f"for {target_date}"
        )
        return player_data

    @performance_monitor("load_silver_team_stats")
    def _load_silver_team_stats(self, target_date: date, dry_run: bool) -> pd.DataFrame:
        """
        Load Silver layer team stats for the target date.

        Args:
            target_date: Date to load data for
            dry_run: If True, return mock data

        Returns:
            DataFrame with Silver layer team stats
        """
        if dry_run:
            # Mock data for testing
            return pd.DataFrame(
                {
                    "team_id": ["team_1", "team_2"],
                    "points": [110, 105],
                    "field_goals_made": [42, 40],
                    "field_goals_attempted": [85, 88],
                    "rebounds": [45, 42],
                    "turnovers": [12, 15],
                    "possessions": [98, 95],
                }
            )

        logger.info(f"Loading Silver team stats for {target_date}")

        # Use S3DataDiscovery to load actual data
        team_data = self.s3_discovery.load_all_silver_data(target_date, "team_stats")

        if team_data.empty:
            logger.warning(f"No team stats found for {target_date}")
            return pd.DataFrame()

        # Validate the loaded data
        self.validator.validate_silver_team_data(team_data, target_date)

        logger.info(
            f"Successfully loaded {len(team_data)} team stat records for {target_date}"
        )
        return team_data

    def _calculate_player_analytics_enhanced(
        self, player_stats: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate advanced player analytics metrics using the new transforms.

        Args:
            player_stats: Raw player statistics

        Returns:
            DataFrame with calculated analytics metrics
        """
        from hoopstat_data.transforms import (
            calculate_assists_per_turnover,
            calculate_effective_field_goal_percentage,
            calculate_efficiency_rating,
            calculate_offensive_rating,
            calculate_points_per_shot,
            calculate_true_shooting_percentage,
            calculate_usage_rate,
        )

        analytics = player_stats.copy()

        # Ensure required columns exist with defaults
        required_columns = {
            "player_id": "unknown",
            "team_id": 0,
            "points": 0,
            "rebounds": 0,
            "assists": 0,
            "field_goals_made": 0,
            "field_goals_attempted": 0,
            "three_pointers_made": 0,
            "three_pointers_attempted": 0,
            "free_throws_made": 0,
            "free_throws_attempted": 0,
            "turnovers": 0,
            "minutes_played": 1,
        }

        for col, default_val in required_columns.items():
            if col not in analytics.columns:
                analytics[col] = default_val

        # Apply vectorized calculations using the new functions
        for idx, row in analytics.iterrows():
            # True Shooting Percentage
            ts_pct = calculate_true_shooting_percentage(
                row.get("points", 0),
                row.get("field_goals_attempted", 0),
                row.get("free_throws_attempted", 0),
            )
            if ts_pct is not None:
                analytics.at[idx, "true_shooting_pct"] = ts_pct

            # Player Efficiency Rating
            row_dict = row.to_dict()
            per = calculate_efficiency_rating(row_dict)
            analytics.at[idx, "player_efficiency_rating"] = per

            # Points per shot
            pps = calculate_points_per_shot(
                row.get("points", 0),
                row.get("field_goals_attempted", 0),
                row.get("free_throws_attempted", 0),
            )
            if pps is not None:
                analytics.at[idx, "points_per_shot"] = pps

            # Assists per turnover
            apt = calculate_assists_per_turnover(
                row.get("assists", 0), row.get("turnovers", 0)
            )
            if apt is not None:
                analytics.at[idx, "assists_per_turnover"] = apt

            # Usage Rate (simplified approximation)
            usage_rate = calculate_usage_rate(
                row.get("field_goals_attempted", 0),
                row.get("free_throws_attempted", 0),
                row.get("turnovers", 0),
                row.get("minutes_played", 1),
                85,  # Estimated team FGA
                25,  # Estimated team FTA
                15,  # Estimated team TOV
                240,  # Team minutes (48 min * 5 players)
            )
            if usage_rate is not None:
                analytics.at[idx, "usage_rate"] = usage_rate

            # Effective Field Goal Percentage
            efg_pct = calculate_effective_field_goal_percentage(
                row.get("field_goals_made", 0),
                row.get("field_goals_attempted", 0),
                row.get("three_pointers_made", 0),
            )
            if efg_pct is not None:
                analytics.at[idx, "effective_field_goal_pct"] = efg_pct

            # Approximate defensive and offensive ratings for players
            # Note: These are simplified approximations
            possessions = max(
                row.get("field_goals_attempted", 0)
                + 0.44 * row.get("free_throws_attempted", 0)
                + row.get("turnovers", 0),
                1,
            )

            off_rating = calculate_offensive_rating(row.get("points", 0), possessions)
            if off_rating:
                analytics.at[idx, "offensive_rating"] = off_rating

            # Defensive rating is complex for players - use a simplified version
            analytics.at[idx, "defensive_rating"] = (
                110.0  # League average approximation
            )

        logger.info(f"Calculated enhanced analytics for {len(analytics)} players")
        return analytics

    def _calculate_team_analytics(self, team_stats: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate advanced team analytics metrics.

        Args:
            team_stats: Raw team statistics

        Returns:
            DataFrame with calculated analytics metrics
        """
        from hoopstat_data.transforms import (
            calculate_defensive_rating,
            calculate_effective_field_goal_percentage,
            calculate_free_throw_rate,
            calculate_offensive_rating,
            calculate_offensive_rebound_percentage,
            calculate_pace,
            calculate_possessions,
            calculate_true_shooting_percentage,
            calculate_turnover_percentage,
        )

        analytics = team_stats.copy()

        # Ensure required columns exist with defaults
        required_columns = {
            "team_id": 0,
            "opponent_team_id": 0,  # Required by schema
            "points": 0,
            "points_allowed": 0,
            "field_goals_made": 0,
            "field_goals_attempted": 0,
            "three_pointers_made": 0,
            "three_pointers_attempted": 0,
            "free_throws_made": 0,
            "free_throws_attempted": 0,
            "offensive_rebounds": 0,
            "defensive_rebounds": 0,
            "total_rebounds": 0,
            "turnovers": 0,
        }

        for col, default_val in required_columns.items():
            if col not in analytics.columns:
                analytics[col] = default_val

        for idx, row in analytics.iterrows():
            # Calculate possessions
            possessions = calculate_possessions(
                row.get("field_goals_attempted", 0),
                row.get("free_throws_attempted", 0),
                row.get("offensive_rebounds", 0),
                row.get("turnovers", 0),
            )

            if possessions:
                analytics.at[idx, "possessions"] = possessions

                # Offensive Rating: Points per 100 possessions
                off_rating = calculate_offensive_rating(
                    row.get("points", 0), possessions
                )
                if off_rating:
                    analytics.at[idx, "offensive_rating"] = off_rating

                # Defensive Rating (using points allowed)
                def_rating = calculate_defensive_rating(
                    row.get("points_allowed", 0), possessions
                )
                if def_rating:
                    analytics.at[idx, "defensive_rating"] = def_rating

                # Net Rating
                if off_rating and def_rating:
                    analytics.at[idx, "net_rating"] = round(off_rating - def_rating, 1)

                # Pace
                pace = calculate_pace(possessions)
                if pace:
                    analytics.at[idx, "pace"] = pace

                # Turnover Percentage
                tov_pct = calculate_turnover_percentage(
                    row.get("turnovers", 0), possessions
                )
                if tov_pct:
                    analytics.at[idx, "turnover_rate"] = tov_pct

            # Four Factors
            # Effective Field Goal Percentage
            efg_pct = calculate_effective_field_goal_percentage(
                row.get("field_goals_made", 0),
                row.get("field_goals_attempted", 0),
                row.get("three_pointers_made", 0),
            )
            if efg_pct:
                analytics.at[idx, "effective_field_goal_pct"] = efg_pct

            # Rebound Rate (using offensive rebound percentage as proxy)
            orb_pct = calculate_offensive_rebound_percentage(
                row.get("offensive_rebounds", 0),
                row.get("field_goals_attempted", 0),
                row.get("field_goals_made", 0),
            )
            if orb_pct:
                analytics.at[idx, "rebound_rate"] = orb_pct

            # Free Throw Rate
            ft_rate = calculate_free_throw_rate(
                row.get("free_throws_attempted", 0),
                row.get("field_goals_attempted", 0),
            )
            if ft_rate:
                analytics.at[idx, "free_throw_rate"] = ft_rate

            # True Shooting Percentage
            ts_pct = calculate_true_shooting_percentage(
                row.get("points", 0),
                row.get("field_goals_attempted", 0),
                row.get("free_throws_attempted", 0),
            )
            if ts_pct:
                analytics.at[idx, "true_shooting_pct"] = ts_pct

        logger.info(f"Calculated enhanced analytics for {len(analytics)} teams")
        return analytics

    def _store_player_analytics(
        self, analytics: pd.DataFrame, target_date: date
    ) -> None:
        """
        Store player analytics in S3 Tables using Apache Iceberg format.

        Args:
            analytics: Player analytics data
            target_date: Date being processed
        """
        if analytics.empty:
            logger.info("No player analytics data to store")
            return

        # Extract season from target_date (assume current NBA season logic)
        # NBA season spans Oct-June, so if month >= 10, it's the start of season
        if target_date.month >= 10:
            season = f"{target_date.year}-{str(target_date.year + 1)[2:]}"
        else:
            season = f"{target_date.year - 1}-{str(target_date.year)[2:]}"

        logger.info(
            f"Storing {len(analytics)} player analytics records for "
            f"date {target_date}, season {season}"
        )

        # TODO: Replace with JSON artifact writing per ADR-028
        # S3 Tables functionality removed - need to write to served/ prefix
        # Use Iceberg writer with proper error handling
        # success = self.iceberg_writer.write_player_analytics(
        #     analytics, target_date, season
        # )
        #
        # if not success:
        #     raise RuntimeError("Failed to store player analytics to S3 Tables")

        logger.warning(
            "S3 Tables write functionality removed - "
            "need to implement JSON artifact writing per ADR-028"
        )

    def _store_team_analytics(self, analytics: pd.DataFrame, target_date: date) -> None:
        """
        Store team analytics in S3 Tables using Apache Iceberg format.

        Args:
            analytics: Team analytics data
            target_date: Date being processed
        """
        if analytics.empty:
            logger.info("No team analytics data to store")
            return

        # Extract season from target_date (assume current NBA season logic)
        if target_date.month >= 10:
            season = f"{target_date.year}-{str(target_date.year + 1)[2:]}"
        else:
            season = f"{target_date.year - 1}-{str(target_date.year)[2:]}"

        logger.info(
            f"Storing {len(analytics)} team analytics records for date {target_date}, "
            f"season {season}"
        )

        # TODO: Replace with JSON artifact writing per ADR-028
        # S3 Tables functionality removed - need to write to served/ prefix
        # Use Iceberg writer with proper error handling
        # success = self.iceberg_writer.write_team_analytics(
        #     analytics, target_date, season
        # )
        #
        # if not success:
        #     raise RuntimeError("Failed to store team analytics to S3 Tables")

        logger.warning(
            "S3 Tables write functionality removed - "
            "need to implement JSON artifact writing per ADR-028"
        )

    def process_date_range(
        self,
        start_date: date,
        end_date: date,
        dry_run: bool = False,
        max_concurrent: int | None = None,
    ) -> dict[date, bool]:
        """
        Process Gold analytics for a range of dates with incremental processing.

        Args:
            start_date: Start date for processing
            end_date: End date for processing (inclusive)
            dry_run: If True, log operations without making changes
            max_concurrent: Maximum concurrent processing (uses config default if None)

        Returns:
            Dictionary mapping dates to processing success status
        """
        max_concurrent = max_concurrent or self.config.max_concurrent_files

        logger.info(f"Processing Gold analytics from {start_date} to {end_date}")

        # Discover which dates have available data
        available_dates = self.s3_discovery.discover_dates_to_process(
            start_date, end_date, "player_stats"
        )

        if not available_dates:
            logger.warning(f"No data found between {start_date} and {end_date}")
            return {}

        # Process dates with performance tracking
        results = {}

        with performance_context("date_range_processing") as ctx:
            for target_date in available_dates:
                try:
                    success = self.process_date(target_date, dry_run)
                    results[target_date] = success

                    if success:
                        ctx["records_processed"] += 1

                except Exception as e:
                    logger.error(f"Failed to process {target_date}: {e}")
                    results[target_date] = False

        successful_dates = sum(1 for success in results.values() if success)
        logger.info(
            f"Completed date range processing: "
            f"{successful_dates}/{len(results)} dates successful"
        )

        return results

    def discover_new_data(self, lookback_days: int = 7) -> list[date]:
        """
        Discover new Silver layer data that needs processing.

        Args:
            lookback_days: Number of days to look back for new data

        Returns:
            List of dates with new data available for processing
        """
        from datetime import timedelta

        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        logger.info(f"Discovering new data from {start_date} to {end_date}")

        # Find dates with available Silver layer data
        player_dates = self.s3_discovery.discover_dates_to_process(
            start_date, end_date, "player_stats"
        )
        team_dates = self.s3_discovery.discover_dates_to_process(
            start_date, end_date, "team_stats"
        )

        # Combine and deduplicate
        all_dates = sorted(set(player_dates + team_dates))

        # Filter for fresh data only
        fresh_dates = []
        for check_date in all_dates:
            if self.s3_discovery.check_data_freshness(
                check_date, "player_stats"
            ) or self.s3_discovery.check_data_freshness(check_date, "team_stats"):
                fresh_dates.append(check_date)

        logger.info(f"Found {len(fresh_dates)} dates with fresh data")
        return fresh_dates

    def process_incremental(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Process incremental updates from Silver layer data.

        Args:
            dry_run: If True, log operations without making changes

        Returns:
            Dictionary with processing summary and results
        """
        logger.info("Starting incremental Gold analytics processing")

        # Discover new data to process
        new_dates = self.discover_new_data()

        if not new_dates:
            logger.info("No new data found for incremental processing")
            return {
                "status": "success",
                "message": "No new data to process",
                "dates_processed": [],
                "records_processed": 0,
            }

        # Process new dates
        results = {}
        total_records = 0

        with performance_context("incremental_processing") as ctx:
            for target_date in new_dates:
                try:
                    success = self.process_date(target_date, dry_run)
                    results[target_date] = success

                    if success:
                        # Estimate records processed (would be tracked by
                        # performance monitoring)
                        total_records += (
                            100  # Placeholder - actual count would come from context
                        )

                except Exception as e:
                    logger.error(
                        f"Incremental processing failed for {target_date}: {e}"
                    )
                    results[target_date] = False

            ctx["records_processed"] = total_records

        successful_dates = [d for d, success in results.items() if success]
        failed_dates = [d for d, success in results.items() if not success]

        summary = {
            "status": "success" if not failed_dates else "partial",
            "message": (
                f"Processed {len(successful_dates)}/{len(new_dates)} dates successfully"
            ),
            "dates_processed": successful_dates,
            "dates_failed": failed_dates,
            "records_processed": total_records,
        }

        logger.info(f"Incremental processing completed: {summary['message']}")
        return summary
