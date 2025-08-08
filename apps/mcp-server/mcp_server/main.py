"""
Main entry point for the Hoopstat MCP Server.
"""

import logging
import sys

from .server import create_server

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting Hoopstat MCP Server...")

    try:
        server = create_server()
        server.run()  # Use the synchronous run method
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
