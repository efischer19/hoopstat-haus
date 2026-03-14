"""Entry point for the Hoopstat Haus MCP local proxy adapter.

Defaults to CLI mode for human-readable output.  Pass ``--mcp`` to
start the MCP JSON-RPC server over stdio for AI clients.

Usage:
    hoopstat-mcp                      # interactive CLI
    hoopstat-mcp get-index            # fetch the latest data index
    hoopstat-mcp get-artifact URI     # fetch a specific artifact
    hoopstat-mcp --mcp                # start MCP stdio server
    uvx hoopstat-mcp --mcp            # via uvx
    python -m app.main --mcp          # direct invocation
"""

import sys


def main():
    """Dispatch between MCP server mode and CLI mode."""
    if "--mcp" in sys.argv:
        from app.server import mcp

        mcp.run(transport="stdio")
    else:
        from app.cli import cli

        cli()


if __name__ == "__main__":
    main()
