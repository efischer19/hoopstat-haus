"""
Silver Layer Processing Application for NBA Statistics.

This application processes Bronze layer JSON data and transforms it into
validated, cleaned Silver layer data following the medallion architecture pattern.
"""

import os
import sys
from datetime import UTC, datetime

import boto3
import click
from botocore.exceptions import BotoCoreError, ClientError
from hoopstat_observability import get_logger

from .processors import SilverProcessor

logger = get_logger(__name__)

# Silver entity type prefixes
SILVER_ENTITY_TYPES = ["player-stats", "team-stats", "game-stats"]


@click.group()
@click.option("--debug/--no-debug", default=False, help="Enable debug logging")
def cli(debug: bool) -> None:
    """Silver layer processing pipeline for NBA statistics."""
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
    "--bronze-bucket",
    type=str,
    help="S3 bucket name for Bronze data (can also be set via BRONZE_BUCKET env var)",
)
@click.option(
    "--silver-bucket",
    type=str,
    help="S3 bucket name for Silver data (can also be set via SILVER_BUCKET env var)",
)
def process(
    date: datetime | None,
    dry_run: bool,
    bronze_bucket: str | None,
    silver_bucket: str | None,
) -> None:
    """Process Bronze layer data into Silver layer format."""
    # Default to today (UTC) if no date provided
    target_date = date.date() if date else datetime.now(UTC).date()

    logger.info(f"Starting silver layer processing for date: {target_date}")

    if dry_run:
        logger.info("Dry run mode - no data will be written")

    # Get bronze bucket from CLI option or environment variable
    bronze_bucket_name = bronze_bucket or os.getenv("BRONZE_BUCKET")
    if not bronze_bucket_name:
        logger.error(
            "Bronze bucket not specified. Use --bronze-bucket option or set "
            "BRONZE_BUCKET environment variable"
        )
        sys.exit(1)

    # Get silver bucket from CLI option or environment variable
    silver_bucket_name = silver_bucket or os.getenv("SILVER_BUCKET")
    if not silver_bucket_name:
        logger.error(
            "Silver bucket not specified. Use --silver-bucket option or set "
            "SILVER_BUCKET environment variable"
        )
        sys.exit(1)

    try:
        # Initialize Silver processor with both Bronze and Silver buckets
        processor = SilverProcessor(
            bronze_bucket=bronze_bucket_name, silver_bucket=silver_bucket_name
        )

        # Process the target date
        success = processor.process_date(target_date, dry_run=dry_run)

        if success:
            logger.info("Silver layer processing completed successfully")
        else:
            logger.error("Silver layer processing failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Silver layer processing failed: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--silver-bucket",
    type=str,
    help="S3 bucket name for Silver data (can also be set via SILVER_BUCKET env var)",
)
def status(silver_bucket: str | None) -> None:
    """Check the status of the silver layer processing pipeline."""
    logger.info("Checking silver layer processing status...")

    # Get silver bucket from CLI option or environment variable
    silver_bucket_name = silver_bucket or os.getenv("SILVER_BUCKET")
    if not silver_bucket_name:
        logger.error(
            "Silver bucket not specified. Use --silver-bucket option or set "
            "SILVER_BUCKET environment variable"
        )
        sys.exit(1)

    try:
        click.echo("=== Silver Layer Status Check ===")
        click.echo(f"Silver Bucket: {silver_bucket_name}")

        s3_client = boto3.client("s3", region_name="us-east-1")

        # Check for silver data prefixes
        silver_response = s3_client.list_objects_v2(
            Bucket=silver_bucket_name, Prefix="silver/", Delimiter="/"
        )
        prefixes = [p["Prefix"] for p in silver_response.get("CommonPrefixes", [])]

        if not prefixes:
            logger.error("No entity types found under silver/ prefix")
            sys.exit(1)

        click.echo(f"Entity prefixes found: {prefixes}")

        # Count objects per entity type
        for entity_type in SILVER_ENTITY_TYPES:
            prefix = f"silver/{entity_type}/"
            count_response = s3_client.list_objects_v2(
                Bucket=silver_bucket_name, Prefix=prefix
            )
            count = count_response.get("KeyCount", 0)
            click.echo(f"Object count for {entity_type}: {count}")

        # Check for recent silver-ready markers
        marker_response = s3_client.list_objects_v2(
            Bucket=silver_bucket_name, Prefix="metadata/", Delimiter="/"
        )
        marker_dates = sorted(
            p["Prefix"].removeprefix("metadata/").rstrip("/")
            for p in marker_response.get("CommonPrefixes", [])
        )

        if marker_dates:
            click.echo(
                f"Silver-ready markers found for {len(marker_dates)} date(s), "
                f"latest: {marker_dates[-1]}"
            )
        else:
            click.echo("No silver-ready markers found under metadata/")

        click.echo("Silver layer status check passed")

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Status check failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the silver layer processing application."""
    cli()


if __name__ == "__main__":
    main()
