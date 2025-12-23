"""
Bronze Layer Ingestion Application for NBA Statistics.

This application ingests NBA data from the NBA API and stores it in the bronze
layer of our data lake following the medallion architecture pattern.
Date-scoped runner that fetches NBA data for a specific date.
"""

import sys
from datetime import datetime

import click
from hoopstat_observability import get_logger

from .ingestion import DateScopedIngestion

# Trigger deployment test - attempt 2
logger = get_logger(__name__)


@click.group()
@click.option("--debug/--no-debug", default=False, help="Enable debug logging")
def cli(debug: bool) -> None:
    """Bronze layer ingestion pipeline for NBA statistics."""
    if debug:
        logger.info("Debug mode enabled")


@cli.command()
@click.option(
    "--date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Date to ingest (YYYY-MM-DD), defaults to today (UTC)",
)
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def ingest(date: datetime | None, dry_run: bool) -> None:
    """Ingest NBA data for the specified date."""
    # Default to today (UTC) if no date provided
    target_date = date.date() if date else datetime.utcnow().date()

    logger.info(f"Starting bronze layer ingestion for date: {target_date}")

    if dry_run:
        logger.info("Dry run mode - no data will be written")

    try:
        ingestion = DateScopedIngestion()
        success = ingestion.run(target_date=target_date, dry_run=dry_run)

        if success:
            logger.info("Bronze layer ingestion completed successfully")
        else:
            logger.error("Bronze layer ingestion failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Bronze layer ingestion failed: {e}")
        sys.exit(1)


@cli.command()
def status() -> None:
    """Check the status of the bronze layer ingestion pipeline."""
    logger.info("Checking bronze layer ingestion status...")

    try:
        # Check if we can create ingestion instance (validates config)
        DateScopedIngestion()
        logger.info("Bronze layer ingestion pipeline is ready")

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the bronze layer ingestion application."""
    cli()


if __name__ == "__main__":
    main()
