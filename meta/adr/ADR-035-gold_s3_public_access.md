---
title: "ADR-035: Gold S3 Public Access via CloudFront with Origin Access Control"
status: "Accepted"
date: "2026-03-09"
tags:
  - "infrastructure"
  - "security"
  - "s3"
  - "cloudfront"
  - "public-access"
---

## Context

* **Problem:** ADR-027 and ADR-028 established that Gold layer JSON artifacts under the `served/` prefix must be publicly accessible via HTTP GET. We need to formalize the access strategy: how the S3 bucket is exposed to the internet, what security boundaries are enforced, and how cost is managed for data transfer.

* **Constraints:**
  - The Gold S3 bucket contains both internal analytics data (Parquet, not public) and public JSON artifacts (under `served/`). Only the `served/` prefix should be publicly readable.
  - ADR-012 (single environment) means there is one production bucket -- no staging/dev separation.
  - ADR-033 (local proxy MCP architecture) means MCP adapters will also consume these artifacts via HTTP GET. There is no server-side compute layer between the client and the data.
  - AWS best practices discourage making S3 buckets directly public; Origin Access Control (OAC) with CloudFront is the recommended pattern.
  - CORS must be enabled for browser-based access (frontend apps, dashboards).

## Decision

**Gold layer JSON artifacts are served exclusively via a CloudFront distribution backed by Origin Access Control (OAC). The S3 bucket remains fully private (Block Public Access enabled). Only the `served/` prefix is accessible through CloudFront.**

The access architecture:

1. **S3 Bucket (Private):** The Gold S3 bucket has Block Public Access enabled. No direct S3 public URLs are used. A bucket policy grants read access exclusively to the CloudFront OAC service principal, scoped to the `served/` prefix.

2. **CloudFront Distribution (Public):** A CloudFront distribution serves as the sole public entry point. It uses OAC to sign requests to S3, providing:
   - Global edge caching for low-latency access worldwide
   - Automatic gzip/brotli compression for smaller payloads
   - HTTPS-only access with TLS termination at the edge
   - 1-hour default cache TTL (matching our daily data update cadence)

3. **CORS Policy:** A CloudFront response headers policy allows GET/HEAD/OPTIONS from any origin (`*`) with a 1-hour max-age, enabling browser-based consumption.

4. **Optional Vanity Domain:** The distribution supports optional custom domain names (e.g., `hoopstat.haus`) via ACM certificates, configured through Terraform variables.

**This decision explicitly rejects direct S3 public access (public bucket policies or S3 static website hosting) in favor of the CloudFront + OAC pattern.**

## Considered Options

1. **CloudFront + Origin Access Control (Chosen):** Private S3 bucket with CloudFront as the sole public access point.
   * *Pros:* S3 bucket stays fully private (defense in depth); CloudFront provides global edge caching, compression, and HTTPS; OAC limits read access to only the `served/` prefix; supports custom domains; aligns with AWS best practices; cost-effective for small payloads (CloudFront data transfer is often cheaper than direct S3 for cached content).
   * *Cons:* Adds CloudFront as a dependency; slight additional infrastructure complexity; cache invalidation needed if artifacts are updated more than once per hour.

2. **Direct S3 Public Access (Public Bucket Policy):** Make the `served/` prefix directly public via an S3 bucket policy.
   * *Pros:* Simplest to configure; no CDN dependency; direct S3 URLs.
   * *Cons:* S3 Block Public Access must be disabled (reduces security posture); no edge caching (higher latency for global users); no compression; no HTTPS custom domain without additional setup; CORS must be configured on the bucket directly; AWS explicitly discourages this pattern for production workloads.

3. **S3 Static Website Hosting:** Enable S3 static website hosting on the bucket.
   * *Pros:* Built-in index document support; simple custom error pages; familiar pattern for static sites.
   * *Cons:* HTTP-only (no HTTPS without CloudFront anyway); requires public bucket access; designed for websites, not API-style JSON artifact serving; limited CORS configuration.

4. **API Gateway + Lambda Proxy:** Serve artifacts through an API Gateway endpoint backed by a Lambda that reads from S3.
   * *Pros:* Could add authentication, rate limiting, or transformation logic.
   * *Cons:* Directly contradicts ADR-033 (no cloud compute for data serving); adds per-request Lambda costs; unnecessary complexity for static file serving; rejected as part of the local proxy architecture decision.

## Consequences

* **Positive:**
  - Defense in depth: S3 bucket is never directly exposed to the internet.
  - Global performance: CloudFront edge caching provides sub-100ms response times for cached artifacts.
  - Cost-effective: Small JSON payloads (<=100KB) with edge caching minimize data transfer costs.
  - HTTPS by default: All public access is encrypted in transit.
  - Compression: Automatic gzip/brotli reduces payload sizes further.
  - Custom domain ready: Vanity domain support is built in via Terraform variables.

* **Negative:**
  - CloudFront distribution is an additional AWS resource to manage (though Terraform handles this).
  - Cache TTL means artifact updates may take up to 1 hour to propagate (acceptable given daily data cadence).
  - CloudFront access logs add minor storage cost if enabled.

* **Future Implications:**
  - MCP adapters (ADR-033, ADR-034) should use the CloudFront URL as their base endpoint, not direct S3 URLs.
  - If update frequency increases beyond daily, the cache TTL may need adjustment or cache invalidation may be needed.
  - The CloudFront distribution ID and domain name should be surfaced as Terraform outputs for downstream consumers.
  - Any new public artifacts must be placed under the `served/` prefix to be accessible through CloudFront.
