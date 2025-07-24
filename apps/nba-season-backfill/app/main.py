"""Main entry point for NBA season backfill application."""

import logging
import sys

import click

from .backfill_runner import BackfillRunner
from .config import BackfillConfig


def setup_logging(log_level: str) -> None:
    """Setup structured JSON logging."""
    try:
        # Try to use hoopstat-observability for JSON logging
        from hoopstat_observability.json_logger import setup_json_logging

        setup_json_logging(service_name="nba-season-backfill", log_level=log_level)
    except ImportError:
        # Fallback to basic logging if hoopstat-observability not available
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


@click.command()
@click.option(
    "--season",
    envvar="SEASON",
    required=True,
    help="NBA season to backfill (e.g., 2024-25)",
)
@click.option(
    "--aws-region", envvar="AWS_REGION", required=True, help="AWS region for S3 bucket"
)
@click.option(
    "--s3-bucket-name",
    envvar="S3_BUCKET_NAME",
    required=True,
    help="S3 bucket name for Bronze layer storage",
)
@click.option(
    "--rate-limit-seconds",
    envvar="RATE_LIMIT_SECONDS",
    type=int,
    default=5,
    help="Seconds to wait between API requests",
)
@click.option(
    "--log-level",
    envvar="LOG_LEVEL",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Logging level",
)
@click.option(
    "--dry-run",
    envvar="DRY_RUN",
    is_flag=True,
    help="Run in dry-run mode without storing data",
)
@click.option(
    "--max-retries",
    envvar="MAX_RETRIES",
    type=int,
    default=3,
    help="Maximum retries for failed operations",
)
def main(
    season: str,
    aws_region: str,
    s3_bucket_name: str,
    rate_limit_seconds: int,
    log_level: str,
    dry_run: bool,
    max_retries: int,
) -> None:
    """NBA Season Data Backfill Application.

    Backfill NBA season data from the NBA API to S3 Bronze layer storage.
    """
    # Setup logging first
    setup_logging(log_level)
    logger = logging.getLogger(__name__)

    try:
        # Create configuration
        config = BackfillConfig(
            aws_region=aws_region,
            s3_bucket_name=s3_bucket_name,
            season=season,
            rate_limit_seconds=rate_limit_seconds,
            log_level=log_level,
            dry_run=dry_run,
            max_retries=max_retries,
        )

        # Validate configuration
        config.validate()

        logger.info(
            "Starting NBA season backfill application",
            extra={
                "season": config.season,
                "s3_bucket": config.s3_bucket_name,
                "aws_region": config.aws_region,
                "rate_limit_seconds": config.rate_limit_seconds,
                "dry_run": config.dry_run,
                "max_retries": config.max_retries,
            },
        )

        # Run backfill
        runner = BackfillRunner(config)
        success = runner.run()

        if success:
            logger.info("Backfill completed successfully")
            sys.exit(0)
        else:
            logger.error("Backfill failed")
            sys.exit(1)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


def main_env() -> None:
    """Entry point using environment variables only."""
    # Setup basic logging
    setup_logging("INFO")
    logger = logging.getLogger(__name__)

    try:
        # Create configuration from environment
        config = BackfillConfig.from_env()
        config.validate()

        logger.info(
            "Starting NBA season backfill from environment config",
            extra={
                "season": config.season,
                "s3_bucket": config.s3_bucket_name,
                "rate_limit_seconds": config.rate_limit_seconds,
                "dry_run": config.dry_run,
            },
        )

        # Run backfill
        runner = BackfillRunner(config)
        success = runner.run()

        sys.exit(0 if success else 1)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
