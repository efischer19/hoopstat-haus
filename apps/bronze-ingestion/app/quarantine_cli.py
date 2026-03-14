"""
CLI commands for reviewing quarantined data.

Provides commands to list, summarize, and inspect quarantined payloads
from the bronze layer ingestion pipeline.
"""

import json
import sys
from datetime import datetime
from typing import Any

import click
from hoopstat_observability import get_logger

from .quarantine import DataQuarantine, ErrorClassification
from .replay import (
    BatchReplayResult,
    ReplayOrchestrator,
    ReplayResult,
    get_transform_by_name,
)
from .s3_manager import BronzeS3Manager

logger = get_logger(__name__)

# Classification display labels
_CLASSIFICATION_LABELS = {
    ErrorClassification.TRANSIENT: "[REPLAY-SAFE] TRANSIENT",
    ErrorClassification.ROUNDING_MISMATCH: "[INVESTIGATE] ROUNDING_MISMATCH",
    ErrorClassification.SCHEMA_CHANGE: "[INVESTIGATE] SCHEMA_CHANGE",
    ErrorClassification.DATA_QUALITY: "[INVESTIGATE] DATA_QUALITY",
    ErrorClassification.UNKNOWN: "[INVESTIGATE] UNKNOWN",
}

# Valid classification filter values
_VALID_CLASSIFICATIONS = [c.value for c in ErrorClassification]

# Valid data type filter values
_VALID_DATA_TYPES = ["schedule", "box_score"]


def _get_quarantine() -> DataQuarantine:
    """Create a DataQuarantine instance with default S3 configuration."""
    s3_manager = BronzeS3Manager()
    return DataQuarantine(s3_manager)


def _format_classification(classification_value: str) -> str:
    """Format an error classification value for display."""
    try:
        classification = ErrorClassification(classification_value)
        return _CLASSIFICATION_LABELS[classification]
    except ValueError:
        return f"[INVESTIGATE] {classification_value.upper()}"


def _is_transient(classification_value: str) -> bool:
    """Check if a classification represents a transient (replay-safe) error."""
    return classification_value == ErrorClassification.TRANSIENT.value


def _parse_date_from_key(key: str) -> str:
    """Extract date from an S3 quarantine key path."""
    parts = key.split("/")
    year = month = day = "?"
    for part in parts:
        if part.startswith("year="):
            year = part.split("=")[1]
        elif part.startswith("month="):
            month = part.split("=")[1].zfill(2)
        elif part.startswith("day="):
            day = part.split("=")[1].zfill(2)
    return f"{year}-{month}-{day}"


def _parse_data_type_from_key(key: str) -> str:
    """Extract data type from an S3 quarantine key path."""
    parts = key.split("/")
    # Key format: quarantine/year=YYYY/month=MM/day=DD/data_type/filename.json
    if len(parts) >= 5:
        return parts[4]
    return "unknown"


def _fetch_record(quarantine: DataQuarantine, key: str) -> dict[str, Any] | None:
    """Fetch and parse a quarantine record from S3."""
    try:
        response = quarantine.s3_manager.s3_client.get_object(
            Bucket=quarantine.s3_manager.bucket_name,
            Key=key,
        )
        body = response["Body"].read().decode("utf-8")
        return json.loads(body)
    except Exception as e:
        logger.error(f"Failed to fetch quarantine record {key}: {e}")
        return None


