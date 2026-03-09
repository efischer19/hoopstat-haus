"""MCP server exposing Hoopstat Haus NBA statistics as tools."""

import os

from mcp.server.fastmcp import FastMCP

from app.http_client import ArtifactFetchError, HoopstatClient

DEFAULT_BASE_URL = "https://data.hoopstat.haus"

mcp = FastMCP("hoopstat-haus")


def _get_client() -> HoopstatClient:
    """Create an HTTP client using the configured base URL."""
    base_url = os.environ.get("HOOPSTAT_BASE_URL", DEFAULT_BASE_URL)
    return HoopstatClient(base_url)


@mcp.tool()
async def get_index() -> str:
    """Fetch the latest Hoopstat Haus data index.

    Returns the latest.json index document which lists all available
    datasets including player daily stats, team daily stats, and top
    performer lists along with the most recent data date.
    """
    client = _get_client()
    try:
        return await client.fetch_index()
    except ArtifactFetchError as exc:
        return f"Error: {exc}"


@mcp.tool()
async def get_artifact(resource_uri: str) -> str:
    """Fetch a specific NBA statistics artifact by its resource URI.

    Retrieves a JSON artifact from the Hoopstat Haus data store.
    The resource_uri should follow the path structure used by the index,
    for example:
      - "player_daily/2024-11-15/2544" for LeBron James' stats on that date
      - "team_daily/2024-11-15/1610612747" for the Lakers' team stats
      - "top_lists/2024-11-15/points" for the top scorers list

    Args:
        resource_uri: Path to the artifact (e.g. "player_daily/2024-11-15/2544").
            The .json extension is added automatically if not present.
    """
    client = _get_client()
    try:
        return await client.fetch_artifact(resource_uri)
    except ArtifactFetchError as exc:
        return f"Error: {exc}"
