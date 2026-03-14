---
title: "ADR-038: CloudFront Cache Tuning for Immutable Historical Data"
status: "Proposed"
date: "2026-03-14"
tags:
  - "infrastructure"
  - "cloudfront"
  - "caching"
  - "cost-optimization"
---

## Context

* **Problem:** ADR-035 established a single CloudFront distribution with a uniform 1-hour cache TTL for all gold-layer artifacts. However, the data has two fundamentally different mutability profiles: the index file (`index/latest.json`) changes every time new data is published, while historical game data (`player_daily/*`, `team_daily/*`, `top_lists/*`) is immutable once written. A uniform TTL wastes edge cache capacity on the index and under-caches the historical data, leading to unnecessary S3 origin fetches and avoidable egress costs.

* **Constraints:**
  - Historical NBA game data never changes once published -- a player's box score for a past game is final.
  - The index file must remain fresh so that clients can discover newly published data within a few minutes.
  - CloudFront supports per-path-pattern cache behaviors with distinct response headers policies.
  - S3 objects can carry their own `Cache-Control` metadata, which CloudFront respects when the response headers policy uses `override = false`.

## Decision

**Apply differentiated Cache-Control headers based on data mutability: a 5-minute TTL for the index and a 1-year immutable TTL for all historical data.**

The implementation has two complementary layers:

1. **S3 Object Metadata (origin-level):** The `JSONArtifactWriter` in `gold-analytics` sets `CacheControl` per-object at upload time:
   - `served/index/latest.json` -- `public, max-age=300` (5 minutes)
   - `served/player_daily/*`, `served/team_daily/*`, `served/top_lists/*` -- `public, max-age=31536000, immutable` (1 year)

2. **CloudFront Response Headers Policies (edge-level fallback):** Two response headers policies provide the same Cache-Control values as a fallback (with `override = false` so the origin header takes precedence):
   - `gold_artifacts_index_cors` -- `public, max-age=300` (applied to `index/*` ordered cache behavior)
   - `gold_artifacts_cors` -- `public, max-age=31536000, immutable` (applied to default cache behavior)

3. **CloudFront Ordered Cache Behavior:** An `index/*` path pattern uses the short-TTL response headers policy, while the default behavior covers all historical data paths.

## Considered Options

1. **Differentiated Cache-Control at both origin and edge (Chosen):** Set per-object `CacheControl` on S3 upload and add matching CloudFront response headers policies for defense in depth.
   * *Pros:* Correct headers regardless of upload path; CloudFront fallback if an object is uploaded without metadata; simple to verify with `curl -I`.
   * *Cons:* Two places to maintain TTL values (code and Terraform), though they serve distinct purposes (origin vs. edge fallback).

2. **Lambda@Edge for dynamic Cache-Control:** Use a Lambda@Edge function to inspect the path and inject the appropriate header on the fly.
   * *Pros:* Single control point for caching logic.
   * *Cons:* Adds per-request Lambda cost; contradicts the project's preference for static infrastructure over runtime compute (ADR-033); more complex to deploy and debug.

3. **Origin-only Cache-Control (no Terraform changes):** Rely solely on S3 object metadata.
   * *Pros:* Simplest Terraform; no new resources.
   * *Cons:* If an object is uploaded without the header (e.g., manual `aws s3 cp`), CloudFront would fall back to its default behavior. Less defense in depth.

## Consequences

* **Positive:**
  - Near-zero S3 origin fetches for historical data after the first edge cache fill -- significantly reduces egress costs.
  - Index freshness within 5 minutes ensures clients always find the latest data pointer.
  - Browsers and CDN edges can cache immutable historical data indefinitely, improving repeat-visit performance.
  - Cache hit ratio should increase from ~50% to >90%.

* **Negative:**
  - If historical data is ever corrected (rare), a CloudFront cache invalidation is required.
  - Two TTL values are maintained in both Python code and Terraform (mitigated by clear constants and comments).

* **Future Implications:**
  - Any new artifact type under `served/` inherits the immutable default. If a new mutable artifact is added, it should be placed under `index/` or a new ordered cache behavior should be created.
  - Season aggregation artifacts (if added) should also use the immutable TTL since they represent completed seasons.
