"""
Bronze Layer Ingestion Application for NBA Statistics.

This application ingests NBA data from the NBA API and stores it in the bronze
layer of our data lake following the medallion architecture pattern.
"""

import sys

import click
from hoopstat_observability import get_logger

logger = get_logger(__name__)


@click.group()
@click.option("--debug/--no-debug", default=False, help="Enable debug logging")
def cli(debug: bool) -> None:
    """Bronze layer ingestion pipeline for NBA statistics."""
    if debug:
        logger.info("Debug mode enabled")


@cli.command()
@click.option(
    "--season", default="2024-25", help="NBA season to ingest (e.g., 2024-25)"
)
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def ingest(season: str, dry_run: bool) -> None:
    """Ingest NBA data for the specified season."""
    logger.info(f"Starting bronze layer ingestion for season: {season}")

    if dry_run:
        logger.info("Dry run mode - no data will be written")

    try:
        # TODO: Implement actual ingestion logic
        # This is a minimal structure to get the app working
        logger.info("Bronze layer ingestion completed successfully")

    except Exception as e:
        logger.error(f"Bronze layer ingestion failed: {e}")
        sys.exit(1)


@cli.command()
def status() -> None:
    """Check the status of the bronze layer ingestion pipeline."""
    logger.info("Checking bronze layer ingestion status...")

    try:
        # TODO: Implement status checking logic
        logger.info("Bronze layer ingestion pipeline is ready")

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the bronze layer ingestion application."""
    cli()


if __name__ == "__main__":
    main()
