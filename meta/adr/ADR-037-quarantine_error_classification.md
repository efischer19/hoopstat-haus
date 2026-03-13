---
title: "ADR-037: Quarantine Error Classification and Replay Strategy"
status: "Proposed"
date: "2026-03-13"
tags:
  - "data-pipeline"
  - "data-quality"
  - "operations"
---

## Context

* **Problem:** All quarantine records in the bronze ingestion layer look the same -- a list of validation issue strings with no structured categorization. A rounding mismatch where `sum(player_stats)` does not quite equal `team_stats` is indistinguishable from a schema-breaking API format change. This makes it difficult for operators to triage quarantined data and decide whether a record can be safely replayed or requires a code fix first.

* **Constraints:**
  - Classification must work with the existing `DataValidator` issues list format (list of human-readable strings) established in the bronze-ingestion app.
  - ADR-031 (file granularity) means quarantine records are per-entity, so classification applies at the individual record level.
  - ADR-028 (layer architecture) places quarantine in the bronze layer, before any transformation occurs.
  - ADR-022 (Click CLI) may be used for future replay commands that consume these classifications.
  - ADR-032 (S3 object key naming) applies to S3 keys but not JSON field names -- snake_case is the project standard for Python/JSON fields.

## Decision

**We introduce an `ErrorClassification` enum and a keyword-based classifier function to categorize every quarantine record by error type. The classification is stored in the quarantine record's metadata JSON as `error_classification`.**

### Error Taxonomy

Five classification values, ordered by severity (highest first):

1. **SCHEMA_CHANGE** -- Structural API format changes that require code updates before replay. Keywords: "schema", "unexpected field", "missing required", "format change".
2. **DATA_QUALITY** -- Missing fields, invalid ranges, or null values that indicate bad data. Keywords: "missing", "invalid", "out of range", "null".
3. **ROUNDING_MISMATCH** -- Player/team stat aggregation tolerance failures where sums do not precisely match. Keywords: "rounding", "sum", "mismatch", "tolerance", "aggregate".
4. **TRANSIENT** -- Network errors, temporary API issues that typically resolve on retry. Keywords: "timeout", "connection", "rate limit", "503", "502", "retry".
5. **UNKNOWN** -- Default when no heuristic matches.

### Classification Heuristics

The `classify_quarantine_error(validation_result)` function:
- Iterates over the `issues` list in the validation result.
- Performs case-insensitive keyword matching against each issue string.
- When multiple issue types are present, returns the most severe classification.
- Returns `UNKNOWN` when no keywords match or when the issues list is empty.

### Replay Lifecycle States

Quarantine records move through these conceptual states:

1. **Quarantined** -- Initial state when data fails validation. The `error_classification` field is set at this point.
2. **Replaying** -- An operator or automated process has initiated replay of the quarantined data.
3. **Resolved** -- Replay succeeded and the data passed validation.
4. **Failed** -- Replay was attempted but the data still fails validation.

Note: The lifecycle state tracking is defined here for future implementation. This ADR establishes the taxonomy; lifecycle state persistence is deferred to a follow-up ticket.

### Severity Ordering

When a quarantine record contains multiple issues spanning different classifications, the most severe classification wins: `SCHEMA_CHANGE > DATA_QUALITY > ROUNDING_MISMATCH > TRANSIENT > UNKNOWN`.

This ordering reflects operational priority -- schema changes require code fixes and block all replays, while transient errors can typically be resolved by simply retrying.

## Considered Options

1. **Keyword-based heuristic classification (Chosen):** Match issue strings against known keyword patterns to determine error type.
   * *Pros:* Simple to implement and extend; works with existing issue string format; no changes to upstream validators needed; easy to understand and debug.
   * *Cons:* Keyword matching can produce false positives (e.g., "missing" in "Missing required" vs "Missing player name"); requires maintenance as new issue patterns emerge.

2. **Structured error codes from validators:** Modify `DataValidator` to emit structured error codes instead of or alongside issue strings.
   * *Pros:* Precise classification with no ambiguity; machine-readable from the start.
   * *Cons:* Requires changes across all validation code paths; breaks existing validation result format; higher implementation cost for the same operational benefit.

3. **ML-based text classification:** Use a language model or text classifier to categorize issue strings.
   * *Pros:* Could handle novel issue patterns without keyword updates.
   * *Cons:* Massive over-engineering for this use case; introduces ML dependency; non-deterministic results; violates YAGNI principle.

## Consequences

* **Positive:**
  - Operators can instantly distinguish "just replay it" (TRANSIENT) from "fix the logic first" (SCHEMA_CHANGE) errors.
  - Automated replay systems can filter by classification to only replay TRANSIENT errors without human review.
  - Quarantine summary reports can aggregate by error type for trend analysis.
  - The severity ordering provides a clear triage priority.

* **Negative:**
  - Keyword-based matching requires ongoing maintenance as new validation messages are added.
  - The "missing" keyword appears in both SCHEMA_CHANGE ("missing required") and DATA_QUALITY ("missing") contexts; multi-word keywords are checked first to mitigate this, and the severity ordering ensures SCHEMA_CHANGE wins when both match.

* **Future Implications:**
  - A CLI replay command (via ADR-022 Click CLI) should accept `--classification` filters to selectively replay quarantined records.
  - Lifecycle state tracking (quarantined, replaying, resolved, failed) should be implemented as a follow-up, potentially using S3 object metadata or a lightweight state store.
  - If the keyword-based approach proves insufficient, migrating to structured error codes from validators is the recommended next step.
  - CloudWatch metrics and alarms could be set up per classification type (e.g., alert on SCHEMA_CHANGE spikes).
