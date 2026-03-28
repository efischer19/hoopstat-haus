# Hoopstat Haus Frontend Application

A simple, static web application that provides a data browser for basketball analytics. Built with vanilla HTML, CSS, and JavaScript following the project's simplicity-first philosophy.

## Features

- **Data Browser Interface**: Browse player and team statistics from the Gold data pipeline
- **Latest Data Banner**: Displays the most recent data date and a refresh button
- **Player/Team Selector**: Tabbed interface with dropdowns populated from the latest index
- **Formatted Data Display**: Stats shown as cards and tables, not raw JSON
- **Mobile-Responsive Design**: Mobile-first CSS with responsive breakpoints
- **Error Handling**: Comprehensive error handling for network and fetch issues
- **Loading States**: Visual feedback during data fetches
- **Accessibility**: WCAG 2.1 AA compliant with screen reader support

## Architecture

This frontend follows a **vanilla HTML/CSS/JavaScript approach** as documented in ADR-019. The design emphasizes:

- **Static-First**: No build process required, can be hosted on any web server
- **Progressive Enhancement**: Core functionality works without JavaScript
- **Minimal Dependencies**: Zero external libraries or frameworks
- **Gold Artifacts**: Fetches JSON artifacts directly from CloudFront (ADR-027, ADR-035)

## File Structure

```
frontend-app/
├── index.html              # Main application entry point
├── health.html             # Pipeline health dashboard
├── assets/
│   ├── styles.css         # Mobile-first responsive CSS
│   └── favicon.svg        # SVG favicon
├── scripts/
│   ├── app.js             # JavaScript for data browsing and artifact fetching
│   └── health.js          # JavaScript for health dashboard rendering
└── README.md              # This file
```

## Development

### Local Development

1. Serve the files with any static web server:

```bash
# Using Python (recommended)
cd frontend-app
python -m http.server 8080

# Using Node.js
npx serve .

# Using PHP
php -S localhost:8080
```

2. Open http://localhost:8080 in your browser

### Configuration

The application is configured via the `CONFIG` object in `scripts/app.js`:

```javascript
const CONFIG = {
  GOLD_BASE_URL: 'https://CLOUDFRONT_DOMAIN_PLACEHOLDER',
  REQUEST_TIMEOUT_MS: 10000,
};
```

The `GOLD_BASE_URL` points to the CloudFront distribution that serves Gold JSON artifacts. Replace `CLOUDFRONT_DOMAIN_PLACEHOLDER` with the actual domain from `terraform output cloudfront_distribution` or a configured vanity domain. The CloudFront distribution uses `origin_path: /served` so client URLs omit the `served/` prefix.

### Artifact Contract (ADR-027)

The frontend fetches these artifacts from CloudFront:

- `index/latest.json` -- entry point; contains latest date, player and team lists
- `player_daily/{date}/{player_id}.json` -- daily stats for a specific player
- `team_daily/{date}/{team_id}.json` -- daily stats for a specific team
- `top_lists/{date}/{metric}.json` -- top performer lists

### Fetch Utility

The `fetchArtifact(path)` function handles all HTTP GET requests to CloudFront with:

- Timeout via `AbortController` (configurable via `REQUEST_TIMEOUT_MS`)
- HTTP status error handling (404s, 5xx errors)
- Content-type validation for JSON responses
- User-friendly error messages

## Features

### Data Browser

On page load, the app fetches `index/latest.json` and:
1. Displays the latest available data date in a banner
2. Populates player and team dropdown selectors
3. Allows selecting a player or team to view their daily stats

### Error Handling

Comprehensive error handling for:
- Network timeouts (configurable limit)
- HTTP errors (404, 5xx)
- Connection issues
- Non-JSON responses

### Accessibility

- Semantic HTML structure
- ARIA labels and tab roles
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support
- Reduced motion support

### Mobile Optimization

- Mobile-first responsive CSS
- Touch-friendly interface elements
- Optimized typography for small screens
- Progressive enhancement for larger screens

## Health Dashboard

The `health.html` page provides an at-a-glance view of pipeline health status, implemented per [ADR-040 — Static Pipeline Health Dashboard](../meta/adr/ADR-040-static-pipeline-health-dashboard.md).

### What It Displays

- **Overall status banner** — Traffic-light indicator (Operational / Degraded / Outage) for the entire pipeline
- **Stage indicator cards** — Individual status for Bronze Ingestion, Silver Processing, and Gold Analytics with last-success timestamps
- **7-day data quality trend** — Chart.js stacked bar chart showing records ingested vs quarantined over the past week
- **Daily breakdown table** — Per-day status icons for each stage and quarantine counts

### Data Source

The dashboard fetches `pipeline_health.json` from the CloudFront CDN (path: `/health/pipeline_health.json`). This JSON artifact is:

- Generated daily by the [health-aggregator](../apps/health-aggregator/) Lambda
- Cached with `Cache-Control: public, max-age=3600` (1-hour TTL)
- Schema-validated by Pydantic models in `hoopstat-data`
- Sanitized to remove any AWS credentials, ARNs, or internal IPs

### Local Testing

To test the health dashboard locally, serve the frontend with a mock `pipeline_health.json`:

```bash
# Create a mock health JSON file
mkdir -p frontend-app/health
cp /path/to/mock/pipeline_health.json frontend-app/health/pipeline_health.json

# Serve locally
cd frontend-app
python3 -m http.server 8080
```

Then open http://localhost:8080/health.html in your browser.

A convenience script is available at `scripts/test-health-dashboard.sh` that generates mock data, starts a local server, and prints the URL for the dashboard.

### Graceful Degradation

- If `pipeline_health.json` cannot be fetched, an error state with a retry button is shown
- If Chart.js CDN is unavailable, the chart area shows a "Chart unavailable" fallback message
- Without JavaScript, the dashboard renders a static no-data state with the page structure, stage cards, and table visible (progressive enhancement)

## Deployment

### Static Hosting

This application can be deployed to any static hosting service:

- **AWS S3 + CloudFront**: Recommended for integration with existing infrastructure
- **Netlify**: Simple drag-and-drop deployment
- **GitHub Pages**: Free hosting for open source projects

### CORS

The CloudFront distribution includes CORS response headers (ADR-035) allowing GET/HEAD/OPTIONS from any origin with a 1-hour max-age.

## Browser Support

- **Modern Browsers**: Chrome 70+, Firefox 65+, Safari 12+, Edge 79+
- **Progressive Enhancement**: Core functionality works in older browsers
- **Feature Detection**: Graceful degradation for unsupported features

## Performance

- **Load Time**: < 2 seconds on 3G networks
- **First Paint**: < 1 second
- **Bundle Size**: < 50KB total (HTML + CSS + JS)
- **Lighthouse Score**: 95+ for Performance, Accessibility, Best Practices

---

Built with ❤️ for the basketball analytics community.