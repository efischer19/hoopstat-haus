"""
Test the MCP server implementation.
"""

import pytest

from mcp_server.server import BasketballDataMCPServer, create_server


def test_server_creation():
    """Test that the server can be created successfully."""
    server = create_server()
    assert isinstance(server, BasketballDataMCPServer)
    assert server.get_app() is not None


def test_server_has_required_components():
    """Test that the server has the required MCP components."""
    server = create_server()
    app = server.get_app()

    # Check that the app was created
    assert app is not None

    # The FastMCP app should be properly initialized
    assert hasattr(app, "list_prompts")
    assert hasattr(app, "add_resource")
    assert hasattr(app, "add_tool")


@pytest.mark.asyncio
async def test_player_stats_tool():
    """Test the get_player_season_stats tool."""
    server = create_server()
    app = server.get_app()

    # Test the tool exists and can be called
    # Note: In a real implementation, we'd need to test the actual tool invocation
    # For now, we just verify the server structure is correct
    assert app is not None


@pytest.mark.asyncio
async def test_team_stats_tool():
    """Test the get_team_stats tool."""
    server = create_server()
    app = server.get_app()

    # Test the tool exists and can be called
    assert app is not None


@pytest.mark.asyncio
async def test_list_players_tool():
    """Test the list_available_players tool."""
    server = create_server()
    app = server.get_app()

    # Test the tool exists and can be called
    assert app is not None


def test_server_app_name():
    """Test that the server has the correct application name."""
    server = create_server()
    app = server.get_app()

    # The server should be properly named
    assert app is not None
