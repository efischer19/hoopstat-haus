---
title: "ADR-036: Lightweight Charting Library -- Chart.js via CDN"
status: "Proposed"
date: "2026-03-12"
tags:
  - "frontend"
  - "visualization"
  - "charting"
  - "cdn"
---

## Context

* **Problem:** The frontend app needs to render time-series charts (e.g., player points over recent games) from Gold JSON artifacts. ADR-019 established a vanilla HTML/CSS/JS frontend with no build process and no npm dependencies. We need a charting library that works within these constraints -- loadable via CDN, usable with vanilla JavaScript, and simple enough to justify the added dependency.

* **Constraints:**
  - No build process or bundler (ADR-019) -- the library must be available via CDN `<script>` tag
  - No npm/node dependency tree -- the library must be self-contained
  - Vanilla JavaScript integration -- no framework-specific adapters required
  - Reasonable payload size -- should not dominate page load for a simple dashboard
  - Must support responsive line/bar charts with tooltips and legends
  - Progressive enhancement -- the page must remain functional if the CDN script fails to load

## Decision

**We will use Chart.js (version 4.x) loaded via CDN for all frontend charting needs.**

Chart.js will be included in `index.html` via a pinned major-version CDN script tag:

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js" defer></script>
```

Chart rendering code will use vanilla JavaScript to create Chart.js instances on `<canvas>` elements. Charts will be guarded behind a `typeof Chart !== 'undefined'` check to ensure progressive enhancement.

## Considered Options

1. **Chart.js via CDN (Chosen):** Full-featured, well-documented charting library with a large community.
   * *Pros:* Excellent documentation and examples; large community (62k+ GitHub stars); supports line, bar, pie, radar, and more chart types out of the box; responsive by default; accessible (ARIA support); works with vanilla JS; ~65KB minified+gzipped; actively maintained; CDN available via jsDelivr, cdnjs, and unpkg; treeshakeable if a build process is ever adopted.
   * *Cons:* Larger than minimalist alternatives (~65KB vs ~35KB for uPlot); includes chart types we may not need; Canvas-based rendering (not SVG) limits CSS styling of individual elements.

2. **uPlot via CDN:** Lightweight, high-performance time-series charting library.
   * *Pros:* Very small (~35KB minified+gzipped); fast rendering; purpose-built for time-series data; Canvas-based.
   * *Cons:* Smaller community (~8k GitHub stars); fewer chart types (primarily line/bar); less documentation; steeper learning curve for customization; fewer CDN hosting options; less accessible out of the box.

3. **D3.js via CDN:** Low-level data visualization toolkit.
   * *Pros:* Extremely powerful and flexible; SVG-based (CSS styleable); massive community; excellent for custom visualizations.
   * *Cons:* Not a charting library -- it is a visualization toolkit requiring significant code to produce a simple line chart; ~90KB minified+gzipped for the full bundle; steep learning curve; overkill for our "points over 10 games" use case; violates YAGNI.

4. **Plotly.js via CDN:** Full-featured scientific charting library.
   * *Pros:* Rich interactivity (zoom, pan, export); supports statistical chart types; good documentation.
   * *Cons:* Very large (~1MB minified for the basic bundle); built on D3; includes far more functionality than needed; violates our simplicity and payload constraints; significant performance overhead.

5. **Vanilla Canvas/SVG (No Library):** Hand-coded charts using the Canvas API or SVG elements.
   * *Pros:* Zero external dependencies; complete control over rendering; smallest possible payload.
   * *Cons:* Requires significant development effort to build responsive, interactive charts with tooltips, legends, and proper scaling; must handle accessibility manually; violates YAGNI by building charting infrastructure from scratch; maintenance burden of custom charting code.

## Consequences

* **Positive:**
  - Fast integration -- Chart.js requires minimal code to render a usable chart.
  - Excellent developer experience -- comprehensive documentation and examples reduce development time.
  - Progressive enhancement -- page works without charts if CDN is unavailable.
  - No build process impact -- CDN script tag aligns with ADR-019's no-build constraint.
  - Future flexibility -- Chart.js supports many chart types if needs expand beyond line charts.
  - Accessibility -- Chart.js supports ARIA labels on canvas elements.

* **Negative:**
  - External CDN dependency -- page load depends on jsDelivr availability (mitigated by `defer` and fallback messaging).
  - Library size (~65KB gzipped) is larger than the rest of the frontend combined (~8KB HTML+CSS+JS).
  - Canvas-based rendering limits CSS control over chart elements compared to SVG.
  - Pinning to major version (`@4`) means automatic minor/patch updates -- a breaking CDN update could theoretically affect the frontend (mitigated by jsDelivr's versioning guarantees).

* **Future Implications:**
  - If the frontend adopts a build process in the future (contrary to ADR-019), Chart.js can be installed via npm and tree-shaken for a smaller bundle.
  - If performance becomes critical with large datasets, uPlot could be evaluated as a lighter alternative.
  - The `createTimeSeriesChart()` helper function should be the single integration point, making it easy to swap charting libraries later if needed.
