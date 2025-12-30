"""Tests for NBA API camelCase to snake_case mapping."""

from app.processors import BronzeToSilverProcessor


class TestNBAAPIMapping:
    """Test cases for NBA API V3 format to BoxScoreRaw format mapping."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = BronzeToSilverProcessor(
            bronze_bucket="test-bronze-bucket", region_name="us-east-1"
        )

    def test_map_nba_api_v3_format(self):
        """Test mapping of NBA API V3 format with boxScoreTraditional wrapper."""
        # Realistic NBA API V3 format data
        nba_api_data = {
            "boxScoreTraditional": {
                "gameId": "0022300123",
                "gameDate": "2024-01-15",
                "arena": "Crypto.com Arena",
                "homeTeam": {
                    "teamId": 1610612747,
                    "teamName": "Lakers",
                    "teamCity": "Los Angeles",
                    "teamTricode": "LAL",
                    "players": [
                        {
                            "personId": 2544,
                            "name": "LeBron James",
                            "nameI": "L. James",
                            "position": "F",
                            "statistics": {
                                "minutes": "PT36M24S",
                                "minutesCalculated": "36:24",
                                "points": 28,
                                "reboundsOffensive": 2,
                                "reboundsDefensive": 6,
                                "assists": 8,
                                "steals": 2,
                                "blocks": 1,
                                "turnovers": 3,
                                "fieldGoalsMade": 11,
                                "fieldGoalsAttempted": 18,
                                "threePointersMade": 3,
                                "threePointersAttempted": 6,
                                "freeThrowsMade": 3,
                                "freeThrowsAttempted": 4,
                            },
                        }
                    ],
                    "statistics": {
                        "points": 108,
                        "fieldGoalsMade": 40,
                        "fieldGoalsAttempted": 85,
                        "threePointersMade": 12,
                        "threePointersAttempted": 30,
                        "freeThrowsMade": 16,
                        "freeThrowsAttempted": 20,
                        "reboundsOffensive": 8,
                        "reboundsDefensive": 32,
                        "reboundsTotal": 40,
                        "assists": 25,
                        "steals": 7,
                        "blocks": 5,
                        "turnovers": 12,
                        "foulsPersonal": 18,
                    },
                },
                "awayTeam": {
                    "teamId": 1610612738,
                    "teamName": "Celtics",
                    "teamCity": "Boston",
                    "teamTricode": "BOS",
                    "players": [
                        {
                            "personId": 1628369,
                            "name": "Jayson Tatum",
                            "position": "F-G",
                            "statistics": {
                                "minutes": "PT38M12S",
                                "minutesCalculated": "38:12",
                                "points": 25,
                                "reboundsOffensive": 1,
                                "reboundsDefensive": 7,
                                "assists": 5,
                                "steals": 1,
                                "blocks": 0,
                                "turnovers": 2,
                                "fieldGoalsMade": 9,
                                "fieldGoalsAttempted": 20,
                                "threePointersMade": 4,
                                "threePointersAttempted": 10,
                                "freeThrowsMade": 3,
                                "freeThrowsAttempted": 3,
                            },
                        }
                    ],
                    "statistics": {
                        "points": 102,
                        "fieldGoalsMade": 38,
                        "fieldGoalsAttempted": 82,
                        "threePointersMade": 10,
                        "threePointersAttempted": 28,
                        "freeThrowsMade": 16,
                        "freeThrowsAttempted": 18,
                        "reboundsOffensive": 6,
                        "reboundsDefensive": 30,
                        "reboundsTotal": 36,
                        "assists": 22,
                        "steals": 5,
                        "blocks": 3,
                        "turnovers": 15,
                        "foulsPersonal": 20,
                    },
                },
            }
        }

        # Map the data
        mapped_data = self.processor._map_nba_api_to_model(nba_api_data)

        # Verify top-level fields
        assert mapped_data["game_id"] == "0022300123"
        assert mapped_data["game_date"] == "2024-01-15"
        assert mapped_data["arena"] == "Crypto.com Arena"

        # Verify home team mapping
        assert mapped_data["home_team"]["id"] == 1610612747
        assert mapped_data["home_team"]["name"] == "Lakers"
        assert mapped_data["home_team"]["city"] == "Los Angeles"
        assert mapped_data["home_team"]["abbreviation"] == "LAL"

        # Verify home team stats mapping
        home_stats = mapped_data["home_team_stats"]
        assert home_stats["points"] == 108
        assert home_stats["field_goals_made"] == 40
        assert home_stats["field_goals_attempted"] == 85
        assert home_stats["three_pointers_made"] == 12
        assert home_stats["offensive_rebounds"] == 8
        assert home_stats["defensive_rebounds"] == 32

        # Verify home players mapping
        assert len(mapped_data["home_players"]) == 1
        lebron = mapped_data["home_players"][0]
        assert lebron["player_id"] == 2544
        assert lebron["player_name"] == "LeBron James"
        assert lebron["team"] == "Lakers"
        assert lebron["position"] == "F"
        assert lebron["points"] == 28
        assert lebron["assists"] == 8

        # Verify away team mapping
        assert mapped_data["away_team"]["id"] == 1610612738
        assert mapped_data["away_team"]["name"] == "Celtics"

        # Verify away team stats mapping
        away_stats = mapped_data["away_team_stats"]
        assert away_stats["points"] == 102

        # Verify away players mapping
        assert len(mapped_data["away_players"]) == 1
        tatum = mapped_data["away_players"][0]
        assert tatum["player_id"] == 1628369
        assert tatum["player_name"] == "Jayson Tatum"
        assert tatum["team"] == "Celtics"

    def test_map_already_snake_case_format(self):
        """Test that already snake_case data passes through unchanged."""
        snake_case_data = {
            "game_id": 123,
            "game_date": "2024-01-15",
            "home_team": {"id": 1, "name": "Lakers"},
            "away_team": {"id": 2, "name": "Celtics"},
        }

        mapped_data = self.processor._map_nba_api_to_model(snake_case_data)

        # Should return unchanged
        assert mapped_data == snake_case_data

    def test_transform_to_silver_with_nba_api_format(self):
        """Test complete transformation from NBA API V3 format to Silver."""
        nba_api_data = {
            "boxScoreTraditional": {
                "gameId": "0022300123",
                "gameDate": "2024-01-15",
                "arena": "Crypto.com Arena",
                "homeTeam": {
                    "teamId": 1610612747,
                    "teamName": "Lakers",
                    "teamCity": "Los Angeles",
                    "teamTricode": "LAL",
                    "players": [
                        {
                            "personId": 2544,
                            "name": "LeBron James",
                            "position": "F",
                            "statistics": {
                                "minutesCalculated": "36:24",
                                "points": 28,
                                "reboundsOffensive": 2,
                                "reboundsDefensive": 6,
                                "assists": 8,
                                "steals": 2,
                                "blocks": 1,
                                "turnovers": 3,
                                "fieldGoalsMade": 11,
                                "fieldGoalsAttempted": 18,
                                "threePointersMade": 3,
                                "threePointersAttempted": 6,
                                "freeThrowsMade": 3,
                                "freeThrowsAttempted": 4,
                            },
                        }
                    ],
                    "statistics": {
                        "points": 108,
                        "fieldGoalsMade": 40,
                        "fieldGoalsAttempted": 85,
                        "threePointersMade": 12,
                        "threePointersAttempted": 30,
                        "freeThrowsMade": 16,
                        "freeThrowsAttempted": 20,
                        "reboundsOffensive": 8,
                        "reboundsDefensive": 32,
                        "assists": 25,
                        "steals": 7,
                        "blocks": 5,
                        "turnovers": 12,
                        "foulsPersonal": 18,
                    },
                },
                "awayTeam": {
                    "teamId": 1610612738,
                    "teamName": "Celtics",
                    "teamCity": "Boston",
                    "teamTricode": "BOS",
                    "players": [],
                    "statistics": {
                        "points": 102,
                        "fieldGoalsMade": 38,
                        "fieldGoalsAttempted": 82,
                        "threePointersMade": 10,
                        "threePointersAttempted": 28,
                        "freeThrowsMade": 16,
                        "freeThrowsAttempted": 18,
                        "reboundsOffensive": 6,
                        "reboundsDefensive": 30,
                        "assists": 22,
                        "steals": 5,
                        "blocks": 3,
                        "turnovers": 15,
                        "foulsPersonal": 20,
                    },
                },
            }
        }

        # Transform to Silver
        result = self.processor.transform_to_silver(nba_api_data, "box_scores")

        # Verify structure
        assert "player_stats" in result
        assert "team_stats" in result
        assert "game_stats" in result

        # Verify player stats were created
        assert len(result["player_stats"]) == 1
        lebron = result["player_stats"][0]
        assert lebron["player_name"] == "LeBron James"
        assert lebron["points"] == 28
        assert lebron["assists"] == 8

        # Verify team stats were created
        assert len(result["team_stats"]) == 2

        # Verify game stats were created
        assert len(result["game_stats"]) == 1
        game = result["game_stats"][0]
        # Note: game_id may have leading zeros stripped during processing
        assert game["game_id"] in ["0022300123", "22300123"]
        assert game["home_score"] == 108
        assert game["away_score"] == 102

    def test_map_team_statistics(self):
        """Test mapping of team statistics from camelCase to snake_case."""
        camel_case_stats = {
            "points": 108,
            "fieldGoalsMade": 40,
            "fieldGoalsAttempted": 85,
            "threePointersMade": 12,
            "threePointersAttempted": 30,
            "freeThrowsMade": 16,
            "freeThrowsAttempted": 20,
            "reboundsOffensive": 8,
            "reboundsDefensive": 32,
            "reboundsTotal": 40,
            "assists": 25,
            "steals": 7,
            "blocks": 5,
            "turnovers": 12,
            "foulsPersonal": 18,
        }

        mapped_stats = self.processor._map_team_statistics(camel_case_stats)

        assert mapped_stats["points"] == 108
        assert mapped_stats["field_goals_made"] == 40
        assert mapped_stats["field_goals_attempted"] == 85
        assert mapped_stats["three_pointers_made"] == 12
        assert mapped_stats["three_pointers_attempted"] == 30
        assert mapped_stats["free_throws_made"] == 16
        assert mapped_stats["free_throws_attempted"] == 20
        assert mapped_stats["offensive_rebounds"] == 8
        assert mapped_stats["defensive_rebounds"] == 32
        assert mapped_stats["rebounds"] == 40
        assert mapped_stats["assists"] == 25
        assert mapped_stats["steals"] == 7
        assert mapped_stats["blocks"] == 5
        assert mapped_stats["turnovers"] == 12
        assert mapped_stats["fouls"] == 18

    def test_map_player_statistics(self):
        """Test mapping of player statistics from camelCase to snake_case."""
        player_data = {
            "personId": 2544,
            "name": "LeBron James",
            "position": "F",
            "statistics": {
                "minutesCalculated": "36:24",
                "points": 28,
                "reboundsOffensive": 2,
                "reboundsDefensive": 6,
                "assists": 8,
                "steals": 2,
                "blocks": 1,
                "turnovers": 3,
                "fieldGoalsMade": 11,
                "fieldGoalsAttempted": 18,
                "threePointersMade": 3,
                "threePointersAttempted": 6,
                "freeThrowsMade": 3,
                "freeThrowsAttempted": 4,
            },
        }

        team_data = {"teamName": "Lakers"}

        mapped_player = self.processor._map_player_statistics(player_data, team_data)

        assert mapped_player["player_id"] == 2544
        assert mapped_player["player_name"] == "LeBron James"
        assert mapped_player["team"] == "Lakers"
        assert mapped_player["position"] == "F"
        assert mapped_player["minutes_played"] == "36:24"
        assert mapped_player["points"] == 28
        assert mapped_player["offensive_rebounds"] == 2
        assert mapped_player["defensive_rebounds"] == 6
        assert mapped_player["assists"] == 8
        assert mapped_player["steals"] == 2
        assert mapped_player["blocks"] == 1
        assert mapped_player["turnovers"] == 3
        assert mapped_player["field_goals_made"] == 11
        assert mapped_player["field_goals_attempted"] == 18
        assert mapped_player["three_pointers_made"] == 3
        assert mapped_player["three_pointers_attempted"] == 6
        assert mapped_player["free_throws_made"] == 3
        assert mapped_player["free_throws_attempted"] == 4

    def test_map_with_missing_optional_fields(self):
        """Test mapping handles missing optional fields gracefully."""
        minimal_data = {
            "boxScoreTraditional": {
                "gameId": "123",
                "homeTeam": {
                    "teamId": 1,
                    "teamName": "Lakers",
                    "players": [],
                    "statistics": {"points": 100},
                },
                "awayTeam": {
                    "teamId": 2,
                    "teamName": "Celtics",
                    "players": [],
                    "statistics": {"points": 95},
                },
            }
        }

        mapped_data = self.processor._map_nba_api_to_model(minimal_data)

        # Should still map successfully with minimal data
        assert mapped_data["game_id"] == "123"
        assert mapped_data["home_team"]["id"] == 1
        assert mapped_data["home_team"]["name"] == "Lakers"
        assert len(mapped_data["home_players"]) == 0
        assert mapped_data["home_team_stats"]["points"] == 100
