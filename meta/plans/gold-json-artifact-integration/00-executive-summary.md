# Gold Layer JSON Artifact Integration — Executive Summary

## Overview

The Gold analytics layer has a fully implemented `JSONArtifactWriter` module
(`apps/gold-analytics/app/json_artifacts.py`) that can generate and upload
player daily, team daily, top-list, and latest-index JSON artifacts to S3 under
the `served/` prefix. However, this writer is **not yet wired** into the
processor pipeline (`processors.py`). All four storage methods in
`GoldProcessor` currently log warnings instead of persisting data.

This epic connects the existing writer to the pipeline, adds the missing season
aggregation artifact format, implements the gold status health-check command,
and delivers the tests and documentation to close out the work.

## Relevant ADRs

| ADR | Title | Relevance |
|-----|-------|-----------|
| ADR-028 | Gold Layer Architecture (Final) | Defines `served/` prefix, JSON artifact ≤100 KB contract, cache strategy |
| ADR-038 | CloudFront Cache Tuning | 5-min index TTL vs 1-year immutable historical data |

No new ADR is proposed. The existing decisions in ADR-028 are sufficient to
guide this implementation — the JSON artifact writer already conforms to them.

## Current State

| Storage Method | Location | Status |
|---------------|----------|--------|
| `_store_player_analytics` | `processors.py` | Stub — logs warning |
| `_store_team_analytics` | `processors.py` | Stub — logs warning |
| `_store_season_aggregations` | `processors.py` | Stub — logs warning |
| `_store_team_season_aggregations` | `processors.py` | Stub — logs warning |
| `status` command | `main.py` | Stub — logs warning |

## Ticket Sequence

| # | Ticket | Effort | Dependencies |
|---|--------|--------|--------------|
| 01 | Wire daily artifact writing (player + team) | Low (2–3 h) | — |
| 02 | Wire top lists and latest index generation | Low (1–2 h) | 01 |
| 03 | Design and implement player season aggregation artifacts | Medium (3–4 h) | 01 |
| 04 | Design and implement team season aggregation artifacts | Medium (3–4 h) | 01 |
| 05 | Implement gold status command | Low (1–2 h) | 01 |
| 06 | Add JSON artifact integration tests | Medium (3–4 h) | 01–05 |
| 07 | Update gold analytics documentation | Low (1 h) | 01–06 |

**Total estimated effort:** 14–20 hours

## Risk & Notes

- The `JSONArtifactWriter` is already battle-tested by its own unit tests.
  Wiring it in is primarily a plumbing exercise.
- Season aggregation artifacts (tickets 03–04) require a new JSON schema and a
  new writer method. This is the only design work in the epic.
- Tickets 01–05 can largely be parallelized after ticket 01 lands, though
  ticket 06 (tests) should wait for all five.
