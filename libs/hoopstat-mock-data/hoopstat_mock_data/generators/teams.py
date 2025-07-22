"""Team generator for creating NBA team data."""

from ..models import Conference, Division, Team


class TeamGenerator:
    """Generator for NBA teams."""

    # Real NBA teams data
    NBA_TEAMS = [
        # Eastern Conference - Atlantic Division
        {
            "name": "Celtics",
            "city": "Boston",
            "abbr": "BOS",
            "conf": Conference.EASTERN,
            "div": Division.ATLANTIC,
        },
        {
            "name": "Nets",
            "city": "Brooklyn",
            "abbr": "BKN",
            "conf": Conference.EASTERN,
            "div": Division.ATLANTIC,
        },
        {
            "name": "Knicks",
            "city": "New York",
            "abbr": "NYK",
            "conf": Conference.EASTERN,
            "div": Division.ATLANTIC,
        },
        {
            "name": "76ers",
            "city": "Philadelphia",
            "abbr": "PHI",
            "conf": Conference.EASTERN,
            "div": Division.ATLANTIC,
        },
        {
            "name": "Raptors",
            "city": "Toronto",
            "abbr": "TOR",
            "conf": Conference.EASTERN,
            "div": Division.ATLANTIC,
        },
        # Eastern Conference - Central Division
        {
            "name": "Bulls",
            "city": "Chicago",
            "abbr": "CHI",
            "conf": Conference.EASTERN,
            "div": Division.CENTRAL,
        },
        {
            "name": "Cavaliers",
            "city": "Cleveland",
            "abbr": "CLE",
            "conf": Conference.EASTERN,
            "div": Division.CENTRAL,
        },
        {
            "name": "Pistons",
            "city": "Detroit",
            "abbr": "DET",
            "conf": Conference.EASTERN,
            "div": Division.CENTRAL,
        },
        {
            "name": "Pacers",
            "city": "Indiana",
            "abbr": "IND",
            "conf": Conference.EASTERN,
            "div": Division.CENTRAL,
        },
        {
            "name": "Bucks",
            "city": "Milwaukee",
            "abbr": "MIL",
            "conf": Conference.EASTERN,
            "div": Division.CENTRAL,
        },
        # Eastern Conference - Southeast Division
        {
            "name": "Hawks",
            "city": "Atlanta",
            "abbr": "ATL",
            "conf": Conference.EASTERN,
            "div": Division.SOUTHEAST,
        },
        {
            "name": "Hornets",
            "city": "Charlotte",
            "abbr": "CHA",
            "conf": Conference.EASTERN,
            "div": Division.SOUTHEAST,
        },
        {
            "name": "Heat",
            "city": "Miami",
            "abbr": "MIA",
            "conf": Conference.EASTERN,
            "div": Division.SOUTHEAST,
        },
        {
            "name": "Magic",
            "city": "Orlando",
            "abbr": "ORL",
            "conf": Conference.EASTERN,
            "div": Division.SOUTHEAST,
        },
        {
            "name": "Wizards",
            "city": "Washington",
            "abbr": "WAS",
            "conf": Conference.EASTERN,
            "div": Division.SOUTHEAST,
        },
        # Western Conference - Northwest Division
        {
            "name": "Nuggets",
            "city": "Denver",
            "abbr": "DEN",
            "conf": Conference.WESTERN,
            "div": Division.NORTHWEST,
        },
        {
            "name": "Timberwolves",
            "city": "Minnesota",
            "abbr": "MIN",
            "conf": Conference.WESTERN,
            "div": Division.NORTHWEST,
        },
        {
            "name": "Thunder",
            "city": "Oklahoma City",
            "abbr": "OKC",
            "conf": Conference.WESTERN,
            "div": Division.NORTHWEST,
        },
        {
            "name": "Trail Blazers",
            "city": "Portland",
            "abbr": "POR",
            "conf": Conference.WESTERN,
            "div": Division.NORTHWEST,
        },
        {
            "name": "Jazz",
            "city": "Utah",
            "abbr": "UTA",
            "conf": Conference.WESTERN,
            "div": Division.NORTHWEST,
        },
        # Western Conference - Pacific Division
        {
            "name": "Warriors",
            "city": "Golden State",
            "abbr": "GSW",
            "conf": Conference.WESTERN,
            "div": Division.PACIFIC,
        },
        {
            "name": "Clippers",
            "city": "Los Angeles",
            "abbr": "LAC",
            "conf": Conference.WESTERN,
            "div": Division.PACIFIC,
        },
        {
            "name": "Lakers",
            "city": "Los Angeles",
            "abbr": "LAL",
            "conf": Conference.WESTERN,
            "div": Division.PACIFIC,
        },
        {
            "name": "Suns",
            "city": "Phoenix",
            "abbr": "PHX",
            "conf": Conference.WESTERN,
            "div": Division.PACIFIC,
        },
        {
            "name": "Kings",
            "city": "Sacramento",
            "abbr": "SAC",
            "conf": Conference.WESTERN,
            "div": Division.PACIFIC,
        },
        # Western Conference - Southwest Division
        {
            "name": "Mavericks",
            "city": "Dallas",
            "abbr": "DAL",
            "conf": Conference.WESTERN,
            "div": Division.SOUTHWEST,
        },
        {
            "name": "Rockets",
            "city": "Houston",
            "abbr": "HOU",
            "conf": Conference.WESTERN,
            "div": Division.SOUTHWEST,
        },
        {
            "name": "Grizzlies",
            "city": "Memphis",
            "abbr": "MEM",
            "conf": Conference.WESTERN,
            "div": Division.SOUTHWEST,
        },
        {
            "name": "Pelicans",
            "city": "New Orleans",
            "abbr": "NOP",
            "conf": Conference.WESTERN,
            "div": Division.SOUTHWEST,
        },
        {
            "name": "Spurs",
            "city": "San Antonio",
            "abbr": "SAS",
            "conf": Conference.WESTERN,
            "div": Division.SOUTHWEST,
        },
    ]

    @classmethod
    def generate_teams(cls, count: int = 30) -> list[Team]:
        """
        Generate NBA teams.

        Args:
            count: Number of teams to generate (max 30 for real NBA teams)

        Returns:
            List of Team models
        """
        if count > 30:
            raise ValueError("Cannot generate more than 30 NBA teams (the real number)")

        teams = []
        for i, team_data in enumerate(cls.NBA_TEAMS[:count]):
            team = Team(
                id=i + 1,
                name=team_data["name"],
                city=team_data["city"],
                full_name=f"{team_data['city']} {team_data['name']}",
                abbreviation=team_data["abbr"],
                conference=team_data["conf"],
                division=team_data["div"],
            )
            teams.append(team)

        return teams

    @classmethod
    def get_team_by_id(cls, team_id: int) -> Team:
        """Get a specific team by ID."""
        teams = cls.generate_teams()
        for team in teams:
            if team.id == team_id:
                return team
        raise ValueError(f"Team with ID {team_id} not found")

    @classmethod
    def get_teams_by_conference(cls, conference: Conference) -> list[Team]:
        """Get all teams in a specific conference."""
        teams = cls.generate_teams()
        return [team for team in teams if team.conference == conference]

    @classmethod
    def get_teams_by_division(cls, division: Division) -> list[Team]:
        """Get all teams in a specific division."""
        teams = cls.generate_teams()
        return [team for team in teams if team.division == division]
