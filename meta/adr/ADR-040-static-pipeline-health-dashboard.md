---
title: "ADR-040: Static Pipeline Health Dashboard Architecture"
status: "Proposed"
date: "2026-03-26"
tags:
  - "observability"
  - "security"
  - "frontend"
  - "data-pipeline"
---

## Context

* **Problem:** The Hoopstat Haus data pipeline processes daily NBA statistics through a Bronze → Silver → Gold Medallion architecture with CloudWatch logging and Silver-layer data quality scoring. However, all operational telemetry is locked inside the AWS environment. Data consumers — developers, AI agents, and frontend users — have no way to verify pipeline freshness, identify degraded states, or distinguish between upstream pipeline failures and their own integration bugs without AWS console access.

* **Constraints:**
  - Must maintain near-zero-cost architecture (ADR-030 removed metric filters/alarms to minimize costs).
  - Must not expose any internal AWS metadata, secrets, stack traces, or infrastructure topology to the public.
  - Must follow the static-first, vanilla frontend approach (ADR-019, ADR-027).
  - Must not create a live backend that could be exploited for Denial of Wallet (DoW) attacks.
  - The existing CloudFront distribution serves only static files from the Gold S3 bucket's `served/` prefix.
  - Chart.js via CDN (ADR-036) is the accepted charting library.

## Decision

**We will build a public, unauthenticated pipeline health dashboard using the Static Generation Pattern.** The system consists of three components:

### 1. Telemetry Aggregator Lambda
A Python Lambda function, triggered daily after Gold processing completes, that:
- Queries CloudWatch Logs Insights for pipeline execution outcomes (success/failure) across Bronze, Silver, and Gold stages.
- Reads quarantine file counts from the Bronze S3 bucket's `quarantine/` prefix.
- Compiles results into a single `pipeline_health.json` file.
- **Sanitizes all output** before writing — stripping stack traces, internal IPs, IAM role names, bucket names, error messages, and any credential-like strings.

### 2. Static JSON Artifact
The `pipeline_health.json` file is written to `s3://hoopstat-haus-gold/served/health/pipeline_health.json` with:
- `Cache-Control: public, max-age=3600` (1-hour TTL, matching frontend asset caching from ADR-038).
- Schema enforced by Pydantic models in the `hoopstat-data` shared library.
- Rolling 7-day window of daily pipeline execution summaries.

### 3. Static Dashboard UI
A vanilla HTML/CSS/JS page (per ADR-019) hosted alongside the existing frontend at `/health.html`:
- Fetches `pipeline_health.json` via the CloudFront CDN URL.
- Renders traffic-light status indicators (Operational / Degraded / Outage) for each pipeline stage.
- Uses Chart.js (ADR-036) to visualize 7-day trends: records ingested vs. quarantined.
- Degrades gracefully if Chart.js CDN is unavailable (shows text-based status only).

### Security Model
The dashboard's security posture is defined by strict invariants:

1. **No Live Backend:** The browser fetches only the static JSON file. The aggregator Lambda runs server-side on a schedule and never exposes an HTTP endpoint.
2. **Log Sanitization:** The aggregator applies an allowlist approach — only explicitly permitted fields (status enums, counts, ISO timestamps) are included in the output. All other data is discarded.
3. **No Secrets Exposure:** The aggregator scans compiled output for patterns matching AWS access keys, tokens, and ARNs, rejecting the entire payload if any are detected.
4. **Obfuscated Execution Windows:** Only completion timestamps are published. Start times, durations, and infrastructure spin-up chronologies are never included.
5. **Cost Protection:** The static file is served from CloudFront cache (1-hour TTL). Even under heavy traffic, origin fetches are limited to ~24/day. No per-request Lambda invocations.

## Considered Options

1. **Static Generation Pattern with Aggregator Lambda (Chosen):** Pre-compute a sanitized JSON artifact on a schedule; serve statically via CDN.
   * *Pros:* Zero per-request cost; CDN caching prevents DoW attacks; strict sanitization boundary between AWS internals and public output; follows established ADR-027 JSON artifact pattern; simple to implement and maintain.
   * *Cons:* Data staleness up to 1 day (dashboard reflects last completed run, not real-time); requires a new Lambda function and IAM role; adds a small amount of infrastructure complexity.

2. **API Gateway + Lambda On-Demand:** Expose a `/health` API endpoint that queries CloudWatch in real-time per request.
   * *Pros:* Always fresh data; familiar REST API pattern.
   * *Cons:* Per-request CloudWatch Logs Insights queries incur cost (~$0.005/GB scanned per query); vulnerable to DoW attacks if endpoint is discovered; requires API Gateway provisioning; contradicts the static-first philosophy; introduces a live backend that must be secured and rate-limited.

3. **CloudWatch Dashboard with Public Sharing:** Use AWS CloudWatch's native dashboard sharing feature.
   * *Pros:* No custom code required; rich built-in visualizations.
   * *Cons:* Requires CloudWatch Dashboard (costs $3/month per dashboard); public sharing URL exposes AWS console-style UI with potentially sensitive metadata; limited customization; vendor lock-in for the UI; cannot enforce sanitization of displayed data.

4. **GitHub Actions Artifact:** Generate the health JSON as a GitHub Actions artifact and serve from GitHub Pages.
   * *Pros:* No AWS infrastructure changes; free hosting via GitHub Pages.
   * *Cons:* Splits the serving infrastructure (data on CloudFront, health on GitHub Pages); GitHub Actions artifact retention is limited; adds complexity to the CI/CD pipeline; latency between pipeline completion and artifact availability.

## Consequences

* **Positive:**
  - Data consumers gain immediate, frictionless visibility into pipeline health without AWS access.
  - The strict sanitization boundary prevents accidental exposure of infrastructure internals.
  - The static pattern adds negligible cost (~$0.01/month for Lambda invocations and S3 storage).
  - Follows established project patterns (ADR-027 JSON artifacts, ADR-019 vanilla frontend, ADR-036 Chart.js).
  - The aggregator Lambda can be extended in future to include additional metrics without changing the dashboard UI.

* **Negative:**
  - Dashboard data may be up to ~24 hours stale (reflects last completed pipeline run).
  - Introduces a new Lambda function that must be maintained, tested, and deployed.
  - The aggregator requires read-only IAM permissions to CloudWatch Logs and S3, expanding the IAM surface area.
  - The sanitization logic must be carefully maintained — a bug could leak internal metadata.

* **Future Implications:**
  - The `pipeline_health.json` schema should be versioned (include a `schema_version` field) to support backward-compatible evolution.
  - If real-time status becomes necessary, the static pattern can be augmented with a lightweight WebSocket or polling approach without replacing the core architecture.
  - The aggregator Lambda serves as a foundation for future observability features (e.g., weekly summary emails, Slack notifications) by extending its output.
  - A custom domain (e.g., `status.hoopstat-haus.com`) can be added later using the patterns from ADR-039.
