"""
Gold Layer Analytics Application for NBA Statistics.

This application processes Silver layer data and transforms it into
advanced analytics metrics per ADR-028.
"""

import json
import os
import sys
from datetime import UTC, datetime

import boto3
import click
from botocore.exceptions import BotoCoreError, ClientError
from hoopstat_observability import get_logger

from .config import load_config
from .processors import GoldProcessor

logger = get_logger(__name__)

# Artifact type prefixes under served/ per ADR-028
SERVED_ARTIFACT_TYPES = ["player_daily", "team_daily", "top_lists"]


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
    help="S3 bucket name for Gold data (can also be set via GOLD_BUCKET env var)",
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
    help="S3 bucket name for Gold data (can also be set via GOLD_BUCKET env var)",
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
        click.echo("=== Gold Layer Status Check ===")
        click.echo(f"Gold Bucket: {gold_bucket_name}")

        aws_region = os.getenv("AWS_REGION", "us-east-1")
        s3_client = boto3.client("s3", region_name=aws_region)

        # List artifact types under served/ prefix
        served_response = s3_client.list_objects_v2(
            Bucket=gold_bucket_name, Prefix="served/", Delimiter="/"
        )
        prefixes = [p["Prefix"] for p in served_response.get("CommonPrefixes", [])]

        if not prefixes:
            logger.error("No artifact types found under served/ prefix")
            sys.exit(1)

        click.echo(f"Artifact prefixes found: {prefixes}")

        # Validate served/index/latest.json is present and parseable
        try:
            index_response = s3_client.get_object(
                Bucket=gold_bucket_name, Key="served/index/latest.json"
            )
            index_body = index_response["Body"].read().decode("utf-8")
            index_data = json.loads(index_body)
            latest_date = index_data.get("latest_date", "unknown")
            click.echo(f"Index file valid — latest date: {latest_date}")
        except ClientError as e:
            logger.error(f"Index file not accessible: {e}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Index file is not valid JSON: {e}")
            sys.exit(1)

        # Count artifacts per type
        for artifact_type in SERVED_ARTIFACT_TYPES:
            prefix = f"served/{artifact_type}/"
            count_response = s3_client.list_objects_v2(
                Bucket=gold_bucket_name, Prefix=prefix
            )
            count = count_response.get("KeyCount", 0)
            click.echo(f"Artifact count for {artifact_type}: {count}")

        click.echo("Gold layer status check passed")

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Status check failed: {e}")
        sys.exit(1)
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
    help="S3 bucket name for Gold data (can also be set via GOLD_BUCKET env var)",
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
    help="S3 bucket name for Gold data (can also be set via GOLD_BUCKET env var)",
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
    help="S3 bucket name for Gold data (can also be set via GOLD_BUCKET env var)",
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
    help="S3 bucket name for Gold data (can also be set via GOLD_BUCKET env var)",
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
