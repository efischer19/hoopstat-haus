"""
Bronze Layer Ingestion Application for NBA Statistics.

This application ingests NBA data from the NBA API and stores it in the bronze
layer of our data lake following the medallion architecture pattern.

Implements date-scoped ingestion per requirements:
- CLI supports --date YYYY-MM-DD (default: today UTC)
- First API call fetches schedule; if no games, exit 0
- Persists Bronze artifacts exclusively in Parquet (ADR-014)
- Uses tenacity for retries (ADR-021) and structured logging (ADR-015)
"""

import sys
from datetime import UTC, datetime

import click
from hoopstat_observability import get_logger

from .config import BronzeIngestionConfig
from .ingester import BronzeIngester

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
    default=None,
    help="Date to ingest in YYYY-MM-DD format (default: today UTC)",
)
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def ingest(date: str, dry_run: bool) -> None:
    """Ingest NBA data for the specified date."""
    # Use today UTC if no date provided
    if date is None:
        date = datetime.now(UTC).strftime("%Y-%m-%d")

    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        logger.error(f"Invalid date format: {date}. Use YYYY-MM-DD format.")
        sys.exit(1)

    logger.info(f"Starting bronze layer ingestion for date: {date}")

    if dry_run:
        logger.info("Dry run mode - no data will be written")

    try:
        # Load configuration
        config = BronzeIngestionConfig.load()

        # Create ingester and run
        ingester = BronzeIngester(config)
        result = ingester.ingest_for_date(date, dry_run=dry_run)

        total_records = sum(result.values())
        logger.info(
            f"Bronze layer ingestion completed successfully: "
            f"{total_records} total records",
            extra={"entity_counts": result},
        )

    except Exception as e:
        logger.error(f"Bronze layer ingestion failed: {e}")
        sys.exit(1)


@cli.command()
def status() -> None:
    """Check the status of the bronze layer ingestion pipeline."""
    logger.info("Checking bronze layer ingestion status...")

    try:
        # Load configuration to test connectivity
        config = BronzeIngestionConfig.load()

        # Test S3 connectivity
        from .s3_client import S3ParquetClient

        S3ParquetClient(config)  # Test initialization only

        logger.info("Bronze layer ingestion pipeline is ready")
        logger.info(f"Connected to S3 bucket: {config.bronze_bucket_name}")

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the bronze layer ingestion application."""
    cli()


if __name__ == "__main__":
    main()
