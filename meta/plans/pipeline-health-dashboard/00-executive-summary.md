# Pipeline Health & Observability Dashboard — Epic Plan

**Status:** Planning
**Date:** 2026-03-26
**Author:** AI Contributor
**Epic Issue:** Public Operational Health & Pipeline Observability Dashboard

## Executive Summary

This epic delivers a **public, unauthenticated health dashboard** that exposes the operational status of the Hoopstat Haus Bronze → Silver → Gold data pipeline. The dashboard consumes a static `pipeline_health.json` artifact generated daily by a lightweight aggregator Lambda, following the project's established static-first architecture (ADR-027) and near-zero-cost principles (ADR-030).

The dashboard enables data consumers — developers, AI agents, and frontend users — to instantly verify pipeline freshness, identify degraded states, and confirm data quality without requiring AWS console access or authentication.

## Motivation

| Problem | Impact |
|---------|--------|
| Pipeline telemetry is locked inside AWS CloudWatch | Consumers cannot verify if today's data is fresh or stale |
| Silver quarantine states are invisible externally | Downstream failures are misattributed to consumer code |
| No public signal for pipeline outages | Developers waste time debugging their integrations when the issue is upstream |

## Architectural Approach

This epic follows a **Static Generation Pattern** consistent with ADR-027 (Stateless Gold Access via JSON Artifacts):

```
CloudWatch Logs ─┐
S3 Inventory ────┤  Aggregator    pipeline_health.json    Static HTML/JS
Quarantine Logs ─┘  Lambda ──────► S3 (served/) ──────────► Dashboard UI
                     (daily)       CloudFront CDN           (Chart.js)
```

1. **Aggregator Lambda** — A Python Lambda triggered after Gold processing completes. Queries CloudWatch, S3 inventory, and quarantine logs. Compiles a single, sanitized JSON artifact.
2. **Static JSON Artifact** — `pipeline_health.json` is written to the Gold S3 bucket under `served/health/` with a 1-hour cache TTL, following existing CloudFront cache behavior patterns (ADR-038).
3. **Static Dashboard UI** — A vanilla HTML/JS page (per ADR-019) using Chart.js (per ADR-036) to render status indicators and data quality trends. Hosted alongside the existing frontend.

## Security Constraints

All sub-tickets must enforce these invariants (detailed in proposed ADR-040):

- **No live backend queries** — The dashboard fetches only the static JSON file. Zero direct access to AWS APIs from the browser.
- **Strict log sanitization** — No stack traces, IAM role names, internal IPs, bucket names, or error messages in the public JSON.
- **No secrets exposure** — The aggregator must filter any tokens, keys, or credentials that appear in CloudWatch logs.
- **Obfuscated execution windows** — Publish completion timestamps only; never publish start times or durations that reveal infrastructure spin-up patterns.

## Relevant ADRs

| ADR | Relevance |
|-----|-----------|
| ADR-015 (JSON Logging) | Aggregator reads structured JSON logs from CloudWatch |
| ADR-018 (CloudWatch Observability) | Defines log group structure and retention policies |
| ADR-019 (Vanilla Frontend) | Dashboard UI follows vanilla HTML/CSS/JS pattern |
| ADR-027 (Stateless Gold Access) | JSON artifact serving pattern via S3 + CloudFront |
| ADR-030 (Cost-Optimized Observability) | Current state: no metric filters/alarms; logs only |
| ADR-036 (Chart.js via CDN) | Charting library for data quality visualizations |
| ADR-038 (CloudFront Cache Tuning) | Cache behavior patterns for the health JSON endpoint |
| **ADR-040 (Proposed)** | Static Pipeline Health Dashboard architecture and security |

## Ticket Sequence

The epic is decomposed into 7 sequenced tickets. Dependencies flow top-to-bottom:

| # | Ticket | Dependencies | Effort |
|---|--------|-------------|--------|
| 1 | Define `pipeline_health.json` schema & Pydantic models | None | Small |
| 2 | Build telemetry aggregator Lambda | Ticket 1 | Medium |
| 3 | Implement log sanitization & security hardening | Ticket 2 | Medium |
| 4 | Build static health dashboard UI | Ticket 1 | Medium |
| 5 | Infrastructure as Code (Terraform) | Tickets 2, 3 | Medium |
| 6 | GitHub Actions workflow for aggregator trigger | Ticket 5 | Small |
| 7 | End-to-end integration testing & documentation | All above | Small |

**Proposed ADR-040** should be reviewed and accepted before implementation begins. It is included alongside these tickets.

## Success Criteria

- [ ] A public, unauthenticated web page displays Bronze/Silver/Gold pipeline status
- [ ] The page accurately reflects "failed" state when a pipeline component errors
- [ ] `pipeline_health.json` is automatically generated and hosted on S3/CloudFront
- [ ] The JSON artifact contains strictly sanitized data with zero internal AWS metadata, secrets, or stack traces
- [ ] Dashboard operates within the project's near-zero-cost budget (< $1/month incremental)
- [ ] Security review confirms no information leakage vectors

## Out of Scope

- Real-time streaming dashboards or WebSocket connections
- Historical trend storage beyond the rolling 7-day window in the JSON
- Alerting or notification systems (email, Slack, PagerDuty)
- Custom domain (e.g., `status.hoopstat-haus.com`) — can be added later per ADR-039 patterns
- Authentication or role-based access to the dashboard
