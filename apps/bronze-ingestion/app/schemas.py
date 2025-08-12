"""
JSON schemas for NBA API response validation.

These schemas define the expected structure of NBA API responses
to ensure data quality and consistency.
"""

# NBA API schedule response schema - based on LeagueGameFinder response
NBA_SCHEDULE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["GAME_ID", "GAME_DATE", "TEAM_ID"],
        "properties": {
            "GAME_ID": {"type": "string", "pattern": r"^\d{10}$"},
            "GAME_DATE": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
            "TEAM_ID": {"type": "integer", "minimum": 1},
            "SEASON_ID": {"type": "string"},
            "TEAM_ABBREVIATION": {"type": "string", "minLength": 2, "maxLength": 3},
            "TEAM_NAME": {"type": "string", "minLength": 1},
            "MATCHUP": {"type": "string"},
            "WL": {"type": ["string", "null"], "enum": ["W", "L", None]},
            "MIN": {"type": ["integer", "null"], "minimum": 0},
            "FGM": {"type": ["integer", "null"], "minimum": 0},
            "FGA": {"type": ["integer", "null"], "minimum": 0},
            "FG_PCT": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
            "FG3M": {"type": ["integer", "null"], "minimum": 0},
            "FG3A": {"type": ["integer", "null"], "minimum": 0},
            "FG3_PCT": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
            "FTM": {"type": ["integer", "null"], "minimum": 0},
            "FTA": {"type": ["integer", "null"], "minimum": 0},
            "FT_PCT": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
            "OREB": {"type": ["integer", "null"], "minimum": 0},
            "DREB": {"type": ["integer", "null"], "minimum": 0},
            "REB": {"type": ["integer", "null"], "minimum": 0},
            "AST": {"type": ["integer", "null"], "minimum": 0},
            "STL": {"type": ["integer", "null"], "minimum": 0},
            "BLK": {"type": ["integer", "null"], "minimum": 0},
            "TOV": {"type": ["integer", "null"], "minimum": 0},
            "PF": {"type": ["integer", "null"], "minimum": 0},
            "PTS": {"type": ["integer", "null"], "minimum": 0},
            "PLUS_MINUS": {"type": ["integer", "null"]},
        },
        "additionalProperties": True,  # Allow additional fields for flexibility
    },
}

# NBA API box score response schema - based on BoxScoreTraditionalV3 response
NBA_BOX_SCORE_SCHEMA = {
    "type": "object",
    "required": ["resultSets"],
    "properties": {
        "resultSets": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["name", "headers", "rowSet"],
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "headers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                    "rowSet": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {
                                "type": ["string", "number", "null"],
                            },
                        },
                    },
                },
                "additionalProperties": True,
            },
        },
        "parameters": {
            "type": "object",
            "properties": {
                "GameID": {"type": "string", "pattern": r"^\d{10}$"},
            },
            "additionalProperties": True,
        },
    },
    "additionalProperties": True,
}

# Base schema for any NBA API response with common metadata
NBA_API_BASE_SCHEMA = {
    "type": "object",
    "properties": {
        "resource": {"type": "string"},
        "parameters": {"type": "object"},
        "resultSets": {"type": "array"},
    },
}


def get_schema(response_type: str) -> dict:
    """
    Get the appropriate schema for a given NBA API response type.

    Args:
        response_type: Type of response ('schedule', 'box_score', 'base')

    Returns:
        JSON schema dictionary

    Raises:
        ValueError: If response_type is not supported
    """
    schemas = {
        "schedule": NBA_SCHEDULE_SCHEMA,
        "box_score": NBA_BOX_SCORE_SCHEMA,
        "base": NBA_API_BASE_SCHEMA,
    }

    if response_type not in schemas:
        raise ValueError(f"Unsupported response type: {response_type}")

    return schemas[response_type]
