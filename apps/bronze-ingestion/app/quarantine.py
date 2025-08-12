"""
Data quarantine module for bronze layer ingestion.

Provides functionality to quarantine invalid data for manual review
and investigation while ensuring the ingestion pipeline continues.
"""

import json
from datetime import date, datetime
from typing import Any

from hoopstat_observability import get_logger

from .s3_manager import BronzeS3Manager

logger = get_logger(__name__)


class DataQuarantine:
    """
    Manages quarantining of invalid data for manual review.

    Stores invalid data in a structured way with metadata about
    validation failures for investigation and debugging.
    """

    def __init__(self, s3_manager: BronzeS3Manager):
        """
        Initialize the data quarantine system.

        Args:
            s3_manager: S3 manager for storing quarantined data
        """
        self.s3_manager = s3_manager
        self.quarantine_prefix = "quarantine"

    def quarantine_data(
        self,
        data: Any,
        validation_result: dict[str, Any],
        data_type: str,
        target_date: date,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Quarantine invalid data with validation metadata.

        Args:
            data: The invalid data to quarantine
            validation_result: Result from validation containing issues
            data_type: Type of data being quarantined (e.g., 'schedule', 'box_score')
            target_date: Date associated with the data
            context: Additional context information

        Returns:
            Quarantine key/path where data was stored
        """
        try:
            # Create quarantine record
            quarantine_record = {
                "data": data,
                "validation_result": validation_result,
                "metadata": {
                    "data_type": data_type,
                    "target_date": target_date.isoformat(),
                    "quarantine_timestamp": datetime.utcnow().isoformat(),
                    "context": context or {},
                    "issues_count": len(validation_result.get("issues", [])),
                    "validation_valid": validation_result.get("valid", False),
                },
            }

            # Generate quarantine key
            timestamp = datetime.utcnow()
            quarantine_key = self._generate_quarantine_key(
                data_type, target_date, timestamp
            )

            # Store in S3 quarantine area
            self._store_quarantine_record(quarantine_record, quarantine_key)

            # Log quarantine action
            logger.warning(
                f"Data quarantined: {data_type} for {target_date}",
                extra={
                    "quarantine_key": quarantine_key,
                    "data_type": data_type,
                    "target_date": target_date.isoformat(),
                    "issues_count": len(validation_result.get("issues", [])),
                    "validation_issues": validation_result.get("issues", []),
                },
            )

            return quarantine_key

        except Exception as e:
            logger.error(f"Failed to quarantine data: {e}")
            # Even if quarantining fails, we should continue processing
            return f"quarantine_failed_{datetime.utcnow().isoformat()}"

    def quarantine_api_response(
        self,
        response_data: Any,
        validation_result: dict[str, Any],
        api_endpoint: str,
        target_date: date,
        request_params: dict[str, Any] | None = None,
    ) -> str:
        """
        Quarantine invalid API response with request context.

        Args:
            response_data: Raw API response data
            validation_result: Validation result with issues
            api_endpoint: API endpoint that was called
            target_date: Date the request was for
            request_params: Parameters used in the API request

        Returns:
            Quarantine key where response was stored
        """
        context = {
            "api_endpoint": api_endpoint,
            "request_params": request_params or {},
            "response_type": "api_response",
        }

        return self.quarantine_data(
            response_data, validation_result, "api_response", target_date, context
        )

    def _generate_quarantine_key(
        self, data_type: str, target_date: date, timestamp: datetime
    ) -> str:
        """Generate a structured key for quarantined data."""
        return (
            f"{self.quarantine_prefix}/"
            f"year={target_date.year}/"
            f"month={target_date.month:02d}/"
            f"day={target_date.day:02d}/"
            f"{data_type}/"
            f"quarantine_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.json"
        )

    def _store_quarantine_record(self, record: dict[str, Any], key: str) -> None:
        """Store quarantine record in S3."""
        try:
            # Convert to JSON string
            json_data = json.dumps(record, default=str, indent=2)

            # Store in S3
            self.s3_manager.s3_client.put_object(
                Bucket=self.s3_manager.bucket_name,
                Key=key,
                Body=json_data.encode("utf-8"),
                ContentType="application/json",
                Metadata={
                    "quarantine_timestamp": datetime.utcnow().isoformat(),
                    "data_type": record["metadata"]["data_type"],
                    "issues_count": str(record["metadata"]["issues_count"]),
                },
            )

            logger.debug(f"Quarantine record stored at {key}")

        except Exception as e:
            logger.error(f"Failed to store quarantine record at {key}: {e}")
            raise

    def list_quarantined_data(
        self, target_date: date | None = None, data_type: str | None = None
    ) -> list[dict[str, Any]]:
        """
        List quarantined data for review.

        Args:
            target_date: Optional date filter
            data_type: Optional data type filter

        Returns:
            List of quarantine metadata records
        """
        try:
            # Build prefix for listing
            prefix = self.quarantine_prefix
            if target_date:
                prefix += (
                    f"/year={target_date.year}/"
                    f"month={target_date.month:02d}/"
                    f"day={target_date.day:02d}/"
                )
                if data_type:
                    prefix += f"{data_type}/"

            # List objects in quarantine area
            response = self.s3_manager.s3_client.list_objects_v2(
                Bucket=self.s3_manager.bucket_name, Prefix=prefix
            )

            quarantine_items = []
            for obj in response.get("Contents", []):
                item_info = {
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                    "metadata": obj.get("Metadata", {}),
                }
                quarantine_items.append(item_info)

            logger.info(f"Found {len(quarantine_items)} quarantined items")
            return quarantine_items

        except Exception as e:
            logger.error(f"Failed to list quarantined data: {e}")
            return []

    def get_quarantine_summary(self, days_back: int = 7) -> dict[str, Any]:
        """
        Get summary statistics of quarantined data.

        Args:
            days_back: Number of days to look back for summary

        Returns:
            Summary statistics dictionary
        """
        try:
            # For now, provide a simple summary based on listing
            # In production, this could be enhanced with more detailed analytics

            all_items = self.list_quarantined_data()

            summary = {
                "total_quarantined": len(all_items),
                "by_data_type": {},
                "recent_items": [],
                "summary_date": datetime.utcnow().isoformat(),
            }

            # Categorize by data type (extracted from key)
            for item in all_items:
                key_parts = item["key"].split("/")
                if len(key_parts) >= 5:  # quarantine/year=/month=/day=/type/
                    data_type = key_parts[4]
                    summary["by_data_type"][data_type] = (
                        summary["by_data_type"].get(data_type, 0) + 1
                    )

            # Get most recent items (up to 10)
            sorted_items = sorted(
                all_items, key=lambda x: x["last_modified"], reverse=True
            )
            summary["recent_items"] = sorted_items[:10]

            logger.info(
                f"Quarantine summary: {summary['total_quarantined']} total items"
            )
            return summary

        except Exception as e:
            logger.error(f"Failed to generate quarantine summary: {e}")
            return {
                "total_quarantined": 0,
                "by_data_type": {},
                "recent_items": [],
                "error": str(e),
                "summary_date": datetime.utcnow().isoformat(),
            }

    def should_quarantine(self, validation_result: dict[str, Any]) -> bool:
        """
        Determine if data should be quarantined based on validation result.

        Args:
            validation_result: Result from data validation

        Returns:
            True if data should be quarantined, False otherwise
        """
        # Quarantine if validation failed
        if not validation_result.get("valid", True):
            return True

        # Quarantine if there are critical issues (even if validation passed)
        issues = validation_result.get("issues", [])
        critical_keywords = ["schema", "missing", "inconsistent", "invalid"]

        for issue in issues:
            if any(keyword in issue.lower() for keyword in critical_keywords):
                return True

        return False
