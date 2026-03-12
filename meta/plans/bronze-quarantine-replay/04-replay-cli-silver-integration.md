# Ticket 04: Replay CLI & Silver Pipeline Integration

## What do you want to build?

Build the replay CLI command and wire it into the existing Silver validation pipeline. This is the core "replay" action: take one or more quarantined files, optionally apply a transformation (from Ticket 03), and push the result through Silver processing. On success, the data enters the Silver layer; on failure, it remains quarantined with updated error information.

This ticket connects the review tooling (Ticket 02) with the transformation framework (Ticket 03) and the existing Silver processing pipeline (`apps/silver-processing/`).

## Acceptance Criteria

- [ ] A new `quarantine replay` Click subcommand is added to the bronze-ingestion CLI with the following interface:
  - `quarantine replay <s3-key>` -- Replay a single quarantined file.
  - `quarantine replay --classification <type>` -- Replay all quarantined files matching a classification (e.g., all transient errors).
  - `quarantine replay --date <YYYY-MM-DD>` -- Replay all quarantined files for a specific date.
  - `quarantine replay --dry-run` -- Validate the transformation and show what would happen without writing to Silver.
  - `quarantine replay --transform <name>` -- Override the default transform for the classification (e.g., use `identity` instead of the default).
- [ ] The replay command performs these steps in order:
  1. Fetch the quarantine record from S3
  2. Apply the appropriate transform (or the overridden one)
  3. Write the transformed payload to the correct Bronze location (`raw/{entity}/{date}/{id}.json`) so the Silver pipeline can pick it up
  4. Invoke the Silver validation pipeline for the affected date(s)
  5. Report success or failure with details
- [ ] On successful replay, the quarantine record's metadata is updated with `replay_status: "resolved"`, `replay_timestamp`, and `transform_applied`.
- [ ] On failed replay, the quarantine record's metadata is updated with `replay_status: "failed"`, `replay_timestamp`, `replay_error`, and the retry count is incremented.
- [ ] Batch replay (by classification or date) processes files sequentially with a summary report at the end showing success/failure counts.
- [ ] All replay operations emit structured JSON logs per ADR-015.
- [ ] Unit tests cover single-file replay, batch replay, dry-run mode, transform override, and failure handling.

## Implementation Notes (Optional)

**Replay flow (detailed):**

```
quarantine replay <s3-key>
    │
    ├─ Fetch quarantine record from S3
    ├─ Determine error classification (from record metadata)
    ├─ Select transform (default for classification, or --transform override)
    ├─ Apply transform to original payload
    │    ├─ Success: continue
    │    └─ TransformError: mark as failed, log, exit
    ├─ Write transformed payload to Bronze path
    │    └─ Path: raw/{entity}/{date}/{id}.json (per ADR-031)
    ├─ Invoke Silver processing for the date
    │    └─ Reuse BronzeToSilverProcessor from apps/silver-processing
    ├─ Check Silver processing result
    │    ├─ Success: update quarantine record (resolved)
    │    └─ Failure: update quarantine record (failed, increment retry)
    └─ Log result
```

**Silver pipeline integration:**
- Import and invoke `BronzeToSilverProcessor` from `apps/silver-processing/app/processors.py`
- This may require extracting the processor into a shared library (`libs/`) or using it as a subprocess call. Evaluate trade-offs:
  - **Direct import** -- tighter coupling but simpler; may require adding `apps/silver-processing` as a path dependency
  - **Subprocess** -- looser coupling; invoke via `poetry run python -m app.main process --date <date>` in the silver-processing directory
  - Recommendation: start with subprocess invocation to maintain app boundary separation (per ADR-008 monorepo structure)

**S3 key construction for restored Bronze data:**
- Extract `entity` and `date` from the quarantine record's metadata
- For box scores: `raw/box/{date}/{game_id}.json` (per ADR-031)
- For schedules: `raw/sched/{date}/games.json`
- Ensure URL-safe characters only (per ADR-032)

**Concurrency:** Process files sequentially for the initial implementation. Parallel processing can be added later if batch sizes warrant it (YAGNI).
