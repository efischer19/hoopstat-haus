"""
Gold Layer Analytics Application for NBA Statistics.

This application processes Silver layer data and transforms it into
advanced analytics metrics stored in S3 Tables using Apache Iceberg format.
"""

import os
import sys
from datetime import UTC, datetime

import click
from hoopstat_observability import get_logger

from .processors import GoldProcessor

logger = get_logger(__name__)


@click.group()
@click.option("--debug/--no-debug", default=False, help="Enable debug logging")
def cli(debug: bool) -> None:
    """Gold layer analytics processing pipeline for NBA statistics."""
    if debug:
        logger.info("Debug mode enabled")


@cli.command()
@click.option(
    "--date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Date to process (YYYY-MM-DD), defaults to today (UTC)",
)
@click.option("--dry-run", is_flag=True, help="Run without making changes")
@click.option(
    "--silver-bucket",
    type=str,
    help="S3 bucket name for Silver data (can also be set via SILVER_BUCKET env var)",
)
@click.option(
    "--gold-bucket",
    type=str,
    help="S3 bucket name for Gold S3 Tables (can also be set via GOLD_BUCKET env var)",
)
def process(
    date: datetime | None,
    dry_run: bool,
    silver_bucket: str | None,
    gold_bucket: str | None,
) -> None:
    """Process Silver layer data into Gold layer analytics."""
    # Default to today (UTC) if no date provided
    target_date = date.date() if date else datetime.now(UTC).date()

    logger.info(f"Starting gold layer analytics processing for date: {target_date}")

    if dry_run:
        logger.info("Dry run mode - no data will be written")

    # Get silver bucket from CLI option or environment variable
    silver_bucket_name = silver_bucket or os.getenv("SILVER_BUCKET")
    if not silver_bucket_name:
        logger.error(
            "Silver bucket not specified. Use --silver-bucket option or set "
            "SILVER_BUCKET environment variable"
        )
        sys.exit(1)

    # Get gold bucket from CLI option or environment variable
    gold_bucket_name = gold_bucket or os.getenv("GOLD_BUCKET")
    if not gold_bucket_name:
        logger.error(
            "Gold bucket not specified. Use --gold-bucket option or set "
            "GOLD_BUCKET environment variable"
        )
        sys.exit(1)

    try:
        # Initialize Gold processor with Silver and Gold buckets
        processor = GoldProcessor(
            silver_bucket=silver_bucket_name, gold_bucket=gold_bucket_name
        )

        # Process the target date
        success = processor.process_date(target_date, dry_run=dry_run)

        if success:
            logger.info("Gold layer analytics processing completed successfully")
        else:
            logger.error("Gold layer analytics processing failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Gold layer analytics processing failed: {e}")
        sys.exit(1)


@cli.command()
def status() -> None:
    """Check the status of the gold layer analytics pipeline."""
    logger.info("Checking gold layer analytics status...")

    try:
        # TODO: Implement status checks for S3 Tables in upcoming PR
        logger.info("Gold layer analytics pipeline is ready")

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the gold layer analytics application."""
    cli()


if __name__ == "__main__":
    main()
