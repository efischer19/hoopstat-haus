# Ticket 01: Quarantine Error Classification System

## What do you want to build?

Define a formal taxonomy of quarantine error types so that operators can instantly distinguish transient errors ("just replay it") from non-transient errors ("fix the logic first"). Implement this classification in the existing `DataQuarantine` class and propose ADR-036 to codify the decision.

Currently, all quarantine records look the same -- a list of validation issue strings. The rounding mismatch where `sum(player_stats)` does not quite equal `team_stats` is indistinguishable from a schema-breaking API format change. This ticket introduces an `ErrorClassification` enum and a classifier function that tags each quarantine record.

## Acceptance Criteria

- [ ] An `ErrorClassification` enum is added to the bronze-ingestion app with at least these values: `TRANSIENT` (network errors, temporary API issues), `ROUNDING_MISMATCH` (player/team stat aggregation tolerance failures), `SCHEMA_CHANGE` (structural API format changes), `DATA_QUALITY` (missing fields, invalid ranges), and `UNKNOWN`.
- [ ] A `classify_quarantine_error(validation_result)` function exists that inspects the validation issues list and returns the appropriate `ErrorClassification`.
- [ ] The `DataQuarantine.quarantine_data()` method is updated to include the classification in the stored quarantine record's metadata (field: `error_classification`).
- [ ] Unit tests cover each classification path, including edge cases where multiple issue types are present (the most severe classification wins).
- [ ] ADR-036 is proposed (status: `Proposed`) documenting the error taxonomy, the classification heuristics, and the replay lifecycle states (quarantined, replaying, resolved, failed).
- [ ] Existing quarantine tests continue to pass without modification.

## Implementation Notes (Optional)

**Error classification heuristics (starting point):**

- `TRANSIENT`: Issue strings containing keywords like "timeout", "connection", "rate limit", "503", "502", "retry".
- `ROUNDING_MISMATCH`: Issue strings containing "rounding", "sum", "mismatch", "tolerance", "aggregate", or custom cross-entity validation checks added in this ticket.
- `SCHEMA_CHANGE`: Issue strings containing "schema", "unexpected field", "missing required", "format change".
- `DATA_QUALITY`: Issue strings containing "missing", "invalid", "out of range", "null".
- `UNKNOWN`: Default when no heuristic matches.

**Severity ordering** (for multi-issue records): `SCHEMA_CHANGE` > `DATA_QUALITY` > `ROUNDING_MISMATCH` > `TRANSIENT` > `UNKNOWN`.

**ADR-036 scope:**
- Title: "Quarantine Error Classification and Replay Strategy"
- Tags: `data-pipeline`, `data-quality`, `operations`
- Should reference ADR-031 (file granularity), ADR-028 (layer architecture), and ADR-022 (Click CLI)

**Relevant code:**
- `apps/bronze-ingestion/app/quarantine.py` -- `should_quarantine()` and `quarantine_data()` methods
- `apps/bronze-ingestion/app/validation.py` -- `DataValidator` issues list format
- `apps/bronze-ingestion/tests/test_quarantine.py` -- existing test patterns
