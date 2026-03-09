"""CLI entry point for the Hoopstat Haus MCP local proxy adapter.

Starts an MCP server using stdio transport, enabling AI agents to
query NBA statistics data served from CloudFront.

Usage:
    hoopstat-mcp          # via installed script
    uvx hoopstat-mcp      # via uvx
    python -m app.main    # direct invocation
"""

from app.server import mcp


def main():
    """Run the MCP server with stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
