# Ticket 5: Build Daily Trends Dashboard View

> **Epic:** [Frontend Simplification & Lightweight Visualization](00-executive-summary.md)
> **Sequence:** 5 of 5 (depends on ticket #4: Integrate Chart.js)
> **Governing ADRs:** ADR-019 (Vanilla Frontend), ADR-027 (Stateless Gold Access), ADR-035 (CloudFront Public Access), ADR-036 (Lightweight Charting Library)

---

## What do you want to build?

Create a simple dashboard view that fetches a player's or team's daily Gold JSON artifact, parses the payload, and renders a time-series chart showing performance trends over recent games (e.g., points scored over the last 10 games). This is the capstone feature of the epic -- it connects all prior work (clean codebase, artifact fetching, Chart.js integration) into a user-facing visualization.

## Acceptance Criteria

- [ ] When a user selects a player from the data browser (ticket #2), the dashboard fetches their daily artifact and renders a line chart of points scored over recent games
- [ ] The chart displays at least the last 10 games (or all available games if fewer than 10)
- [ ] The x-axis shows game dates; the y-axis shows the stat value (e.g., points)
- [ ] Users can toggle between different stats on the chart (e.g., points, assists, rebounds) via simple controls (buttons or a dropdown)
- [ ] When a different player is selected, the chart updates with the new player's data (no page reload)
- [ ] Team daily artifacts can also be visualized with relevant team-level stats
- [ ] The chart is responsive and renders correctly on mobile, tablet, and desktop viewports
- [ ] A loading indicator is shown while the artifact is being fetched and the chart is being rendered
- [ ] If a player/team has no data or the artifact is missing, a clear "No data available" message is shown instead of a broken chart
- [ ] The dashboard view integrates cleanly with the data browser UI from ticket #2
- [ ] All chart interactions (hover tooltips, legend clicks) work correctly

## Implementation Notes (Optional)

### Artifact JSON shape (from ADR-027)

Player daily artifacts are expected to follow a schema like:

```json
{
  "version": "v1",
  "player_id": 2544,
  "player_name": "LeBron James",
  "team_abbr": "LAL",
  "date": "2026-03-11",
  "games": [
    {
      "game_date": "2026-03-10",
      "opponent": "GSW",
      "points": 28,
      "rebounds": 7,
      "assists": 9,
      "steals": 2,
      "blocks": 1,
      "fg_pct": 0.524,
      "three_pct": 0.400,
      "ft_pct": 0.857,
      "minutes": 35,
      "plus_minus": 12
    }
  ]
}
```

The exact schema will be defined by the Gold analytics job. The frontend should be resilient to missing optional fields.

### Chart rendering flow

```
User selects player
  → fetchArtifact(`player_daily/${date}/${playerId}.json`)
  → Parse response.games[]
  → Extract labels (game_date) and datasets (points, assists, etc.)
  → createTimeSeriesChart('trends-chart', labels, datasets)
```

### Stat toggle controls

Add simple buttons or a `<select>` dropdown above the chart:

```html
<div class="stat-selector">
  <button class="stat-btn active" data-stat="points">Points</button>
  <button class="stat-btn" data-stat="rebounds">Rebounds</button>
  <button class="stat-btn" data-stat="assists">Assists</button>
</div>
```

When a stat is selected, update the chart data without destroying the chart instance:

```javascript
function updateChartStat(chart, games, statKey) {
  chart.data.datasets[0].data = games.map(g => g[statKey]);
  chart.data.datasets[0].label = statKey.charAt(0).toUpperCase() + statKey.slice(1);
  chart.update();
}
```

### CSS additions

```css
.stat-selector {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.stat-btn {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--surface-color);
  cursor: pointer;
}

.stat-btn.active {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.no-data-message {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}
```

### Edge cases to handle

- **Empty games array:** Show "No games data available for this player"
- **Missing stat fields:** Skip games where the selected stat is `null` or `undefined`; do not substitute zero values for missing data
- **Single game:** Chart still renders correctly with a single data point
- **Very long game histories:** Limit display to last 10-20 games; add a "Show more" control if needed
- **Artifact fetch failure:** Show error message in the chart area; do not break the data browser

### Verification

1. Select a player with game data -- chart renders with points over recent games
2. Toggle to "Assists" -- chart updates without page reload
3. Select a different player -- chart updates with new data
4. Select a player with no data -- "No data available" message displays
5. Resize browser to mobile width -- chart reflows responsively
6. Hover over data points -- tooltips display correctly
7. Select a team -- team-level chart renders with appropriate stats
