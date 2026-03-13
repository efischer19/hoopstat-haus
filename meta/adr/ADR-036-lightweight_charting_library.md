---
title: "ADR-036: Lightweight Charting Library -- Chart.js via CDN"
status: "Accepted"
date: "2026-03-13"
tags:
  - "frontend"
  - "visualization"
  - "charting"
  - "cdn"
---

## Context

* **Problem:** The Hoopstat Haus frontend needs to display visual representations of basketball statistics -- trend lines, bar comparisons, and similar chart types -- to make data more accessible and engaging than raw JSON tables. We need a charting library that integrates cleanly with our existing vanilla HTML/CSS/JavaScript frontend (ADR-019) without introducing a build process, package manager dependencies, or framework coupling.

* **Constraints:**
  - ADR-019 established a vanilla HTML/CSS/JS frontend with no build process, no npm/node dependencies, and static file hosting. Any charting solution must respect this decision.
  - Libraries must be loadable via CDN `<script>` tag -- no bundlers, no `import` from `node_modules`.
  - Payload budget is limited. The frontend serves small JSON artifacts (<=100KB per ADR-035) and page loads should remain fast. A multi-megabyte charting library would be disproportionate.
  - Charts should work with vanilla JavaScript -- no React/Vue/Angular adapters required.
  - Progressive enhancement is preferred: the page should remain functional (showing data in text/table form) even if the charting library fails to load from the CDN.
  - The solution should cover common chart types (line, bar, pie/doughnut) without requiring low-level drawing code.

## Decision

**We will use Chart.js as the charting library for the Hoopstat Haus frontend, loaded via CDN from jsDelivr.**

The integration pattern is a single `<script>` tag:

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
```

**Version pinning strategy:** Pin to the major version (`@4`) in the CDN URL. This allows automatic patch and minor updates (bug fixes, non-breaking improvements) while preventing breaking changes from a future major version. If a specific minor version introduces a regression, we can temporarily pin to an exact version (e.g., `@4.4.7`) until the issue is resolved upstream.

**Chart initialization convention:** Charts are created by passing a `<canvas>` element and a configuration object to the `Chart` constructor. Chart setup logic lives in dedicated `<script>` blocks or JS files alongside the pages that use them, following the existing vanilla JS patterns from ADR-019.

**Progressive enhancement:** Pages that include charts should render meaningful content (tables, text summaries) before chart initialization. If Chart.js fails to load (CDN outage, blocked network), the page degrades gracefully to its non-chart content.

## Considered Options

1. **Chart.js via CDN (Chosen):** A well-established, high-level charting library (~65KB minified + gzipped) with a declarative configuration API.
   * *Pros:* Large community and extensive documentation; supports line, bar, pie, doughnut, radar, and more chart types out of the box; responsive by default; works with vanilla JS and a plain `<canvas>` element; available on all major CDNs; active maintenance with regular releases; simple declarative API -- a basic chart requires ~10-15 lines of configuration.
   * *Cons:* ~65KB minified + gzipped is not the smallest option available; introduces a runtime dependency on an external CDN; full bundle includes chart types and plugins that may go unused; customization beyond built-in options requires understanding the plugin system.

2. **uPlot via CDN:** A lightweight, high-performance charting library (~35KB minified + gzipped) focused on time-series data.
   * *Pros:* Roughly half the size of Chart.js; excellent rendering performance for large datasets; minimal API surface.
   * *Cons:* Smaller community and less comprehensive documentation; primarily designed for time-series line/area charts -- limited built-in support for bar, pie, or doughnut charts; fewer examples and tutorials available; would require more custom code for non-time-series visualizations.

3. **D3.js via CDN:** A powerful, low-level data visualization toolkit (~90KB minified + gzipped for the full bundle).
   * *Pros:* Extremely flexible -- can produce virtually any visualization; large community and extensive ecosystem; considered the industry standard for custom data visualization.
   * *Cons:* D3 is a visualization toolkit, not a charting library -- producing a simple line chart requires significantly more code than Chart.js; steep learning curve; overkill for standard chart types; the low-level API conflicts with our simplicity-first philosophy; larger payload than Chart.js for less out-of-the-box charting capability.

4. **Plotly.js via CDN:** A full-featured, high-level charting and scientific visualization library.
   * *Pros:* Rich interactive features (zoom, pan, hover tooltips) with minimal configuration; supports 40+ chart types including statistical and 3D charts; built-in export to PNG/SVG.
   * *Cons:* ~1MB minified for the full bundle -- violates our payload budget constraint by an order of magnitude; partial bundles are available but still large (~300KB+); heavy runtime footprint; designed for data science dashboards, not lightweight web frontends.

5. **Vanilla Canvas/SVG (No Library):** Build charts from scratch using the HTML5 Canvas API or inline SVG elements.
   * *Pros:* Zero external dependencies; maximum control over rendering; smallest possible payload (only our own code); no CDN dependency.
   * *Cons:* Requires significant development effort to implement responsive, interactive charts (axes, labels, legends, tooltips, animations); violates YAGNI -- we would be building a charting library instead of building a basketball statistics app; ongoing maintenance burden for chart rendering code; accessibility and cross-browser edge cases must be handled manually.

## Consequences

* **Positive:**
  - Simple integration: a single `<script>` tag and a `<canvas>` element are all that is needed to add a chart to any page.
  - No build process impact: fully compatible with the vanilla frontend approach (ADR-019).
  - Comprehensive documentation and community support reduce development time for new chart types.
  - Responsive charts by default -- Chart.js handles window resizing and mobile viewports automatically.
  - Declarative configuration keeps chart code readable and maintainable.

* **Negative:**
  - Runtime dependency on jsDelivr CDN availability. If the CDN is unreachable, charts will not render (mitigated by progressive enhancement -- non-chart content remains visible).
  - ~65KB added to page payload on first load (cached by the browser for subsequent visits).
  - Chart.js bundles all chart types even if only one or two are used (tree-shaking is not available without a bundler).
  - Future major version upgrades (e.g., v4 to v5) may require migration effort, though major version pinning prevents surprise breakage.

* **Future Implications:**
  - If payload size becomes a critical concern, uPlot is a viable drop-in alternative for time-series charts at roughly half the size.
  - If the frontend eventually adopts a build process (contrary to ADR-019), Chart.js supports ES module imports and tree-shaking for smaller bundles.
  - Chart.js plugins (e.g., `chartjs-plugin-datalabels`, `chartjs-plugin-annotation`) can be added via additional CDN script tags if advanced features are needed.
  - All chart-related JavaScript should guard against `Chart` being undefined to maintain progressive enhancement.
