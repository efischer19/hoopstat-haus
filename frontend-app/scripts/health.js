/**
 * Hoopstat Haus — Pipeline Health Dashboard
 * Fetches pipeline_health.json and renders status indicators, chart, and table.
 */

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const HEALTH_JSON_URL = '/health/pipeline_health.json';
const REQUEST_TIMEOUT_MS = 10000;

/** Maps status values to CSS class names used for styling. */
const STATUS_CLASS = {
  operational: 'operational',
  success:     'operational',
  degraded:    'degraded',
  failed:      'outage',
  outage:      'outage',
  skipped:     'no-data',
  no_data:     'no-data',
};

/** Human-readable labels for status values. */
const STATUS_LABEL = {
  operational: 'Operational',
  success:     'Operational',
  degraded:    'Degraded',
  failed:      'Failed',
  outage:      'Outage',
  skipped:     'Skipped',
  no_data:     'No Data',
};

/** Unicode icons for pipeline stage statuses in the table. */
const STATUS_ICON = {
  operational: '✓',
  success:     '✓',
  degraded:    '⚠',
  failed:      '✗',
  outage:      '✗',
  skipped:     '—',
  no_data:     '—',
};

/** Chart.js colors for the stacked bar chart. */
const CHART_COLORS = {
  ingested:    'rgba(34, 197, 94, 0.8)',
  quarantined: 'rgba(234, 179, 8, 0.8)',
};

// ---------------------------------------------------------------------------
// DOM helpers
// ---------------------------------------------------------------------------

function show(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = '';
}

function hide(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'none';
}

// ---------------------------------------------------------------------------
// Fetch pipeline_health.json
// ---------------------------------------------------------------------------

