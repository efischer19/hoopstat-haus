# Stateless Gold Access Plan (Public JSON Artifacts)

> Governing decision: ADR-027 (Accepted). This document provides implementation detail and backlog context for the stateless JSON-first approach. MCP is future/optional.

Status: Draft (tracked via issues)

This document tracks the plan to expose read-only basketball analytics via a stateless, open (no-auth) public API with strict rate limiting. Work will be organized as GitHub issues; we won’t implement code directly here.

## Intent (TL;DR)
- Serve small, precomputed JSON artifacts directly from S3. Public, no-auth, CORS-enabled, CDN optional.
- Keep payloads ≤ 100 KB. Provide indices like index/latest.json. Include human-readable fields.
- MCP adapter may be added later via API Gateway + Lambda, but it’s explicitly out of initial scope.

## Medallion Clarification: Not a 4th Layer
We are NOT adding a new medallion tier. “gold/served/” is simply a projection inside the existing Gold layer—think materialized views optimized for public consumption. It lives under the Gold bucket namespace and is produced by the Gold processing job.

- Gold (system of record): analytics computations and storage
- Gold-served (projection within Gold): small, cacheable JSON views for low-latency public reads

## Why JSON-only for Public Access
- Minimal complexity and lowest cost
- Predictable latency and spend; no in-request scans or heavy deps
- Fits stateless, no-auth, hobby constraints; easy to evolve

## Artifact Contract (v1)
- served/player_daily/{date}/{player_id}.json
- served/team_daily/{date}/{team_id}.json
- served/top_lists/{date}/{top_ts|top_per|top_efg|top_net}.json
- served/index/latest.json
- Optional: served/metadata/players_v1.json, served/metadata/teams_v1.json

## Implementation Outline
1) Public Access Config
- S3 public read on gold/served/ prefix + CORS; CDN optional

2) Gold processing
- Produce “served” artifacts after analytics steps; keep ≤ 100 KB per file
- Simple backfill optional

3) Docs & Tests
- Document shapes and size limits; add unit tests and a tiny load script

## Delivery Approach: GitHub Issues Backlog
See issues #361–#366 for the initial backlog.

