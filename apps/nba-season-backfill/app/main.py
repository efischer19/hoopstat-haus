"""
Main CLI entry point for NBA season backfill application.

Provides command-line interface for configuring and running the backfill
process with proper error handling and structured logging.
"""

import sys

import click
from dotenv import load_dotenv
from hoopstat_observability import get_logger, performance_context

from .backfill_runner import BackfillRunner
from .config import BackfillConfig

# Load environment variables from .env file if present
load_dotenv()

logger = get_logger(__name__)


@click.command()
@click.option(
    "--season",
    default="2024-25",
    help="NBA season to backfill (format: YYYY-YY)",
)
@click.option(
    "--rate-limit",
    default=5.0,
    type=float,
    help="Seconds to wait between NBA API requests",
)
@click.option(
    "--s3-bucket",
    default="hoopstat-haus-bronze",
    help="S3 bucket for Bronze layer storage",
)
@click.option(
    "--s3-prefix",
    default="historical-backfill",
    help="S3 prefix for backfill data",
)
@click.option(
    "--state-file-path",
    default="s3://hoopstat-haus-bronze/backfill-state/checkpoint.json",
    help="Path to state/checkpoint file",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Run in dry-run mode without making API calls or uploads",
)
@click.option(
    "--resume",
    is_flag=True,
    help="Resume from existing checkpoint",
)
@click.option(
    "--max-retries",
    default=3,
    type=int,
    help="Maximum retry attempts for transient failures",
)
@click.option(
    "--no-box-scores",
    is_flag=True,
    help="Skip box score collection",
)
@click.option(
    "--no-play-by-play",
    is_flag=True,
    help="Skip play-by-play collection",
)
@click.option(
    "--no-player-info",
    is_flag=True,
    help="Skip player info collection",
)
def main(
    season: str,
    rate_limit: float,
    s3_bucket: str,
    s3_prefix: str,
    state_file_path: str,
    dry_run: bool,
    resume: bool,
    max_retries: int,
    no_box_scores: bool,
    no_play_by_play: bool,
    no_player_info: bool,
):
    """
    NBA Season Backfill Application

    Containerized application for backfilling NBA 2024-25 season data from NBA API
    to Bronze layer S3 storage with rate limiting and state management.
    """
    try:
        # Create configuration
        config = BackfillConfig(
            target_season=season,
            rate_limit_seconds=rate_limit,
            s3_bucket=s3_bucket,
            s3_prefix=s3_prefix,
            state_file_path=state_file_path,
            dry_run=dry_run,
            resume_from_checkpoint=resume,
            max_retries=max_retries,
            collect_box_scores=not no_box_scores,
            collect_play_by_play=not no_play_by_play,
            collect_player_info=not no_player_info,
        )

        logger.info(
            "Starting NBA season backfill application",
            season=config.target_season,
            dry_run=config.dry_run,
            resume=config.resume_from_checkpoint,
            rate_limit_seconds=config.rate_limit_seconds,
        )

        # Run backfill with performance monitoring
        with performance_context("nba_season_backfill") as ctx:
            runner = BackfillRunner(config)
            result = runner.run()

            # Update performance context with results
            ctx["records_processed"] = result.get("total_games_processed", 0)

            logger.info("NBA season backfill completed successfully", **result)

    except Exception as e:
        logger.error(
            "NBA season backfill failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
