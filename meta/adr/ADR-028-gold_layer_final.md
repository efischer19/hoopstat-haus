---
title: "ADR-028: Gold Layer Architecture and Serving Strategy (Final)"
status: "Accepted"
date: "2025-11-16"
supersedes: ["ADR-025", "ADR-026", "ADR-027"]
tags:
  - "data-architecture"
  - "gold-layer"
  - "storage"
  - "serving"
  - "spark-glue"
  - "manifests"
---

## Context

We iterated through multiple options for Gold-layer storage and serving (JSON-only MVP, S3 Tables/Iceberg, and public JSON artifacts). This created confusion about what we are shipping for v1 and why. We need one, clear decision that optimizes for simplicity, cost control, and fast delivery while leaving room for future enhancements.

## Decision

For v1:

- Internal storage
  - Bronze: JSON (raw landing, human-inspectable)
  - Silver: Parquet (partitioned; typed, analytics-friendly)
  - Gold (internal): Parquet (partitioned; produced by Spark jobs)

- Public serving (Gold presentation layer)
  - Pre-computed, small JSON artifacts (≤100KB) written to S3 under a `served/` prefix
  - Public read with CORS for browser/apps; optional CDN caching
  - JSON schemas versioned and documented; deterministic key layout (indexes for discovery)

- Orchestration & compute
  - Bronze→Silver: AWS Lambda triggered by Bronze `_metadata/summary.json` updates (simple daily coordination)
  - Silver→Gold: PySpark jobs on AWS Glue, orchestrated by EventBridge→Glue Workflow
  - S3→Lambda notifications are disabled by default for Silver→Gold in v1

- Discovery/catalog
  - Adopt ADR-024 lightweight manifest-based catalog (JSON manifests in S3) for dataset/schema/partition discovery
  - Defer Glue Data Catalog and Iceberg table catalogs for a later phase if/when needed (note: we are using AWS Glue for jobs/workflows now; the deferral is specifically about catalogs)

- Optional future enhancements (explicitly out-of-scope for v1)
  - Iceberg tables for Silver/Gold to enable ACID/time travel
  - Athena/Trino-based NL→SQL for ad-hoc queries via MCP
  - S3 Tables as an AWS-managed Iceberg control plane (gated; not required for public serving)

## Rationale

- Simplicity and speed: Spark/Glue + Parquet internally is a well-understood, low-friction path to robust transforms. JSON artifacts provide the simplest, fastest public interface.
- Cost control: Direct S3 GET of small JSONs keeps serving costs trivial; Glue runs only when we transform.
- Separation of concerns: Internal analytics storage vs public presentation artifacts are decoupled; we can evolve either independently.
- Future-ready: We can add Iceberg or a SQL endpoint later without breaking the public JSON contract.

### Why not Glue Data Catalog/Iceberg now?
- Scope fit (v1): We don’t need ad‑hoc SQL, time‑travel, or ACID right away; public JSON artifacts meet v1 product needs.
- Complexity/cost: Catalog setup (tables, crawlers or job DDL, permissions, governance) and Iceberg ops add cognitive/ops load pre‑v1.
- Simplicity for tests: ADR‑024 manifests give deterministic discovery for E2E and tooling without binding to a specific catalog engine.
- Single‑env strategy (ADR‑012): Keeps the runtime simple; we can add a catalog later if analytics/SQL needs emerge.
- Current infra note: Prior S3 Tables/Iceberg resources exist in Terraform from earlier exploration; per plan Task 29 these will be gated/disabled by default until we intentionally adopt a catalog.

## Consequences

### Positive
- Clear v1 contract for the frontend and external consumers (small, versioned JSON artifacts)
- Robust internal data model with Parquet and partitioning
- Minimal operational complexity (no long-lived servers; serverless batch transforms)
- Easy evolution toward Iceberg/SQL later if needed

### Negative
- No ad-hoc server-side SQL for v1 (by design)
- Requires discipline to keep JSON artifacts within size budgets and to maintain indexes

### Neutral
- S3 Tables/Iceberg remains an option; we intentionally defer it

## Scope and Non-Goals

- In scope (v1): Spark/Glue transforms (Silver→Gold); Parquet storage; JSON artifact publishing with schemas and indexes; manifest-based catalog; EventBridge→Glue orchestration (Silver→Gold); public read + CORS configuration.
- Out of scope (v1): Iceberg/Glue Catalog; Athena NL→SQL; S3 Tables-backed public serving.

## Implementation Notes

- Partitions
  - Silver: partition by `game_date` (consider `player_id` if beneficial)
  - Gold internal: partition by season/date/team_id/player_id to match access patterns

- JSON artifacts (examples)
  - `served/player_daily/{date}/{player_id}.json`
  - `served/team_daily/{date}/{team_id}.json`
  - `served/top_lists/{date}/{metric}.json`
  - `served/index/latest.json` and other discovery indices

- Manifests (ADR-024)
  - Generate dataset/schema/partition manifests at the end of each job
  - Use manifests for test discovery and tooling (no hardcoded paths)

- Orchestration
  - EventBridge on Silver readiness → Glue Workflow
  - Conditional job chaining Silver→Gold

## Migration and Clean-up

- Retain S3→Lambda trigger for Bronze→Silver via `_metadata/summary.json` updates
- Disable S3→Lambda notifications for Silver→Gold processing in v1
- Retain or remove Lambda prototypes behind tfvars; safe to delete post-v1
- Gate any S3 Tables resources by default; enable only if/when we adopt Iceberg formally

## Supersedes

- ADR-025 (JSON Storage for MVP): JSON remains only for Bronze and public artifacts; internal Silver/Gold use Parquet
- ADR-026 (S3 Tables for Gold): We are not using S3 Tables for public serving in v1
- ADR-027 (Stateless public JSON): Reaffirmed as the public serving layer, but clarified alongside internal Parquet, Spark/Glue, and manifests in one cohesive decision

## Success Criteria

- Public JSON endpoints fetched via S3/HTTPS with CORS in <100ms (cached)
- Spark jobs complete successfully end-to-end and publish manifests and artifacts
- E2E tests validate Silver/Gold internal Parquet and public JSON payloads
