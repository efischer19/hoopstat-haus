# Ticket 1: Define `pipeline_health.json` Schema & Pydantic Models

**Title:** `feat: Define pipeline_health.json schema and Pydantic models`

**Labels:** `enhancement`

---

## What do you want to build?

Define the canonical schema for the `pipeline_health.json` artifact that the health dashboard will consume. This schema is the contract between the telemetry aggregator (backend) and the dashboard UI (frontend), so it must be defined first and shared via the `hoopstat-data` library.

The schema captures a rolling 7-day window of daily pipeline execution summaries across all three Medallion layers (Bronze, Silver, Gold), along with an overall system status indicator and data quality metrics.

### Proposed Schema Structure

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-03-26T06:00:00Z",
  "overall_status": "operational",
  "stages": {
    "bronze": {
      "status": "operational",
      "last_success_at": "2026-03-26T04:15:00Z"
    },
    "silver": {
      "status": "operational",
      "last_success_at": "2026-03-26T04:45:00Z"
    },
    "gold": {
      "status": "operational",
      "last_success_at": "2026-03-26T05:30:00Z"
    }
  },
  "daily_summaries": [
    {
      "date": "2026-03-26",
      "bronze": {
        "status": "success",
        "records_ingested": 450
      },
      "silver": {
        "status": "success",
        "records_processed": 448,
        "records_quarantined": 2,
        "quality_score": 0.996
      },
      "gold": {
        "status": "success",
        "artifacts_written": 312
      }
    }
  ]
}
```

### Implementation Details

- Add Pydantic models to `libs/hoopstat-data` alongside existing Silver and Gold models.
- Include strict field validation: status fields must be enums (`success`, `failed`, `skipped`, `no_data`), timestamps must be ISO 8601 UTC, counts must be non-negative integers, quality scores must be floats in [0.0, 1.0].
- Include a `schema_version` field (SemVer string) to support backward-compatible evolution per ADR-040.
- Overall status is derived: `operational` if all stages succeeded in the most recent run, `degraded` if any stage has quarantined records but completed, `outage` if any stage failed.
- The `daily_summaries` array contains up to 7 entries, ordered most-recent first.
- **Security:** The schema must NOT include fields for error messages, stack traces, internal identifiers, durations, or start times (per ADR-040 security constraints).

---

## Acceptance Criteria

- [ ] Pydantic models for `PipelineHealthReport`, `StageStatus`, `DailySummary`, `BronzeDailySummary`, `SilverDailySummary`, and `GoldDailySummary` are added to `libs/hoopstat-data`
- [ ] Status fields use a `PipelineStageStatus` string enum (`success`, `failed`, `skipped`, `no_data`)
- [ ] Overall status uses an `OverallSystemStatus` string enum (`operational`, `degraded`, `outage`)
- [ ] All models include comprehensive field validation (types, ranges, formats)
- [ ] A `schema_version` field is present and defaults to `"1.0.0"`
- [ ] Unit tests validate serialization/deserialization round-trips and edge cases (empty summaries, all-failed states, boundary quality scores)
- [ ] The data dictionary auto-generation script (`scripts/generate-data-dictionary.py`) picks up the new models

---

## Implementation Notes (Optional)

- Follow the existing model patterns in `libs/hoopstat-data/hoopstat_data/gold_models.py` for style and conventions.
- The `hoopstat-data` library uses heavy dependencies (pandas, fuzzywuzzy) in its `__init__.py`. The new health models should be importable without triggering those imports — consider placing them in a separate module (e.g., `health_models.py`) that can be imported directly.
- Reference ADR-040 (Static Pipeline Health Dashboard) for the security constraints that shaped this schema.
- This ticket has no infrastructure dependencies and can begin immediately.
