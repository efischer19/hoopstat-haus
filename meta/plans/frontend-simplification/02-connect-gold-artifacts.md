# Ticket 2: Connect Frontend to Gold JSON Artifacts

> **Epic:** [Frontend Simplification & Lightweight Visualization](00-executive-summary.md)
> **Sequence:** 2 of 5 (depends on ticket #1: Strip Mock Backends)
> **Governing ADRs:** ADR-019 (Vanilla Frontend), ADR-027 (Stateless Gold Access), ADR-035 (CloudFront Public Access)

---

## What do you want to build?

Refactor the frontend to fetch Gold JSON artifacts directly from the public CloudFront distribution via standard HTTP GET requests. Replace the Q&A form interface with a data browser that lets users select a date and view available player/team data. This connects the frontend to the real data pipeline for the first time.

## Acceptance Criteria

- [ ] A `GOLD_BASE_URL` configuration constant points to the CloudFront distribution URL for the `served/` prefix
- [ ] A `fetchArtifact(path)` utility function performs GET requests to `GOLD_BASE_URL + path` with appropriate error handling (network errors, 404s, non-JSON responses)
- [ ] On page load, the app fetches `served/index/latest.json` and displays the latest available date and summary info
- [ ] The UI provides a way to select a player or team from the latest index data and fetch their daily artifact (`served/player_daily/{date}/{player_id}.json` or `served/team_daily/{date}/{team_id}.json`)
- [ ] Fetched artifact data is displayed in a readable, formatted view (structured HTML, not raw JSON dump)
- [ ] The Q&A form (`#question-form`) and example question buttons are replaced with the data browser UI
- [ ] Loading states are shown during artifact fetches
- [ ] Errors (network failures, missing artifacts) are displayed clearly to the user
- [ ] CORS preflight requests succeed (CloudFront CORS policy per ADR-035)
- [ ] The frontend remains vanilla HTML/CSS/JS with no build process (ADR-019)

## Implementation Notes (Optional)

### CloudFront URL

The CloudFront distribution URL is defined in Terraform outputs. For the frontend CONFIG, use the pattern:

```javascript
const CONFIG = {
  GOLD_BASE_URL: 'https://{cloudfront-domain}/served',
  REQUEST_TIMEOUT_MS: 10000,
};
```

The exact domain will come from the Terraform `cloudfront_distribution_domain_name` output or a configured vanity domain.

### Fetch utility

```javascript
async function fetchArtifact(path) {
  const response = await fetch(`${CONFIG.GOLD_BASE_URL}/${path}`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch ${path}: HTTP ${response.status}`);
  }

  return response.json();
}
```

### Artifact contract (from ADR-027)

```
served/index/latest.json          -- entry point; contains latest date, player/team lists
served/player_daily/{date}/{id}.json  -- daily stats for a specific player
served/team_daily/{date}/{id}.json    -- daily stats for a specific team
served/top_lists/{date}/{list}.json   -- top performer lists
```

### UI changes

Replace the Q&A form in `index.html` with:

1. **Latest data banner** -- shows the date from `latest.json` and a refresh button
2. **Player/team selector** -- dropdown or list populated from the latest index
3. **Data display area** -- formatted view of the selected artifact's contents
4. **Error display** -- reuse existing error container pattern

### CSS updates

- Style the data browser elements (selector, data display)
- Reuse existing responsive patterns from `styles.css`
- Add styles for data tables or stat cards as needed

### Verification

1. Open `index.html` in a browser
2. Confirm `latest.json` is fetched on load (check Network tab)
3. Select a player/team and confirm the daily artifact loads
4. Confirm CORS headers are present on responses
5. Simulate a network error and confirm the error UI displays
6. Test on mobile viewport widths to verify responsiveness
