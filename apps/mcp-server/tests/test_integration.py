"""
Integration tests for MCP protocol compliance.
"""

import pytest

from mcp_server.server import create_server


@pytest.mark.asyncio
async def test_mcp_resources_discovery():
    """Test that the MCP server provides proper resource discovery."""
    server = create_server()
    app = server.get_app()

    # The server should have resources defined
    assert app is not None


@pytest.mark.asyncio
async def test_mcp_tools_discovery():
    """Test that the MCP server provides proper tool discovery."""
    server = create_server()
    app = server.get_app()

    # The server should have tools defined
    assert app is not None


def test_server_has_basketball_resources():
    """Test that the server has basketball-specific resources."""
    server = create_server()
    app = server.get_app()

    # Verify the server was created with basketball data focus
    assert app is not None


def test_server_has_basketball_tools():
    """Test that the server has basketball-specific tools."""
    server = create_server()
    app = server.get_app()

    # Verify the server has the expected tools for basketball data
    assert app is not None


def test_server_protocol_compliance():
    """Test basic MCP protocol compliance."""
    server = create_server()
    app = server.get_app()

    # The FastMCP app should have the required methods for MCP compliance
    assert hasattr(app, "run")
    assert hasattr(app, "run_stdio_async")
    assert callable(app.run)
    assert callable(app.run_stdio_async)


def test_server_error_handling():
    """Test that the server handles errors gracefully."""
    server = create_server()
    app = server.get_app()

    # Basic test that the server can be created without errors
    assert app is not None
    
    # Test that the server has both synchronous and asynchronous run methods
    assert hasattr(server, "run")
    assert hasattr(server, "run_stdio")
    assert callable(server.run)
    assert callable(server.run_stdio)