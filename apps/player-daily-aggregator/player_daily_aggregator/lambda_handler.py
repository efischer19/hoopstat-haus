"""
AWS Lambda handler for player daily statistics aggregation.

Main entry point that orchestrates the Silver-to-Gold ETL process
with structured logging per ADR-015.
"""

import json
import time
import uuid
from datetime import datetime
from typing import Any

from .aggregations import (
    aggregate_daily_stats,
    calculate_season_to_date_stats,
    validate_aggregated_data,
)
from .s3_utils import S3DataHandler, extract_s3_info_from_event


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Main Lambda handler for player daily statistics aggregation.

    Args:
        event: Lambda event (S3 trigger)
        context: Lambda context object

    Returns:
        Dictionary with processing results
    """
    # Initialize tracking variables
    start_time = time.time()
    correlation_id = f"agg-{uuid.uuid4().hex[:8]}"
    records_processed = 0

    try:
        # Log job start
        log_info("Player daily aggregation job started", correlation_id)

        # Extract S3 information from event
        s3_info = extract_s3_info_from_event(event)
        season = s3_info["season"]
        date = s3_info["date"]
        silver_path = s3_info["silver_path"]

        log_info(
            f"Processing Silver layer data for season={season}, date={date}",
            correlation_id,
            extra={"season": season, "date": date, "silver_path": silver_path},
        )

        # Initialize S3 handler
        s3_handler = S3DataHandler()

        # Read Silver layer data
        player_games_df = s3_handler.read_silver_layer_data(silver_path)

        if player_games_df.empty:
            log_warning("No player game data found in Silver layer", correlation_id)
            return create_response(
                "success",
                "No data to process",
                correlation_id,
                0,
                time.time() - start_time,
            )

        log_info(f"Read {len(player_games_df)} player game records", correlation_id)

        # Aggregate daily statistics
        daily_stats_df = aggregate_daily_stats(player_games_df)
        records_processed = len(daily_stats_df)

        if daily_stats_df.empty:
            log_warning("No daily statistics generated", correlation_id)
            return create_response(
                "success",
                "No statistics generated",
                correlation_id,
                0,
                time.time() - start_time,
            )

        # Validate aggregated data
        validation_results = validate_aggregated_data(daily_stats_df)
        if not validation_results["validation_passed"]:
            log_error(
                "Data validation failed",
                correlation_id,
                extra={"validation_issues": validation_results["issues"]},
            )
            return create_response(
                "error",
                "Data validation failed",
                correlation_id,
                records_processed,
                time.time() - start_time,
            )

        # Write daily statistics to Gold layer
        gold_base_path = "s3://hoopstat-haus-gold/player_daily_stats"
        written_paths = s3_handler.write_gold_layer_data(
            daily_stats_df, gold_base_path, partition_columns=["season", "player_id"]
        )

        log_info(
            f"Successfully wrote daily statistics to {len(written_paths)} partitions",
            correlation_id,
            extra={"written_paths_count": len(written_paths)},
        )

        # Calculate and write season-to-date statistics
        season_stats_written = 0
        for _, player_stats in daily_stats_df.iterrows():
            player_id = player_stats["player_id"]

            # Read existing season data
            existing_season_df = s3_handler.read_existing_season_data(
                player_id, season, "s3://hoopstat-haus-gold/player_season_stats"
            )

            # Calculate updated season stats
            updated_season_df = calculate_season_to_date_stats(
                daily_stats_df[daily_stats_df["player_id"] == player_id],
                existing_season_df,
            )

            # Write updated season stats
            season_base_path = "s3://hoopstat-haus-gold/player_season_stats"
            s3_handler.write_gold_layer_data(
                updated_season_df,
                season_base_path,
                partition_columns=["season", "player_id"],
            )
            season_stats_written += 1

        # Log successful completion
        duration = time.time() - start_time
        log_info(
            "Player daily aggregation completed successfully",
            correlation_id,
            extra={
                "records_processed": records_processed,
                "daily_partitions_written": len(written_paths),
                "season_stats_updated": season_stats_written,
                "duration_in_seconds": duration,
                "validation_passed": True,
            },
        )

        return create_response(
            "success",
            f"Processed {records_processed} player records",
            correlation_id,
            records_processed,
            duration,
        )

    except Exception as e:
        duration = time.time() - start_time
        error_msg = f"Player daily aggregation failed: {str(e)}"

        log_error(
            error_msg,
            correlation_id,
            extra={
                "duration_in_seconds": duration,
                "records_processed": records_processed,
            },
        )

        return create_response(
            "error", error_msg, correlation_id, records_processed, duration
        )


def create_response(
    status: str,
    message: str,
    correlation_id: str,
    records_processed: int,
    duration: float,
) -> dict[str, Any]:
    """Create standardized Lambda response."""
    return {
        "status": status,
        "message": message,
        "correlation_id": correlation_id,
        "records_processed": records_processed,
        "duration_in_seconds": round(duration, 2),
    }


def log_info(message: str, correlation_id: str, extra: dict[str, Any] = None) -> None:
    """Log INFO level message with structured JSON format per ADR-015."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": "INFO",
        "message": message,
        "job_name": "player_daily_aggregator",
        "correlation_id": correlation_id,
    }

    if extra:
        log_entry.update(extra)

    print(json.dumps(log_entry))


def log_warning(
    message: str, correlation_id: str, extra: dict[str, Any] = None
) -> None:
    """Log WARNING level message with structured JSON format per ADR-015."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": "WARNING",
        "message": message,
        "job_name": "player_daily_aggregator",
        "correlation_id": correlation_id,
    }

    if extra:
        log_entry.update(extra)

    print(json.dumps(log_entry))


def log_error(message: str, correlation_id: str, extra: dict[str, Any] = None) -> None:
    """Log ERROR level message with structured JSON format per ADR-015."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": "ERROR",
        "message": message,
        "job_name": "player_daily_aggregator",
        "correlation_id": correlation_id,
    }

    if extra:
        log_entry.update(extra)

    print(json.dumps(log_entry))