async function fetchHealthData() {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(HEALTH_JSON_URL, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

// ---------------------------------------------------------------------------
// Rendering helpers
// ---------------------------------------------------------------------------

/**
 * Format an ISO 8601 UTC timestamp into a human-readable string.
 * e.g. "2026-03-26T06:00:00Z" → "2026-03-26 06:00 UTC"
 */
function formatTimestamp(isoString) {
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    const yyyy = d.getUTCFullYear();
    const mm   = String(d.getUTCMonth() + 1).padStart(2, '0');
    const dd   = String(d.getUTCDate()).padStart(2, '0');
    const hh   = String(d.getUTCHours()).padStart(2, '0');
    const min  = String(d.getUTCMinutes()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd} ${hh}:${min} UTC`;
  } catch {
    return isoString;
  }
}

/**
 * Format a date string (YYYY-MM-DD) as "Mar 26".
 */
function formatDate(dateStr) {
  try {
    const [year, month, day] = dateStr.split('-').map(Number);
    const d = new Date(year, month - 1, day);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return dateStr;
  }
}

/**
 * Render the overall status banner.
 */
function renderBanner(data) {
  const banner = document.getElementById('overall-banner');
  const statusText = document.getElementById('overall-status-text');
  const updatedEl = document.getElementById('overall-updated');

  const cls = STATUS_CLASS[data.overall_status] || 'no-data';
  banner.className = `health-banner ${cls}`;

  const label = STATUS_LABEL[data.overall_status] || data.overall_status;
  statusText.textContent = `System Status: ${label}`;

  updatedEl.textContent = `Last updated: ${formatTimestamp(data.generated_at)}`;
}

/**
 * Render the three stage indicator cards (Bronze, Silver, Gold).
 */
function renderStages(stages) {
  const grid = document.getElementById('stages-grid');
  grid.innerHTML = '';

  const stageNames = [
    { key: 'bronze', label: 'Bronze Ingestion' },
    { key: 'silver', label: 'Silver Processing' },
    { key: 'gold',   label: 'Gold Analytics' },
  ];

  for (const { key, label } of stageNames) {
    const stage = stages[key];
    const cls = stage ? (STATUS_CLASS[stage.status] || 'no-data') : 'no-data';
    const statusLabel = stage ? (STATUS_LABEL[stage.status] || stage.status) : 'No Data';

    let lastSuccessText = '';
    if (stage && stage.last_success_at) {
      lastSuccessText = `Last: ${formatTimestamp(stage.last_success_at)}`;
    }

    const card = document.createElement('div');
    card.className = 'stage-card';
    card.setAttribute('role', 'status');
    card.setAttribute('aria-label', `${label}: ${statusLabel}`);
    card.innerHTML = `
      <div class="stage-dot ${cls}" aria-hidden="true"></div>
      <div class="stage-info">
        <div class="stage-name">${label}</div>
        <div class="stage-status-label ${cls}">${statusLabel}</div>
        ${lastSuccessText ? `<div class="stage-last-success">${lastSuccessText}</div>` : ''}
      </div>
    `;
    grid.appendChild(card);
  }
}

/**
 * Render the Chart.js stacked bar chart.
 * If Chart.js is not available, show the fallback message.
 */
function renderChart(dailySummaries) {
  if (typeof Chart === 'undefined') {
    hide('health-chart');
    show('chart-unavailable');
    return;
  }

  // Build chart data in chronological order (oldest → newest)
  const summaries = [...dailySummaries].reverse();
  const labels     = summaries.map(s => formatDate(s.date));
  const ingested   = summaries.map(s => s.silver ? s.silver.records_processed : 0);
  const quarantine = summaries.map(s => s.silver ? s.silver.records_quarantined : 0);

  const canvas = document.getElementById('health-chart');
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Records Ingested',
          data: ingested,
          backgroundColor: CHART_COLORS.ingested,
          stack: 'records',
        },
        {
          label: 'Records Quarantined',
          data: quarantine,
          backgroundColor: CHART_COLORS.quarantined,
          stack: 'records',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: { mode: 'index', intersect: false },
      },
      scales: {
        x: { stacked: true },
        y: {
          stacked: true,
          beginAtZero: true,
          ticks: { precision: 0 },
        },
      },
    },
  });
}

/**
 * Render the daily breakdown table body.
 */
function renderTable(dailySummaries) {
  const tbody = document.getElementById('daily-table-body');
  tbody.innerHTML = '';

  for (const summary of dailySummaries) {
    const bronzeStatus  = summary.bronze ? summary.bronze.status   : 'no_data';
    const silverStatus  = summary.silver ? summary.silver.status   : 'no_data';
    const goldStatus    = summary.gold   ? summary.gold.status     : 'no_data';
    const quarantined   = summary.silver ? summary.silver.records_quarantined : 0;

    const bronzeIcon  = STATUS_ICON[bronzeStatus]  || '—';
    const silverIcon  = STATUS_ICON[silverStatus]  || '—';
    const goldIcon    = STATUS_ICON[goldStatus]    || '—';

    const quarClass   = quarantined > 0 ? 'some' : 'none';
    const row = document.createElement('tr');
    row.innerHTML = `
      <td><time datetime="${summary.date}">${formatDate(summary.date)}</time></td>
      <td class="status-icon" aria-label="Bronze: ${STATUS_LABEL[bronzeStatus] || bronzeStatus}">${bronzeIcon}</td>
      <td class="status-icon" aria-label="Silver: ${STATUS_LABEL[silverStatus] || silverStatus}">${silverIcon}</td>
      <td class="status-icon" aria-label="Gold: ${STATUS_LABEL[goldStatus] || goldStatus}">${goldIcon}</td>
      <td><span class="quarantine-count ${quarClass}">${quarantined}</span></td>
    `;
    tbody.appendChild(row);
  }

  if (dailySummaries.length === 0) {
    const row = document.createElement('tr');
    row.innerHTML = '<td colspan="5" style="text-align:center;color:var(--text-secondary);">No data available</td>';
    tbody.appendChild(row);
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function showError(message) {
  hide('health-loading');
  hide('health-dashboard');
  const msgEl = document.getElementById('health-error-message');
  if (msgEl) msgEl.textContent = message;
  show('health-error');
}

async function loadDashboard() {
  hide('health-error');
  hide('health-dashboard');
  show('health-loading');

  try {
    const data = await fetchHealthData();
    renderBanner(data);
    renderStages(data.stages || {});
    renderChart(data.daily_summaries || []);
    renderTable(data.daily_summaries || []);

    hide('health-loading');
    show('health-dashboard');
  } catch (err) {
    hide('health-loading');
    const msg = err.name === 'AbortError'
      ? 'Request timed out. Please try again later.'
      : 'Unable to load pipeline status. Please try again later.';
    showError(msg);
  }
}

function initHealthDashboard() {
  const retryBtn = document.getElementById('health-retry-btn');
  if (retryBtn) {
    retryBtn.addEventListener('click', loadDashboard);
  }
  loadDashboard();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initHealthDashboard);
} else {
  initHealthDashboard();
}
