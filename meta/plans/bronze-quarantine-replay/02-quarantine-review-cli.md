# Ticket 02: Quarantine Review CLI Tool

## What do you want to build?

Build a Click-based CLI tool (per ADR-022) that lets operators list, filter, and inspect quarantined payloads. The tool must clearly surface the timestamp, endpoint, validation error, and -- critically -- the error classification (from Ticket 01) so that transient errors are immediately distinguishable from non-transient issues like rounding mismatches.

This is the "read" side of the quarantine workflow. It builds on the existing `DataQuarantine.list_quarantined_data()` and `get_quarantine_summary()` methods but wraps them in a human-friendly CLI with filtering, formatting, and detail views.

## Acceptance Criteria

- [ ] A new Click command group `quarantine` is added to the bronze-ingestion CLI (`apps/bronze-ingestion/app/main.py`) with the following subcommands:
  - `quarantine list` -- Lists quarantined payloads with columns: date, data type, error classification, issue count, and S3 key.
  - `quarantine summary` -- Shows aggregate counts grouped by error classification and data type.
  - `quarantine inspect <s3-key>` -- Fetches and displays the full quarantine record for a specific file, including the original payload (truncated by default, `--full` flag for complete output), all validation issues, and metadata.
- [ ] `quarantine list` supports filtering flags: `--date YYYY-MM-DD`, `--type schedule|box_score`, `--classification transient|rounding_mismatch|schema_change|data_quality|unknown`.
- [ ] `quarantine summary` output clearly separates transient errors (safe to replay) from non-transient errors (require investigation), using visual indicators (e.g., color, icons, or labels).
- [ ] `quarantine list` supports `--output json` for machine-readable output (default is a human-readable table).
- [ ] All new CLI commands have `--help` documentation.
- [ ] Unit tests cover CLI output formatting, filtering logic, and error handling (e.g., S3 connectivity failure).

## Implementation Notes (Optional)

**CLI framework:** Use Click (ADR-022). Follow the existing CLI patterns in `apps/bronze-ingestion/app/main.py` which already uses Click with `@click.group()` and subcommands.

**Display library:** Consider `rich` or `tabulate` for table formatting, but only if already in the dependency tree. Otherwise, simple formatted strings are sufficient per the development philosophy (YAGNI, minimize dependencies).

**Key integration points:**
- `DataQuarantine.list_quarantined_data(start_date, end_date, data_type)` -- already exists, returns S3 object metadata
- `DataQuarantine.get_quarantine_summary()` -- already exists, returns type-grouped counts
- S3 `get_object()` for `quarantine inspect` to fetch full record content

**Classification display:**
- Transient errors should be labeled clearly, e.g., `[REPLAY-SAFE] TRANSIENT`
- Rounding mismatches should be labeled, e.g., `[INVESTIGATE] ROUNDING_MISMATCH`
- Schema changes should be labeled, e.g., `[INVESTIGATE] SCHEMA_CHANGE`

**Structured logging:** All CLI operations should log per ADR-015 patterns.

**Testing approach:** Use Click's `CliRunner` for integration testing. Mock S3 calls with the existing test patterns from `test_quarantine.py`.
