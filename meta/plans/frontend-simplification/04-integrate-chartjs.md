# Ticket 4: Integrate Chart.js via CDN

> **Epic:** [Frontend Simplification & Lightweight Visualization](00-executive-summary.md)
> **Sequence:** 4 of 5 (depends on ticket #2: Connect Gold Artifacts, and ticket #3: ADR-036 Accepted)
> **Governing ADRs:** ADR-019 (Vanilla Frontend), ADR-036 (Lightweight Charting Library -- must be Accepted before this work begins)

---

## What do you want to build?

Add Chart.js to the frontend via CDN script tag and create a small chart utility module that provides helper functions for creating and updating charts from Gold JSON artifact data. This sets up the charting infrastructure that ticket #5 will use to build the dashboard.

## Acceptance Criteria

- [ ] ADR-036 has been accepted before this work begins
- [ ] `index.html` includes a Chart.js CDN `<script>` tag pinned to major version 4 (e.g., `chart.js@4`)
- [ ] The Chart.js script loads before `app.js` (correct dependency order in the HTML)
- [ ] A `<canvas>` element is added to `index.html` inside the main content area for chart rendering
- [ ] A chart utility module (or section in `app.js`) provides a `createTimeSeriesChart(canvasId, labels, datasets, options)` helper function
- [ ] The helper function wraps Chart.js initialization with sensible defaults for time-series line charts (responsive, tooltips, legend)
- [ ] The helper function supports updating chart data without destroying/recreating the chart instance
- [ ] Chart.js loads successfully with no console errors
- [ ] If the CDN script fails to load, the page still renders without charts (progressive enhancement) and displays a graceful fallback message
- [ ] The frontend remains dependency-free in terms of npm/node packages (CDN only, per ADR-019)

## Implementation Notes (Optional)

### CDN script tag

Add to `index.html` `<head>`, before the `app.js` script:

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js" defer></script>
```

Both scripts use `defer`, so they execute in document order after HTML parsing.

### Canvas element

Add inside `<main>` in `index.html`:

```html
<div class="chart-container" id="chart-section" style="display: none;">
  <h2>Performance Trends</h2>
  <canvas id="trends-chart" aria-label="Player performance trends chart" role="img">
    <p>Chart could not be displayed. Please check your connection.</p>
  </canvas>
</div>
```

The `<p>` fallback inside `<canvas>` displays when canvas is unsupported or Chart.js fails to load.

### Chart utility pattern

```javascript
// Chart utility (in app.js or a separate charts.js)
function createTimeSeriesChart(canvasId, labels, datasets, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) {
    console.warn(`Canvas element '${canvasId}' not found`);
    return null;
  }
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js library not loaded');
    return null;
  }

  const defaults = {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: { mode: 'index', intersect: false },
      },
      scales: {
        x: { title: { display: true, text: 'Game Date' } },
        y: { title: { display: true, text: 'Value' }, beginAtZero: true },
      },
      ...options,
    },
  };

  return new Chart(ctx, defaults);
}
```

### Progressive enhancement check

```javascript
// Guard chart creation behind CDN availability
if (typeof Chart !== 'undefined') {
  // Initialize charts
} else {
  document.getElementById('chart-section').innerHTML =
    '<p class="chart-fallback">Charts unavailable. Data is displayed below.</p>';
}
```

### CSS additions

Add to `styles.css`:

```css
.chart-container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 1rem;
  position: relative;
  height: 400px;
}

.chart-fallback {
  text-align: center;
  color: var(--text-muted);
  padding: 2rem;
}
```

### Verification

1. Open `index.html` in a browser
2. Check Network tab -- Chart.js CDN script loads successfully
3. Check console -- no errors related to Chart.js
4. Call `createTimeSeriesChart('trends-chart', ['G1','G2','G3'], [{label:'PTS', data:[20,25,18]}])` from console -- chart renders
5. Disable network and reload -- page still renders, fallback message shows
6. Test on mobile viewport -- chart is responsive
