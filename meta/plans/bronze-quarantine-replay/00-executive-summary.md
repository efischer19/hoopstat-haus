# Bronze Data Quarantine & Replay Mechanism -- Executive Summary

## Overview

This epic builds a mechanism to rescue, review, and re-process failed or malformed NBA API responses currently trapped in the Bronze layer's quarantine. Today, quarantined data is stored in S3 (`quarantine/year={YYYY}/month={MM}/day={DD}/{type}/`) but there is no tooling to inspect, classify, or replay it. This work fills that gap, ensuring we don't permanently lose data due to transient API format changes, network hiccups, or known non-transient issues like stat rounding mismatches.

## Problem Statement

The Bronze ingestion pipeline (ADR-031) quarantines invalid API responses via the `DataQuarantine` class, preserving the original payload and validation errors in S3. However:

1. **No visibility** -- There is no CLI or tool to list quarantined files, view their errors, or understand why they failed.
2. **No classification** -- All quarantine errors are treated identically. Transient errors (network timeouts, temporary API format changes) look the same as non-transient errors (rounding mismatches where `sum(player_stats) != team_stats`). Operators cannot quickly distinguish "just replay it" from "fix the logic first."
3. **No replay path** -- There is no mechanism to take a quarantined file, optionally apply a transformation, and push it back through the Silver validation pipeline.
4. **No idempotency guarantee** -- If a replay succeeds, there is no formal process to mark the quarantine record as resolved or prevent duplicate data downstream.
5. **No CI/CD integration** -- Replay requires manual local execution; there is no GitHub Actions workflow for `workflow_dispatch`-triggered replays.

## Relevant ADRs

| ADR | Relevance |
|-----|-----------|
| ADR-007 | GitHub Actions for CI/CD and job scheduling (workflow_dispatch) |
| ADR-008 | Monorepo structure -- new tooling goes under `apps/` |
| ADR-015 | Structured JSON logging with standard fields |
| ADR-021 | Tenacity for retry logic and resilience |
| ADR-022 | Click for command-line interfaces |
| ADR-028 | Layer architecture: Bronze (JSON), Silver (Parquet), Gold (JSON artifacts) |
| ADR-031 | Bronze file granularity: one file per game, path `raw/{entity}/{YYYY-MM-DD}/{id}.json` |
| ADR-032 | S3 key naming: URL-safe characters only (`a-z`, `0-9`, `/`, `-`) |

## Proposed ADR

**ADR-036: Quarantine Error Classification and Replay Strategy** -- Establishes the taxonomy of quarantine error types (transient vs. non-transient), defines the replay contract (idempotent, auditable, transformation-aware), and codifies the quarantine lifecycle (quarantined -> replaying -> resolved/failed). See ticket `01-quarantine-error-classification.md`.

## Ticket Sequence

The work is broken into six sequenced tickets, each designed to be a small, independently verifiable unit:

| # | Ticket | Summary | Depends On |
|---|--------|---------|------------|
| 01 | [Quarantine Error Classification](01-quarantine-error-classification.md) | Define error taxonomy (transient vs. non-transient) and propose ADR-036 | -- |
| 02 | [Quarantine Review CLI](02-quarantine-review-cli.md) | Build a Click CLI to list, filter, and inspect quarantined payloads | 01 |
| 03 | [Replay Transformation Framework](03-replay-transformation-framework.md) | Create a pluggable transformation layer for patching quarantined data before replay | 01 |
| 04 | [Replay CLI & Silver Pipeline Integration](04-replay-cli-silver-integration.md) | Build the replay CLI command and wire it into the Silver validation pipeline | 02, 03 |
| 05 | [Idempotency & State Management](05-idempotency-state-management.md) | Ensure replayed files overwrite failed state without duplicating downstream data | 04 |
| 06 | [GitHub Actions Workflow for Replay](06-github-actions-replay-workflow.md) | Create a `workflow_dispatch` Action to trigger replay without local script execution | 04, 05 |

## Architecture Sketch

```
┌─────────────────────────────────────────────────────────────────┐
│                    Quarantine Review CLI                        │
│  (list / inspect / classify quarantined payloads)               │
└──────────────────────────┬──────────────────────────────────────┘
                           │ select file(s)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               Replay Transformation Framework                   │
│  (identity / rounding-tolerance / custom patch)                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │ transformed payload
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Replay CLI / GitHub Action                       │
│  (invoke Silver pipeline, track state, ensure idempotency)      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
     Silver Pipeline             Quarantine State
     (existing processing)       (resolved / failed)
```

## Out of Scope

- Automatic retry of transient errors at ingestion time (covered by ADR-021 Tenacity)
- Changes to the Gold layer pipeline
- Alerting or notification on new quarantine events (future work)
- Bulk historical backfill tooling
