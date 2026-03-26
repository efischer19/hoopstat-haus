# Ticket 4: Build Static Health Dashboard UI

**Title:** `feat: Build static health dashboard UI for pipeline observability`

**Labels:** `enhancement`

---

## What do you want to build?

Build a public, unauthenticated static HTML/CSS/JS page (`health.html`) that visualizes the pipeline health data from `pipeline_health.json`. The dashboard provides at-a-glance status for all three Medallion layers and a 7-day trend chart for data quality metrics.

This page follows the existing vanilla frontend approach (ADR-019), uses Chart.js for visualizations (ADR-036), and is hosted alongside the current frontend app on CloudFront.

### Dashboard Layout

```
┌──────────────────────────────────────────────────────┐
│  Hoopstat Haus — Pipeline Health                     │
│  Last updated: 2026-03-26 06:00 UTC                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ● Bronze Ingestion    ● Silver Processing    ● Gold │
│    Operational           Operational          Oper.  │
│    Last: 04:15 UTC       Last: 04:45 UTC      05:30  │
│                                                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  7-Day Data Quality Trend                            │
│  ┌────────────────────────────────────────────┐      │
│  │  ██ Ingested  ░░ Quarantined               │      │
│  │  ██████████████████████████████████         │      │
│  │  ██████████████████████████████████  ░░     │      │
│  │  ████████████████████████████████████████   │      │
│  └────────────────────────────────────────────┘      │
│                                                      │
├──────────────────────────────────────────────────────┤
│  Daily Breakdown (most recent 7 days)                │
│  ┌─────────┬────────┬────────┬──────┬────────┐      │
│  │ Date    │ Bronze │ Silver │ Gold │ Quar.  │      │
│  ├─────────┼────────┼────────┼──────┼────────┤      │
│  │ Mar 26  │   ✓    │   ✓    │  ✓   │   2    │      │
│  │ Mar 25  │   ✓    │   ✓    │  ✓   │   0    │      │
│  │ Mar 24  │   ✗    │   —    │  —   │   0    │      │
│  └─────────┴────────┴────────┴──────┴────────┘      │
│                                                      │
│  Data provided by pipeline_health.json               │
│  Refreshes hourly · No authentication required       │
└──────────────────────────────────────────────────────┘
```

### Visual Design

- **Status indicators** use color-coded circles: green (operational/success), yellow (degraded/quarantined), red (outage/failed), gray (no_data/skipped).
- **Overall system banner** changes background color based on `overall_status`: green bar for operational, yellow for degraded, red for outage.
- **Chart** is a stacked bar chart (Chart.js) showing daily records ingested vs. quarantined over the 7-day window.
- **Table** shows a per-day breakdown with status icons and quarantine counts.
- **Mobile responsive** — the layout stacks vertically on small screens.

### Progressive Enhancement

Per ADR-036, the page must degrade gracefully:
- If `pipeline_health.json` fails to load → display "Unable to load pipeline status. Please try again later." with a retry button.
- If Chart.js fails to load from CDN → the table and status indicators still render; the chart section shows "Chart unavailable."
- The page is functional without JavaScript disabled → basic structure is visible, with a `<noscript>` message explaining that JS is required for live data.

---

## Acceptance Criteria

- [ ] A `health.html` file is added to `frontend-app/` alongside the existing frontend
- [ ] The page fetches `pipeline_health.json` from the CloudFront CDN relative path (`/health/pipeline_health.json`)
- [ ] Three status indicators display the current state of Bronze, Silver, and Gold pipelines with color coding
- [ ] An overall system status banner reflects `operational`, `degraded`, or `outage`
- [ ] A Chart.js stacked bar chart visualizes 7-day records ingested vs. records quarantined
- [ ] A data table shows per-day breakdown with status icons and quarantine counts
- [ ] The page displays the `generated_at` timestamp as "Last updated: ..." in a human-readable format
- [ ] The page degrades gracefully when `pipeline_health.json` fails to load (error message + retry)
- [ ] The page degrades gracefully when Chart.js CDN is unavailable (table still renders)
- [ ] The layout is responsive and usable on mobile devices (min-width: 320px)
- [ ] CSS styling is consistent with the existing frontend-app visual style
- [ ] No external dependencies beyond Chart.js CDN (per ADR-019, no npm/node/build tools)

---

## Implementation Notes (Optional)

- Follow the existing frontend patterns in `frontend-app/` — the current app uses vanilla HTML/CSS/JS with no build process.
- The `pipeline_health.json` URL should be a relative path (e.g., `/health/pipeline_health.json`) so it works through CloudFront without hardcoding a domain.
- Use semantic HTML (`<main>`, `<section>`, `<table>`, `<time>`) for accessibility.
- Chart.js is loaded via CDN per ADR-036: `<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>`. Guard chart initialization with `if (typeof Chart !== 'undefined')`.
- The status color mapping: `success`/`operational` → `#22c55e` (green), `degraded` → `#eab308` (yellow), `failed`/`outage` → `#ef4444` (red), `skipped`/`no_data` → `#9ca3af` (gray).
- Consider adding a small "Last checked: X seconds ago" timer that updates client-side to show the page is live, even though data updates hourly.
- **Dependency on Ticket 1:** The JSON schema must be finalized to know what fields to render. However, the UI can be developed in parallel using a mock `pipeline_health.json` file.
- The `deploy-frontend.yml` workflow already syncs `frontend-app/` to S3 — no changes needed for deployment of the HTML file itself.
