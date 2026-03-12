# Ticket 05: Idempotency & State Management

## What do you want to build?

Ensure that the replay mechanism is fully idempotent: replaying a file that has already been successfully processed does not duplicate data downstream, and the quarantine state machine prevents invalid transitions (e.g., replaying an already-resolved record without an explicit `--force` flag).

This ticket also formalizes the quarantine record lifecycle and adds state-tracking metadata so operators can see the full history of a quarantine record's journey.

## Acceptance Criteria

- [ ] A quarantine record has a `status` field with valid states: `quarantined`, `replaying`, `resolved`, `failed`. State transitions are enforced:
  - `quarantined` -> `replaying` (replay initiated)
  - `replaying` -> `resolved` (Silver processing succeeded)
  - `replaying` -> `failed` (Silver processing failed)
  - `failed` -> `replaying` (retry initiated)
  - `resolved` -> `replaying` (only with `--force` flag; for re-processing after logic changes)
- [ ] Attempting to replay a record in `resolved` status without `--force` logs a warning and skips the file (no error, no duplicate processing).
- [ ] Attempting to replay a record in `replaying` status logs a warning about a concurrent replay and skips the file (guard against double-processing).
- [ ] When a replay writes data to the Bronze layer (`raw/{entity}/{date}/{id}.json`), it overwrites any existing file at that key -- the Bronze layer is the source of truth and S3 PutObject is inherently idempotent.
- [ ] When Silver processing runs for a replayed date, it processes all Bronze files for that date (including the restored one), producing a complete Silver output. The Silver layer's existing write pattern (overwrite per date partition) ensures no duplication.
- [ ] The quarantine record maintains an `attempts` list that logs each replay attempt with: timestamp, transform applied, result (resolved/failed), and error details (if failed).
- [ ] Unit tests verify: skip-on-resolved, skip-on-replaying, force-replay, state transitions, and the attempts audit trail.

## Implementation Notes (Optional)

**State storage:**
- The quarantine record already lives in S3 as a JSON file. Extend it with:
  ```json
  {
    "status": "quarantined",
    "attempts": [],
    "data": { ... },
    "validation_result": { ... },
    "metadata": { ... }
  }
  ```
- State transitions update the JSON in-place via S3 PutObject (overwrite).

**Idempotency guarantees:**
- **Bronze overwrite:** S3 PutObject is atomic and idempotent. Writing the same file twice produces identical results.
- **Silver overwrite:** The Silver processor writes output partitioned by date. Re-running for the same date replaces the output entirely. No append-only patterns to worry about.
- **Gold layer:** Not affected by this ticket. Gold is a downstream consumer of Silver and will pick up changes on its next run.

**Race condition mitigation:**
- The `replaying` state acts as a simple lock. The CLI sets `replaying` before starting and `resolved`/`failed` after completion.
- For the MVP, this is a best-effort advisory lock (no distributed locking). Acceptable because replay is an operator-initiated action, not an automated concurrent process.
- If distributed locking becomes necessary later, consider DynamoDB conditional writes or S3 object tagging with ETags.

**Backward compatibility:**
- Existing quarantine records (created before this ticket) won't have `status` or `attempts` fields. The replay CLI should treat missing `status` as `quarantined` and initialize `attempts` as an empty list on first replay.