def _enrich_items(
    quarantine: DataQuarantine, items: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Enrich quarantine list items with classification and issue count."""
    enriched = []
    for item in items:
        record = _fetch_record(quarantine, item["key"])
        metadata = record.get("metadata", {}) if record else {}
        enriched.append(
            {
                **item,
                "date": _parse_date_from_key(item["key"]),
                "data_type": _parse_data_type_from_key(item["key"]),
                "error_classification": metadata.get("error_classification", "unknown"),
                "issues_count": metadata.get("issues_count", 0),
            }
        )
    return enriched


def _format_table(items: list[dict[str, Any]]) -> str:
    """Format enriched quarantine items as a human-readable table."""
    if not items:
        return "No quarantined items found."

    # Column headers and widths
    headers = ["Date", "Data Type", "Classification", "Issues", "S3 Key"]
    rows = []
    for item in items:
        rows.append(
            [
                item["date"],
                item["data_type"],
                _format_classification(item["error_classification"]),
                str(item["issues_count"]),
                item["key"],
            ]
        )

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    # Build table
    separator = "  "
    header_line = separator.join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    divider = separator.join("-" * w for w in col_widths)

    lines = [header_line, divider]
    for row in rows:
        lines.append(
            separator.join(cell.ljust(col_widths[i]) for i, cell in enumerate(row))
        )

    return "\n".join(lines)


def _format_summary(
    summary: dict[str, Any], enriched_items: list[dict[str, Any]]
) -> str:
    """Format quarantine summary for display."""
    lines = []
    lines.append("Quarantine Summary")
    lines.append("=" * 60)
    lines.append(f"Total quarantined: {summary['total_quarantined']}")
    lines.append(f"Summary date: {summary['summary_date']}")
    lines.append("")

    # Group by classification
    by_classification: dict[str, int] = {}
    for item in enriched_items:
        cls = item.get("error_classification", "unknown")
        by_classification[cls] = by_classification.get(cls, 0) + 1

    # Separate transient from non-transient
    transient_count = by_classification.pop(ErrorClassification.TRANSIENT.value, 0)
    non_transient_total = sum(by_classification.values())

    lines.append("By Error Classification:")
    lines.append("-" * 40)

    if transient_count > 0:
        label = _format_classification(ErrorClassification.TRANSIENT.value)
        lines.append(f"  {label}: {transient_count}")

    for cls_value, count in sorted(by_classification.items()):
        label = _format_classification(cls_value)
        lines.append(f"  {label}: {count}")

    lines.append("")
    lines.append(f"  Replay-safe (transient): {transient_count}")
    lines.append(f"  Requires investigation:  {non_transient_total}")
    lines.append("")

    # By data type
    if summary.get("by_data_type"):
        lines.append("By Data Type:")
        lines.append("-" * 40)
        for data_type, count in sorted(summary["by_data_type"].items()):
            lines.append(f"  {data_type}: {count}")

    return "\n".join(lines)


def _format_inspect(record: dict[str, Any], full: bool) -> str:
    """Format a quarantine record for detailed inspection."""
    lines = []
    metadata = record.get("metadata", {})

    lines.append("Quarantine Record Details")
    lines.append("=" * 60)

    # Metadata section
    lines.append("")
    lines.append("Metadata:")
    lines.append("-" * 40)
    lines.append(f"  Data type:            {metadata.get('data_type', 'N/A')}")
    lines.append(f"  Target date:          {metadata.get('target_date', 'N/A')}")
    lines.append(
        f"  Quarantine timestamp: {metadata.get('quarantine_timestamp', 'N/A')}"
    )
    cls_value = metadata.get("error_classification", "unknown")
    lines.append(f"  Error classification: {_format_classification(cls_value)}")
    lines.append(f"  Issues count:         {metadata.get('issues_count', 0)}")
    lines.append(f"  Validation valid:     {metadata.get('validation_valid', 'N/A')}")

    # Context
    context = metadata.get("context", {})
    if context:
        lines.append("")
        lines.append("Context:")
        lines.append("-" * 40)
        for key, value in context.items():
            lines.append(f"  {key}: {value}")

    # Validation issues
    validation_result = record.get("validation_result", {})
    issues = validation_result.get("issues", [])
    lines.append("")
    lines.append("Validation Issues:")
    lines.append("-" * 40)
    if issues:
        for i, issue in enumerate(issues, 1):
            lines.append(f"  {i}. {issue}")
    else:
        lines.append("  No issues recorded.")

    # Original payload
    data = record.get("data")
    lines.append("")
    lines.append("Original Payload:")
    lines.append("-" * 40)
    if data is not None:
        payload_str = json.dumps(data, default=str, indent=2)
        if not full and len(payload_str) > 500:
            lines.append(payload_str[:500])
            lines.append(f"  ... (truncated, {len(payload_str)} chars total)")
            lines.append("  Use --full to see complete payload.")
        else:
            lines.append(payload_str)
    else:
        lines.append("  No payload data recorded.")

    return "\n".join(lines)


@click.group()
def quarantine() -> None:
    """Review and inspect quarantined data from the bronze ingestion pipeline."""
    pass


@quarantine.command("list")
@click.option(
    "--date",
    "filter_date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Filter by date (YYYY-MM-DD).",
)
@click.option(
    "--type",
    "filter_type",
    type=click.Choice(_VALID_DATA_TYPES, case_sensitive=False),
    default=None,
    help="Filter by data type.",
)
@click.option(
    "--classification",
    "filter_classification",
    type=click.Choice(_VALID_CLASSIFICATIONS, case_sensitive=False),
    default=None,
    help="Filter by error classification.",
)
@click.option(
    "--output",
    "output_format",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    help="Output format (default: table).",
)
def quarantine_list(
    filter_date: datetime | None,
    filter_type: str | None,
    filter_classification: str | None,
    output_format: str,
) -> None:
    """List quarantined payloads with filtering options."""
    logger.info(
        "Listing quarantined data",
        extra={
            "filter_date": filter_date.isoformat() if filter_date else None,
            "filter_type": filter_type,
            "filter_classification": filter_classification,
            "output_format": output_format,
        },
    )

    try:
        q = _get_quarantine()
        target_date = filter_date.date() if filter_date else None
        items = q.list_quarantined_data(target_date=target_date, data_type=filter_type)

        if not items:
            click.echo("No quarantined items found.")
            return

        enriched = _enrich_items(q, items)

        # Apply classification filter (post-fetch since it requires record content)
        if filter_classification:
            enriched = [
                item
                for item in enriched
                if item["error_classification"] == filter_classification
            ]

        if not enriched:
            click.echo("No quarantined items match the specified filters.")
            return

        if output_format == "json":
            click.echo(json.dumps(enriched, default=str, indent=2))
        else:
            click.echo(_format_table(enriched))

    except Exception as e:
        logger.error(f"Failed to list quarantined data: {e}")
        click.echo(f"Error: Failed to list quarantined data: {e}", err=True)
        sys.exit(1)


@quarantine.command("summary")
def quarantine_summary() -> None:
    """Show aggregate counts of quarantined data by classification and type."""
    logger.info("Generating quarantine summary")

    try:
        q = _get_quarantine()
        summary = q.get_quarantine_summary()

        if summary.get("error"):
            click.echo(
                f"Error: Failed to generate summary: {summary['error']}", err=True
            )
            sys.exit(1)

        items = q.list_quarantined_data()
        enriched = _enrich_items(q, items)

        click.echo(_format_summary(summary, enriched))

    except Exception as e:
        logger.error(f"Failed to generate quarantine summary: {e}")
        click.echo(f"Error: Failed to generate quarantine summary: {e}", err=True)
        sys.exit(1)


@quarantine.command("inspect")
@click.argument("s3_key")
@click.option(
    "--full",
    is_flag=True,
    default=False,
    help="Show complete payload without truncation.",
)
def quarantine_inspect(s3_key: str, full: bool) -> None:
    """Fetch and display the full quarantine record for a specific S3 key."""
    logger.info("Inspecting quarantine record", extra={"s3_key": s3_key})

    try:
        q = _get_quarantine()
        record = _fetch_record(q, s3_key)

        if record is None:
            click.echo(f"Error: Could not fetch quarantine record: {s3_key}", err=True)
            sys.exit(1)

        click.echo(_format_inspect(record, full))

    except Exception as e:
        logger.error(f"Failed to inspect quarantine record: {e}")
        click.echo(f"Error: Failed to inspect quarantine record: {e}", err=True)
        sys.exit(1)


def _get_replay_orchestrator(
    silver_processing_dir: str | None = None,
) -> ReplayOrchestrator:
    """Create a ReplayOrchestrator with default configuration."""
    s3_manager = BronzeS3Manager()
    quarantine_instance = DataQuarantine(s3_manager)
    return ReplayOrchestrator(
        s3_manager=s3_manager,
        quarantine=quarantine_instance,
        silver_processing_dir=silver_processing_dir,
    )


def _format_replay_result(result: ReplayResult) -> str:
    """Format a single replay result for display."""
    status = "OK" if result.success else "FAILED"
    if result.dry_run:
        status = "DRY-RUN OK"
    line = f"  [{status}] {result.s3_key}"
    if result.transform_applied:
        line += f"  (transform: {result.transform_applied})"
    if result.error:
        line += f"\n         Error: {result.error}"
    return line


def _format_batch_summary(batch_result: BatchReplayResult) -> str:
    """Format a batch replay summary for display."""
    lines = []
    lines.append("")
    lines.append("Replay Summary")
    lines.append("=" * 60)
    lines.append(f"Total:     {batch_result.total}")
    lines.append(f"Succeeded: {batch_result.succeeded}")
    lines.append(f"Failed:    {batch_result.failed}")
    lines.append("")
    lines.append("Details:")
    lines.append("-" * 40)
    for result in batch_result.results:
        lines.append(_format_replay_result(result))
    return "\n".join(lines)


@quarantine.command("replay")
@click.argument("s3_key", required=False, default=None)
@click.option(
    "--classification",
    "filter_classification",
    type=click.Choice(_VALID_CLASSIFICATIONS, case_sensitive=False),
    default=None,
    help="Replay all quarantined files matching a classification.",
)
@click.option(
    "--date",
    "filter_date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Replay all quarantined files for a specific date (YYYY-MM-DD).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Validate the transformation and show what would happen without writing.",
)
@click.option(
    "--transform",
    "transform_name",
    type=str,
    default=None,
    help="Override the default transform (e.g., 'identity', 'rounding_tolerance').",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force replay of already-resolved records.",
)
def quarantine_replay(
    s3_key: str | None,
    filter_classification: str | None,
    filter_date: datetime | None,
    dry_run: bool,
    transform_name: str | None,
    force: bool,
) -> None:
    """Replay quarantined data through the Bronze-to-Silver pipeline.

    Provide an S3_KEY to replay a single file, or use --classification
    or --date to replay matching files in batch.
    """
    # Validate that at least one selection method is provided
    if s3_key is None and filter_classification is None and filter_date is None:
        click.echo(
            "Error: Provide an S3 key argument, or use --classification "
            "or --date to select files.",
            err=True,
        )
        sys.exit(1)

    logger.info(
        "Starting quarantine replay",
        extra={
            "s3_key": s3_key,
            "classification": filter_classification,
            "date": filter_date.date().isoformat() if filter_date else None,
            "dry_run": dry_run,
            "force": force,
            "transform": transform_name,
        },
    )

    try:
        # Resolve transform override
        transform_override = None
        if transform_name:
            try:
                transform_override = get_transform_by_name(transform_name)
            except ValueError as e:
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)

        orchestrator = _get_replay_orchestrator()

        if s3_key:
            # Single-file replay
            result = orchestrator.replay_single(
                s3_key,
                transform_override=transform_override,
                dry_run=dry_run,
                force=force,
            )
            click.echo(_format_replay_result(result))
            if not result.success:
                sys.exit(1)
        else:
            # Batch replay -- collect matching items
            q = orchestrator.quarantine
            target_date = filter_date.date() if filter_date else None
            items = q.list_quarantined_data(target_date=target_date)

            if not items:
                click.echo("No quarantined items found matching the criteria.")
                return

            # Apply classification filter if specified
            if filter_classification:
                enriched = _enrich_items(q, items)
                items = [
                    item
                    for item in enriched
                    if item["error_classification"] == filter_classification
                ]
                if not items:
                    click.echo(
                        "No quarantined items match the specified classification."
                    )
                    return

            batch_result = orchestrator.replay_batch(
                items,
                transform_override=transform_override,
                dry_run=dry_run,
                force=force,
            )
            click.echo(_format_batch_summary(batch_result))
            if batch_result.failed > 0:
                sys.exit(1)

    except Exception as e:
        logger.error(f"Replay failed: {e}")
        click.echo(f"Error: Replay failed: {e}", err=True)
        sys.exit(1)
