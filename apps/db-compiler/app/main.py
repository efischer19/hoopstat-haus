"""
CLI entry point for the db-compiler application.

Usage examples::

    # Compile both formats from a local directory of Gold JSON artifacts
    poetry run compile --local-dir ./test-data/ --output-dir /tmp/db/

    # Compile from an S3 bucket (requires AWS credentials)
    poetry run compile --s3-bucket hoopstat-haus-gold --output-dir /tmp/db/

    # Compile only DuckDB format
    poetry run compile --local-dir ./test-data/ --output-dir /tmp/db/ --format duckdb

    # Dry run — discover and report artifact counts without writing databases
    poetry run compile --local-dir ./test-data/ --dry-run
"""

import logging
import os
import sys

import click

from app.compiler import DUCKDB_FILENAME, SQLITE_FILENAME, compile_databases
from app.fetcher import load_from_local_dir, load_from_s3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--output-dir",
    required=False,
    default=None,
    help="Directory for the compiled .duckdb / .sqlite output files.",
)
@click.option(
    "--local-dir",
    default=None,
    help=(
        "Load Gold artifacts from a local directory instead of S3.  "
        "The directory must mirror the S3 served/ key structure."
    ),
)
@click.option(
    "--s3-bucket",
    default=None,
    envvar="GOLD_BUCKET",
    help="S3 bucket containing served/ Gold artifacts.  "
    "Can also be set via the GOLD_BUCKET environment variable.",
)
@click.option(
    "--base-url",
    default="https://data.hoopstat.haus",
    show_default=True,
    help="CloudFront base URL (informational; S3 or local-dir is used for fetching).",
)
@click.option(
    "--season",
    default=None,
    help=(
        "Restrict season-level artifact loading to a specific season "
        "(e.g. '2024-25').  Daily artifacts are always loaded in full."
    ),
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["duckdb", "sqlite", "both"]),
    default="both",
    show_default=True,
    help="Which database format(s) to compile.",
)
@click.option(
    "--aws-region",
    default="us-east-1",
    show_default=True,
    help="AWS region for the S3 client (S3 mode only).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Discover and report artifacts without writing any database files.",
)
def main(
    output_dir: str | None,
    local_dir: str | None,
    s3_bucket: str | None,
    base_url: str,
    season: str | None,
    fmt: str,
    aws_region: str,
    dry_run: bool,
) -> None:
    """Compile Gold JSON artifacts into DuckDB and/or SQLite databases.

    Loads Gold-layer JSON artifacts once from the specified source and writes
    them into both a DuckDB file and a SQLite file (the "load once, write
    twice" pattern).

    At least one of --local-dir or --s3-bucket must be provided (or the
    GOLD_BUCKET environment variable must be set), unless --dry-run is used
    with --local-dir.
    """
    # ---------------------------------------------------------------------------
    # 1. Determine data source and load artifacts
    # ---------------------------------------------------------------------------
    if local_dir:
        click.echo(f"Loading Gold artifacts from local directory: {local_dir}")
        dataset = load_from_local_dir(local_dir)
    else:
        bucket = s3_bucket or os.environ.get("GOLD_BUCKET")
        if not bucket:
            click.echo(
                "Error: specify --local-dir or --s3-bucket "
                "(or set the GOLD_BUCKET environment variable).",
                err=True,
            )
            sys.exit(1)
        click.echo(f"Loading Gold artifacts from S3 bucket: {bucket}")
        dataset = load_from_s3(bucket, season=season, aws_region=aws_region)

    # ---------------------------------------------------------------------------
    # 2. Report what was discovered
    # ---------------------------------------------------------------------------
    click.echo(dataset.summary())

    if dry_run:
        click.echo("Dry run complete — no database files written.")
        return

    # ---------------------------------------------------------------------------
    # 3. Require --output-dir for actual compilation
    # ---------------------------------------------------------------------------
    if not output_dir:
        click.echo(
            "Error: --output-dir is required when not using --dry-run.", err=True
        )
        sys.exit(1)

    # ---------------------------------------------------------------------------
    # 4. Resolve requested formats
    # ---------------------------------------------------------------------------
    formats = ["duckdb", "sqlite"] if fmt == "both" else [fmt]

    click.echo(f"Compiling {', '.join(formats)} database(s) → {output_dir}/ ...")

    # ---------------------------------------------------------------------------
    # 5. Compile (write + validate)
    # ---------------------------------------------------------------------------
    results = compile_databases(dataset, output_dir, formats=formats)

    # ---------------------------------------------------------------------------
    # 6. Report validation results
    # ---------------------------------------------------------------------------
    any_failure = False
    for format_name, validation in results.items():
        filename = DUCKDB_FILENAME if format_name == "duckdb" else SQLITE_FILENAME
        status = "✓ PASS" if validation.failed == 0 else "✗ FAIL"
        click.echo(
            f"\n[{format_name.upper()}] {filename}  —  "
            f"{validation.passed} checks passed, {validation.failed} failed  {status}"
        )
        for check in validation.checks:
            icon = "  ✓" if check.status == "pass" else "  ✗"
            detail = (
                f"{check.value} rows" if check.value is not None else check.error or ""
            )
            click.echo(f"{icon}  {check.name}: {detail}")

        if validation.failed > 0:
            any_failure = True

    # Cross-format count parity summary
    if "duckdb" in results and "sqlite" in results:
        duck_counts = results["duckdb"].table_counts()
        sqlite_counts = results["sqlite"].table_counts()
        parity_ok = all(duck_counts.get(t) == sqlite_counts.get(t) for t in duck_counts)
        parity_icon = "✓" if parity_ok else "✗"
        click.echo(f"\n[PARITY]  DuckDB ↔ SQLite record counts match: {parity_icon}")
        if not parity_ok:
            any_failure = True

    if any_failure:
        click.echo("\nCompilation completed with validation failures.", err=True)
        sys.exit(1)
    else:
        click.echo("\nCompilation successful.")
