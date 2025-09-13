"""
Gold layer analytics processors for NBA statistics.

This module provides processors for transforming Silver layer data into
advanced analytics metrics and player season aggregations.
"""

from datetime import date

import pandas as pd
from hoopstat_data.transforms import PlayerSeasonAggregator, TeamSeasonAggregator
from hoopstat_observability import get_logger

from .iceberg_integration import IcebergS3TablesWriter

logger = get_logger(__name__)


class GoldProcessor:
    """
    Processor for Gold layer analytics calculations and season aggregations.

    Transforms Silver layer NBA data into advanced analytics metrics
    and season summaries with comprehensive statistical calculations.
    """

    def __init__(self, silver_bucket: str, gold_bucket: str) -> None:
        """
        Initialize the Gold processor.

        Args:
            silver_bucket: S3 bucket containing Silver layer data
            gold_bucket: S3 bucket for Gold layer data storage
        """
        self.silver_bucket = silver_bucket
        self.gold_bucket = gold_bucket
        self.season_aggregator = PlayerSeasonAggregator(validation_mode="lenient")
        self.team_aggregator = TeamSeasonAggregator(validation_mode="lenient")
        
        # Initialize Iceberg writer for S3 Tables
        self.iceberg_writer = IcebergS3TablesWriter(gold_bucket)
        
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

        # TODO: Implement actual S3 data loading
        logger.info(f"Loading season team games for {season}")
        raise NotImplementedError("Season team game loading not yet implemented")

    def _store_team_season_aggregations(
        self, aggregated_seasons: dict[str, dict], season: str
    ) -> None:
        """
        Store aggregated team season statistics.

        Args:
            aggregated_seasons: Dictionary mapping team_id to season stats
            season: Season being processed
        """
        # TODO: Implement actual storage
        logger.info(
            f"Storing team season aggregations for {len(aggregated_seasons)} teams "
            f"in season {season}"
        )
        # Placeholder for actual storage implementation

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

        # TODO: Implement actual S3 data loading
        logger.info(f"Loading season player games for {season}")
        raise NotImplementedError("Season player game loading not yet implemented")

    def _store_season_aggregations(
        self, aggregated_seasons: dict[str, dict], season: str
    ) -> None:
        """
        Store aggregated season statistics.

        Args:
            aggregated_seasons: Dictionary mapping player_id to season stats
            season: Season being processed
        """
        # TODO: Implement actual storage
        logger.info(
            f"Storing season aggregations for {len(aggregated_seasons)} players "
            f"in season {season}"
        )
        # Placeholder for actual storage implementation

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
            # Load Silver data
            player_stats = self._load_silver_player_stats(target_date, dry_run)
            team_stats = self._load_silver_team_stats(target_date, dry_run)

            # Calculate advanced analytics using new functions
            player_analytics = self._calculate_player_analytics_enhanced(player_stats)
            team_analytics = self._calculate_team_analytics(team_stats)

            # Store results
            if not dry_run:
                self._store_player_analytics(player_analytics, target_date)
                self._store_team_analytics(team_analytics, target_date)
            else:
                logger.info(f"Would store {len(player_analytics)} player analytics")
                logger.info(f"Would store {len(team_analytics)} team analytics")

            logger.info(f"Successfully processed Gold analytics for {target_date}")
            return True

        except Exception as e:
            logger.error(f"Failed to process Gold analytics for {target_date}: {e}")
            return False

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

        # TODO: Implement actual S3 data loading
        logger.info(f"Loading Silver player stats for {target_date}")
        raise NotImplementedError("Silver data loading not yet implemented")

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

        # TODO: Implement actual S3 data loading
        logger.info(f"Loading Silver team stats for {target_date}")
        raise NotImplementedError("Silver data loading not yet implemented")

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
            calculate_efficiency_rating,
            calculate_points_per_shot,
            calculate_true_shooting_percentage,
            calculate_usage_rate,
            calculate_effective_field_goal_percentage,
            calculate_defensive_rating,
            calculate_offensive_rating,
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
            possessions = max(row.get("field_goals_attempted", 0) + 
                            0.44 * row.get("free_throws_attempted", 0) + 
                            row.get("turnovers", 0), 1)
            
            off_rating = calculate_offensive_rating(row.get("points", 0), possessions)
            if off_rating:
                analytics.at[idx, "offensive_rating"] = off_rating
            
            # Defensive rating is complex for players - use a simplified version
            analytics.at[idx, "defensive_rating"] = 110.0  # League average approximation

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
            f"Storing {len(analytics)} player analytics records for date {target_date}, "
            f"season {season}"
        )
        
        # Use Iceberg writer with proper error handling
        success = self.iceberg_writer.write_player_analytics(
            analytics, target_date, season
        )
        
        if not success:
            raise RuntimeError("Failed to store player analytics to S3 Tables")

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
        
        # Use Iceberg writer with proper error handling
        success = self.iceberg_writer.write_team_analytics(
            analytics, target_date, season
        )
        
        if not success:
            raise RuntimeError("Failed to store team analytics to S3 Tables")
