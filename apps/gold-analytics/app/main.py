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

from .config import load_config
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
@click.option(
    "--gold-bucket",
    type=str,
    help="S3 bucket name for Gold S3 Tables (can also be set via GOLD_BUCKET env var)",
)
def status(gold_bucket: str | None) -> None:
    """Check the status of the gold layer analytics pipeline."""
    logger.info("Checking gold layer analytics status...")

    # Get gold bucket from CLI option or environment variable
    gold_bucket_name = gold_bucket or os.getenv("GOLD_BUCKET")
    if not gold_bucket_name:
        logger.error(
            "Gold bucket not specified. Use --gold-bucket option or set "
            "GOLD_BUCKET environment variable"
        )
        sys.exit(1)

    try:
        from .iceberg_integration import IcebergS3TablesWriter

        # Initialize Iceberg writer and check table health
        iceberg_writer = IcebergS3TablesWriter(gold_bucket_name)

        # Check both analytics tables
        player_health = iceberg_writer.check_table_health(
            "basketball_analytics.player_analytics"
        )
        team_health = iceberg_writer.check_table_health(
            "basketball_analytics.team_analytics"
        )

        logger.info("=== S3 Tables Health Check ===")
        logger.info(
            f"Player Analytics Table: {'✓' if player_health['exists'] else '✗'}"
        )
        if player_health.get("error"):
            logger.error(f"  Error: {player_health['error']}")
        elif player_health["exists"]:
            logger.info(
                f"  Schema version: {player_health.get('schema_version', 'unknown')}"
            )
            logger.info(f"  Snapshot ID: {player_health.get('snapshot_id', 'none')}")

        logger.info(f"Team Analytics Table: {'✓' if team_health['exists'] else '✗'}")
        if team_health.get("error"):
            logger.error(f"  Error: {team_health['error']}")
        elif team_health["exists"]:
            logger.info(
                f"  Schema version: {team_health.get('schema_version', 'unknown')}"
            )
            logger.info(f"  Snapshot ID: {team_health.get('snapshot_id', 'none')}")

        if player_health["exists"] and team_health["exists"]:
            logger.info("Gold layer analytics pipeline is ready ✓")
        else:
            logger.warning(
                "Some S3 Tables are not available - first write will create them"
            )

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--season",
    type=str,
    required=True,
    help="Season to process (e.g., '2023-24')",
)
@click.option(
    "--player-id",
    type=str,
    help="Specific player ID to process (optional, processes all if not specified)",
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
def season_players(
    season: str,
    player_id: str | None,
    dry_run: bool,
    silver_bucket: str | None,
    gold_bucket: str | None,
) -> None:
    """Process player season aggregations from Silver layer data."""
    logger.info(f"Starting player season aggregation for season: {season}")

    if player_id:
        logger.info(f"Processing specific player: {player_id}")

    if dry_run:
        logger.info("Dry run mode - no data will be written")

    # Get bucket names
    silver_bucket_name = silver_bucket or os.getenv("SILVER_BUCKET")
    gold_bucket_name = gold_bucket or os.getenv("GOLD_BUCKET")

    if not silver_bucket_name:
        logger.error(
            "Silver bucket not specified. Use --silver-bucket option or set "
            "SILVER_BUCKET environment variable"
        )
        sys.exit(1)

    if not gold_bucket_name:
        logger.error(
            "Gold bucket not specified. Use --gold-bucket option or set "
            "GOLD_BUCKET environment variable"
        )
        sys.exit(1)

    try:
        processor = GoldProcessor(
            silver_bucket=silver_bucket_name, gold_bucket=gold_bucket_name
        )

        success = processor.process_season_aggregation(
            season=season, player_id=player_id, dry_run=dry_run
        )

        if success:
            logger.info("Player season aggregation completed successfully")
        else:
            logger.error("Player season aggregation failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Player season aggregation failed: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--season",
    type=str,
    required=True,
    help="Season to process (e.g., '2023-24')",
)
@click.option(
    "--team-id",
    type=str,
    help="Specific team ID to process (optional, processes all if not specified)",
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
def season_teams(
    season: str,
    team_id: str | None,
    dry_run: bool,
    silver_bucket: str | None,
    gold_bucket: str | None,
) -> None:
    """Process team season aggregations from Silver layer data."""
    logger.info(f"Starting team season aggregation for season: {season}")

    if team_id:
        logger.info(f"Processing specific team: {team_id}")

    if dry_run:
        logger.info("Dry run mode - no data will be written")

    # Get bucket names
    silver_bucket_name = silver_bucket or os.getenv("SILVER_BUCKET")
    gold_bucket_name = gold_bucket or os.getenv("GOLD_BUCKET")

    if not silver_bucket_name:
        logger.error(
            "Silver bucket not specified. Use --silver-bucket option or set "
            "SILVER_BUCKET environment variable"
        )
        sys.exit(1)

    if not gold_bucket_name:
        logger.error(
            "Gold bucket not specified. Use --gold-bucket option or set "
            "GOLD_BUCKET environment variable"
        )
        sys.exit(1)

    try:
        processor = GoldProcessor(
            silver_bucket=silver_bucket_name, gold_bucket=gold_bucket_name
        )

        success = processor.process_team_season_aggregation(
            season=season, team_id=team_id, dry_run=dry_run
        )

        if success:
            logger.info("Team season aggregation completed successfully")
        else:
            logger.error("Team season aggregation failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Team season aggregation failed: {e}")
        sys.exit(1)


@cli.command()
@click.option("--dry-run", is_flag=True, help="Run without making changes")
@click.option(
    "--lookback-days",
    type=int,
    default=7,
    help="Number of days to look back for new data (default: 7)",
)
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
def incremental(
    dry_run: bool,
    lookback_days: int,
    silver_bucket: str | None,
    gold_bucket: str | None,
) -> None:
    """Process incremental updates from Silver layer data."""
    logger.info("Starting incremental Gold analytics processing")

    if dry_run:
        logger.info("Dry run mode - no data will be written")

    # Get bucket names
    silver_bucket_name = silver_bucket or os.getenv("SILVER_BUCKET")
    gold_bucket_name = gold_bucket or os.getenv("GOLD_BUCKET")

    if not silver_bucket_name:
        logger.error(
            "Silver bucket not specified. Use --silver-bucket option or set "
            "SILVER_BUCKET environment variable"
        )
        sys.exit(1)

    if not gold_bucket_name:
        logger.error(
            "Gold bucket not specified. Use --gold-bucket option or set "
            "GOLD_BUCKET environment variable"
        )
        sys.exit(1)

    try:
        # Use configuration if available
        try:
            config = load_config()
            processor = GoldProcessor(
                silver_bucket=silver_bucket_name,
                gold_bucket=gold_bucket_name,
                config=config,
            )
        except ValueError:
            # Fall back to basic initialization
            processor = GoldProcessor(
                silver_bucket=silver_bucket_name, gold_bucket=gold_bucket_name
            )

        # Process incremental updates
        results = processor.process_incremental(dry_run=dry_run)

        logger.info(f"Incremental processing results: {results['message']}")
        if results["status"] == "success":
            logger.info("Incremental Gold analytics processing completed successfully")
        elif results["status"] == "partial":
            logger.warning("Incremental processing completed with some failures")
            if results.get("dates_failed"):
                logger.warning(f"Failed dates: {results['dates_failed']}")
        else:
            logger.error("Incremental Gold analytics processing failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Incremental Gold analytics processing failed: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--start-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    required=True,
    help="Start date for processing range (YYYY-MM-DD)",
)
@click.option(
    "--end-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    required=True,
    help="End date for processing range (YYYY-MM-DD)",
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
def process_range(
    start_date: datetime,
    end_date: datetime,
    dry_run: bool,
    silver_bucket: str | None,
    gold_bucket: str | None,
) -> None:
    """Process Gold analytics for a range of dates."""
    start_date_obj = start_date.date()
    end_date_obj = end_date.date()

    logger.info(f"Processing Gold analytics from {start_date_obj} to {end_date_obj}")

    if dry_run:
        logger.info("Dry run mode - no data will be written")

    # Get bucket names
    silver_bucket_name = silver_bucket or os.getenv("SILVER_BUCKET")
    gold_bucket_name = gold_bucket or os.getenv("GOLD_BUCKET")

    if not silver_bucket_name:
        logger.error(
            "Silver bucket not specified. Use --silver-bucket option or set "
            "SILVER_BUCKET environment variable"
        )
        sys.exit(1)

    if not gold_bucket_name:
        logger.error(
            "Gold bucket not specified. Use --gold-bucket option or set "
            "GOLD_BUCKET environment variable"
        )
        sys.exit(1)

    try:
        # Use configuration if available
        try:
            config = load_config()
            processor = GoldProcessor(
                silver_bucket=silver_bucket_name,
                gold_bucket=gold_bucket_name,
                config=config,
            )
        except ValueError:
            # Fall back to basic initialization
            processor = GoldProcessor(
                silver_bucket=silver_bucket_name, gold_bucket=gold_bucket_name
            )

        # Process the date range
        results = processor.process_date_range(
            start_date_obj, end_date_obj, dry_run=dry_run
        )

        successful_dates = sum(1 for success in results.values() if success)
        total_dates = len(results)

        if successful_dates == total_dates and total_dates > 0:
            logger.info(
                f"Date range processing completed successfully: "
                f"{successful_dates} dates"
            )
        elif successful_dates > 0:
            logger.warning(
                f"Date range processing completed with some failures: "
                f"{successful_dates}/{total_dates} dates successful"
            )
        else:
            logger.error("Date range processing failed for all dates")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Date range processing failed: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the gold layer analytics application."""
    cli()


if __name__ == "__main__":
    main()
