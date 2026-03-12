# Epic: Frontend Simplification & Lightweight Visualization

> **Status:** Planning
> **Governing ADRs:** ADR-019 (Vanilla Frontend), ADR-027 (Stateless Gold Access), ADR-035 (CloudFront Public Access)
> **Proposed ADR:** ADR-036 (Lightweight Charting Library)

## Summary

The `frontend-app` currently contains half-developed mock backend code -- simulated API calls, dummy data generators, and a Q&A interface designed for a server-side backend that does not exist. This conflicts with our accepted static-first architecture (ADR-027, ADR-035), which serves pre-computed Gold JSON artifacts directly from CloudFront.

This epic cleans out the mock backend concepts, connects the frontend to real Gold artifacts via standard HTTP GET, and adds lightweight charting to visualize daily player/team trends.

## Goals

1. **Strip mock backends:** Remove all simulated API calls (`simulateAPICall`, `generateMockResponse`), dummy data, and dynamic server-side assumptions from `frontend-app`.
2. **Connect to Gold artifacts:** Fetch `latest.json` and player/team daily JSON artifacts from the public CloudFront `served/` URL.
3. **Integrate lightweight charting:** Add a dependency-free or lightweight charting library via CDN, documented in a proposed ADR.
4. **Render daily trends:** Build a simple dashboard that parses Gold JSON payloads and renders time-series charts (e.g., points over the last 10 games).

## Sequenced Tickets

| # | Ticket | Depends On | Scope |
|---|--------|------------|-------|
| 1 | [Strip Mock Backend Code](01-strip-mock-backends.md) | -- | Cleanup |
| 2 | [Connect to Gold JSON Artifacts](02-connect-gold-artifacts.md) | #1 | Data layer + UI |
| 3 | [Propose ADR-036: Charting Library](03-adr-charting-library.md) | -- | Documentation |
| 4 | [Integrate Chart.js via CDN](04-integrate-chartjs.md) | #2, #3 | Dependency |
| 5 | [Build Daily Trends Dashboard](05-daily-trends-dashboard.md) | #4 | Feature |

Tickets #1 and #3 can be worked in parallel. Ticket #2 depends on #1 (clean code to build on). Ticket #4 depends on both #2 (UI to embed charts into) and #3 (ADR approval for the library choice). Ticket #5 is the capstone feature.

## Architecture Context

### Current State (What We're Removing)

```
User types question → app.js simulateAPICall() → fake 2-3s delay → generateMockResponse()
                    → (or) makeAPICall() POST to /api/v1/ask → never-built backend
```

The current `app.js` has:
- `CONFIG.API_BASE_URL` pointing to a non-existent `api.hoopstat.haus`
- `CONFIG.ENABLE_API_CALLS = false` feature flag for a non-existent backend
- `simulateAPICall()` with fake network delays and 10% error simulation
- `generateMockResponse()` returning canned Q&A-style answers
- `makeAPICall()` POSTing to `/api/v1/ask` -- a server that will never be built
- Rate limiting infrastructure designed for a request-response API pattern

### Target State (What We're Building)

```
Dashboard loads → fetch(CloudFront/served/index/latest.json) → populate date/player selectors
User selects player → fetch(CloudFront/served/player_daily/{date}/{player_id}.json)
                    → parse JSON → Chart.js renders time-series (points, assists, etc.)
```

The new frontend will:
- Fetch static JSON artifacts via GET from the CloudFront distribution (ADR-035)
- Use the `served/index/latest.json` index for discoverability (ADR-027)
- Render charts using Chart.js loaded from CDN (ADR-036, proposed)
- Remain vanilla HTML/CSS/JS with no build process (ADR-019)

### Relevant Artifact Contract (from ADR-027)

```
served/player_daily/{date}/{player_id}.json
served/team_daily/{date}/{team_id}.json
served/top_lists/{date}/{top_ts|top_per|top_efg|top_net}.json
served/index/latest.json
```

## Out of Scope

- MCP integration (governed by ADR-033, ADR-034 -- separate concern)
- Authentication or user sessions (no-auth by design per ADR-027)
- Backend API development (explicitly rejected by static-first architecture)
- Complex state management or SPA framework adoption (ADR-019)
