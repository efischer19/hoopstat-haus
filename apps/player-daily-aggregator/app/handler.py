"""
AWS Lambda handler for player daily statistics aggregation.

This module contains the main Lambda function that processes Silver layer
player game data and creates Gold layer daily aggregations.
"""

import json
import logging
from typing import Any
from urllib.parse import unquote_plus

from app.aggregator import PlayerStatsAggregator
from app.config import LambdaConfig
from app.s3_utils import S3Client

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    AWS Lambda handler for processing S3 events and aggregating player stats.

    Args:
        event: AWS Lambda event (S3 event notification)
        context: AWS Lambda context object

    Returns:
        Dict containing processing results and status
    """
    try:
        # Initialize configuration
        config = LambdaConfig.from_environment()

        # Initialize S3 client
        s3_client = S3Client(config.aws_region)

        # Initialize aggregator
        aggregator = PlayerStatsAggregator(config, s3_client)

        # Process S3 events
        results = []

        for record in event.get("Records", []):
            if record.get("eventSource") == "aws:s3":
                try:
                    result = process_s3_event(record, aggregator)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing S3 event: {e}")
                    results.append(
                        {
                            "status": "error",
                            "error": str(e),
                            "bucket": record.get("s3", {})
                            .get("bucket", {})
                            .get("name"),
                            "key": record.get("s3", {}).get("object", {}).get("key"),
                        }
                    )

        # Return summary
        successful = len([r for r in results if r.get("status") == "success"])
        failed = len([r for r in results if r.get("status") == "error"])

        return {
            "statusCode": 200 if failed == 0 else 207,  # 207 = Multi-Status
            "body": json.dumps(
                {
                    "message": (
                        f"Processed {len(results)} events: "
                        f"{successful} successful, {failed} failed"
                    ),
                    "results": results,
                }
            ),
        }

    except Exception as e:
        logger.error(f"Lambda handler error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal server error", "error": str(e)}),
        }


def process_s3_event(
    record: dict[str, Any], aggregator: PlayerStatsAggregator
) -> dict[str, Any]:
    """
    Process a single S3 event record.

    Args:
        record: S3 event record
        aggregator: PlayerStatsAggregator instance

    Returns:
        Dict containing processing result
    """
    # Extract S3 information
    bucket = record["s3"]["bucket"]["name"]
    key = unquote_plus(record["s3"]["object"]["key"])

    logger.info(f"Processing S3 object: s3://{bucket}/{key}")

    # Validate this is a Silver layer file we should process
    if not _is_valid_silver_file(key):
        logger.info(f"Skipping non-Silver file: {key}")
        return {
            "status": "skipped",
            "reason": "Not a valid Silver layer player stats file",
            "bucket": bucket,
            "key": key,
        }

    # Process the file
    try:
        stats = aggregator.process_silver_file(bucket, key)

        return {
            "status": "success",
            "bucket": bucket,
            "key": key,
            "players_processed": stats["players_processed"],
            "files_written": stats["files_written"],
            "season": stats.get("season"),
            "date": stats.get("date"),
        }

    except Exception as e:
        logger.error(f"Error processing file s3://{bucket}/{key}: {e}")
        raise


def _is_valid_silver_file(key: str) -> bool:
    """
    Check if S3 key represents a valid Silver layer player stats file.

    Args:
        key: S3 object key

    Returns:
        True if this is a file we should process
    """
    # Expected pattern: silver/player_games/season=YYYY/date=YYYY-MM-DD/...parquet
    parts = key.split("/")

    if len(parts) < 4:
        return False

    if not (parts[0] == "silver" and parts[1] == "player_games"):
        return False

    # Check for season and date partitions
    season_part = next((p for p in parts if p.startswith("season=")), None)
    date_part = next((p for p in parts if p.startswith("date=")), None)

    if not (season_part and date_part):
        return False

    # Check file extension
    if not key.endswith(".parquet"):
        return False

    return True


# For local testing
if __name__ == "__main__":
    # Example S3 event for testing
    test_event = {
        "Records": [
            {
                "eventSource": "aws:s3",
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {
                        "key": (
                            "silver/player_games/season=2023/"
                            "date=2024-01-15/player_stats.parquet"
                        )
                    },
                },
            }
        ]
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
