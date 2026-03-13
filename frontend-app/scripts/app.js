/**
 * Hoopstat Haus - Frontend Application
 * Data browser for basketball analytics artifacts served via CloudFront
 */

// Configuration
const CONFIG = {
  // CloudFront distribution base URL for Gold JSON artifacts.
  // The CloudFront origin_path is "/served", so client paths omit that prefix.
  // DEPLOY: Replace this placeholder with the actual domain from:
  //   cd infrastructure && terraform output cloudfront_distribution
  // or a configured vanity domain (e.g. "https://hoopstat.haus").
  GOLD_BASE_URL: 'https://CLOUDFRONT_DOMAIN_PLACEHOLDER',
  REQUEST_TIMEOUT_MS: 10000,
};

// Application state
const state = {
  isLoading: false,
  latestDate: null,
  indexData: null,
  activeTab: 'players',
};

// DOM elements
let elements = {};

// ---------------------------------------------------------------------------
// Fetch utility
// ---------------------------------------------------------------------------

async function fetchArtifact(path) {
  const controller = new AbortController();
  const timeoutId = setTimeout(
    () => controller.abort(),
    CONFIG.REQUEST_TIMEOUT_MS,
  );

  try {
    const response = await fetch(`${CONFIG.GOLD_BASE_URL}/${path}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch ${path}: HTTP ${response.status}`);
    }

    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('json') && !contentType.includes('octet-stream')) {
      throw new Error(`Unexpected content type for ${path}: ${contentType}`);
    }

    return response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

function initializeApp() {
  elements = {
    latestBanner: document.getElementById('latest-banner'),
    latestDate: document.getElementById('latest-date'),
    latestSummary: document.getElementById('latest-summary'),
    refreshBtn: document.getElementById('refresh-btn'),
    loadingIndicator: document.getElementById('loading-indicator'),
    selectorContainer: document.getElementById('selector-container'),
    tabPlayers: document.getElementById('tab-players'),
    tabTeams: document.getElementById('tab-teams'),
    panelPlayers: document.getElementById('panel-players'),
    panelTeams: document.getElementById('panel-teams'),
    playerSelect: document.getElementById('player-select'),
    teamSelect: document.getElementById('team-select'),
    dataLoading: document.getElementById('data-loading'),
    dataContainer: document.getElementById('data-container'),
    dataTitle: document.getElementById('data-title'),
    dataContent: document.getElementById('data-content'),
    errorContainer: document.getElementById('error-container'),
    errorMessage: document.getElementById('error-message'),
    retryBtn: document.getElementById('retry-btn'),
  };

  attachEventListeners();
  initChartSection();
  loadIndex();

  console.log('Hoopstat Haus app initialized');
}

function attachEventListeners() {
  elements.refreshBtn.addEventListener('click', loadIndex);
  elements.retryBtn.addEventListener('click', loadIndex);

  elements.tabPlayers.addEventListener('click', () => switchTab('players'));
  elements.tabTeams.addEventListener('click', () => switchTab('teams'));

  elements.playerSelect.addEventListener('change', handlePlayerSelect);
  elements.teamSelect.addEventListener('change', handleTeamSelect);
}

// ---------------------------------------------------------------------------
// Index loading
// ---------------------------------------------------------------------------

async function loadIndex() {
  hideError();
  hideData();
  elements.latestBanner.style.display = 'none';
  elements.selectorContainer.style.display = 'none';
  elements.loadingIndicator.style.display = 'flex';

  try {
    const data = await fetchArtifact('index/latest.json');
    state.indexData = data;
    state.latestDate = getLatestDate(data);

    displayBanner(data);
    populateSelectors(data);

    elements.selectorContainer.style.display = 'block';
  } catch (err) {
    showError(getErrorMessage(err));
  } finally {
    elements.loadingIndicator.style.display = 'none';
  }
}

// ---------------------------------------------------------------------------
// Banner
// ---------------------------------------------------------------------------

function displayBanner(data) {
  const dateStr = getLatestDate(data) || 'Unknown';
  elements.latestDate.textContent = `Latest data: ${dateStr}`;

  const players = data.players || [];
  const teams = data.teams || [];
  const parts = [];
  if (players.length) parts.push(`${players.length} players`);
  if (teams.length) parts.push(`${teams.length} teams`);
  elements.latestSummary.textContent = parts.length
    ? parts.join(', ')
    : '';

  elements.latestBanner.style.display = 'flex';
}

// ---------------------------------------------------------------------------
// Selectors
// ---------------------------------------------------------------------------

function populateSelectors(data) {
  const players = data.players || [];
  const teams = data.teams || [];

  populateSelect(
    elements.playerSelect,
    players,
    '-- Select a player --',
  );
  populateSelect(
    elements.teamSelect,
    teams,
    '-- Select a team --',
  );
}

function populateSelect(selectEl, items, placeholder) {
  selectEl.innerHTML = '';
  const defaultOpt = document.createElement('option');
  defaultOpt.value = '';
  defaultOpt.textContent = placeholder;
  selectEl.appendChild(defaultOpt);

  items.forEach(item => {
    const opt = document.createElement('option');
    const id = getItemId(item);
    opt.value = id;
    opt.textContent = getItemName(item, id);
    selectEl.appendChild(opt);
  });
}

// ---------------------------------------------------------------------------
// Tab switching
// ---------------------------------------------------------------------------

function switchTab(tab) {
  state.activeTab = tab;

  const isPlayers = tab === 'players';
  elements.tabPlayers.classList.toggle('active', isPlayers);
  elements.tabTeams.classList.toggle('active', !isPlayers);
  elements.tabPlayers.setAttribute('aria-selected', String(isPlayers));
  elements.tabTeams.setAttribute('aria-selected', String(!isPlayers));
  elements.panelPlayers.style.display = isPlayers ? 'block' : 'none';
  elements.panelTeams.style.display = isPlayers ? 'none' : 'block';

  hideData();
}

// ---------------------------------------------------------------------------
// Selection handlers
// ---------------------------------------------------------------------------

async function handlePlayerSelect() {
  const playerId = elements.playerSelect.value;
  if (!playerId) {
    hideData();
    return;
  }
  const date = state.latestDate;
  await loadArtifact(`player_daily/${date}/${playerId}.json`, 'Player Stats');
}

async function handleTeamSelect() {
  const teamId = elements.teamSelect.value;
  if (!teamId) {
    hideData();
    return;
  }
  const date = state.latestDate;
  await loadArtifact(`team_daily/${date}/${teamId}.json`, 'Team Stats');
}

async function loadArtifact(path, title) {
  hideError();
  hideData();
  elements.dataLoading.style.display = 'flex';

  try {
    const data = await fetchArtifact(path);
    showData(data, title);
  } catch (err) {
    showError(getErrorMessage(err));
  } finally {
    elements.dataLoading.style.display = 'none';
  }
}

// ---------------------------------------------------------------------------
// Data display
// ---------------------------------------------------------------------------

function showData(data, title) {
  elements.dataTitle.textContent = title;
  elements.dataContent.innerHTML = formatArtifact(data);
  elements.dataContainer.style.display = 'block';
  elements.dataContainer.scrollIntoView({ behavior: 'smooth' });
}

function hideData() {
  elements.dataContainer.style.display = 'none';
}

function formatArtifact(data) {
  if (typeof data !== 'object' || data === null) {
    return `<p>${escapeHtml(String(data))}</p>`;
  }

  // Build stat cards for top-level scalar values and tables for nested data
  let cardsHtml = '';
  let tablesHtml = '';

  for (const [key, value] of Object.entries(data)) {
    if (value === null || value === undefined) continue;

    if (Array.isArray(value)) {
      tablesHtml += renderArraySection(key, value);
    } else if (typeof value === 'object') {
      tablesHtml += renderObjectSection(key, value);
    } else {
      cardsHtml += `<div class="stat-card">
        <span class="stat-label">${escapeHtml(formatLabel(key))}</span>
        <span class="stat-value">${escapeHtml(String(value))}</span>
      </div>`;
    }
  }

  let html = '';
  if (cardsHtml) {
    html += `<div class="stat-cards">${cardsHtml}</div>`;
  }
  if (tablesHtml) {
    html += tablesHtml;
  }
  return html || '<p>No data available.</p>';
}

function renderObjectSection(key, obj) {
  let rows = '';
  for (const [k, v] of Object.entries(obj)) {
    rows += `<tr>
      <td>${escapeHtml(formatLabel(k))}</td>
      <td>${escapeHtml(String(v ?? ''))}</td>
    </tr>`;
  }
  return `<div class="data-section">
    <h3>${escapeHtml(formatLabel(key))}</h3>
    <table class="stats-table"><tbody>${rows}</tbody></table>
  </div>`;
}

function renderArraySection(key, arr) {
  if (arr.length === 0) return '';
  const first = arr[0];

  if (typeof first !== 'object' || first === null) {
    const items = arr.map(v => `<li>${escapeHtml(String(v))}</li>`).join('');
    return `<div class="data-section">
      <h3>${escapeHtml(formatLabel(key))}</h3>
      <ul>${items}</ul>
    </div>`;
  }

  const headers = Object.keys(first);
  const thRow = headers.map(h => `<th>${escapeHtml(formatLabel(h))}</th>`).join('');
  const bodyRows = arr
    .map(row => {
      const cells = headers
        .map(h => `<td>${escapeHtml(String(row[h] ?? ''))}</td>`)
        .join('');
      return `<tr>${cells}</tr>`;
    })
    .join('');

  return `<div class="data-section">
    <h3>${escapeHtml(formatLabel(key))}</h3>
    <div class="table-wrapper">
      <table class="stats-table">
        <thead><tr>${thRow}</tr></thead>
        <tbody>${bodyRows}</tbody>
      </table>
    </div>
  </div>`;
}

// ---------------------------------------------------------------------------
// Error display
// ---------------------------------------------------------------------------

function showError(message) {
  elements.errorMessage.textContent = message;
  elements.errorContainer.style.display = 'block';
  elements.errorContainer.scrollIntoView({ behavior: 'smooth' });
}

function hideError() {
  elements.errorContainer.style.display = 'none';
}

// ---------------------------------------------------------------------------
// Utility functions
// ---------------------------------------------------------------------------

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatLabel(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Extract the latest date from index data.
 * Supports both "date" and "latest_date" field names to handle
 * potential schema variations in the Gold index artifact.
 */
function getLatestDate(data) {
  return data.date || data.latest_date || null;
}

/**
 * Get a display-friendly identifier from a player or team entry.
 * The index artifact may use "id", "player_id", or "team_id" depending
 * on the entry type, so we check all variants defensively.
 */
function getItemId(item) {
  return item.id || item.player_id || item.team_id || '';
}

/**
 * Get a display-friendly name from a player or team entry.
 * Supports "name", "full_name", and "team_name" field variants.
 */
function getItemName(item, fallbackId) {
  return item.name || item.full_name || item.team_name || `ID ${fallbackId}`;
}

function getErrorMessage(error) {
  if (error.name === 'AbortError') {
    return 'Request timed out. Please try again.';
  }

  const msg = error.message || '';
  if (msg.includes('HTTP 404')) {
    return 'Data not found. The requested resource may not be available yet.';
  }
  if (msg.includes('HTTP 5')) {
    return 'Server error. Please try again later.';
  }
  if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
    return 'Network error. Please check your connection and try again.';
  }

  return 'Something went wrong. Please try again.';
}

// ---------------------------------------------------------------------------
// Chart utilities
// ---------------------------------------------------------------------------

/**
 * Create a time-series line chart on the given canvas element.
 * Returns the Chart instance, or null if the canvas or Chart.js is unavailable.
 * Supports updating data in-place via the returned instance.
 */
function createTimeSeriesChart(canvasId, labels, datasets, options) {
  var ctx = document.getElementById(canvasId);
  if (!ctx) {
    console.warn("Canvas element '" + canvasId + "' not found");
    return null;
  }
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js library not loaded');
    return null;
  }

  var mergedOptions = Object.assign(
    {},
    {
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
    },
    options || {},
  );

  return new Chart(ctx, {
    type: 'line',
    data: { labels: labels, datasets: datasets },
    options: mergedOptions,
  });
}

/**
 * Update an existing Chart instance with new labels and datasets
 * without destroying and recreating it.
 */
function updateChartData(chart, labels, datasets) {
  if (!chart) return;
  chart.data.labels = labels;
  chart.data.datasets = datasets;
  chart.update();
}

/**
 * Progressive enhancement: show fallback message when Chart.js
 * is unavailable (e.g. CDN failure, network blocked).
 */
function initChartSection() {
  var section = document.getElementById('chart-section');
  if (!section) return;

  if (typeof Chart === 'undefined') {
    section.style.display = 'block';
    section.innerHTML =
      '<p class="chart-fallback">Charts unavailable. Data is displayed below.</p>';
  }
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}

// Export for testing (if needed)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    CONFIG,
    escapeHtml,
    formatLabel,
    formatArtifact,
    getErrorMessage,
    getLatestDate,
    getItemId,
    getItemName,
    fetchArtifact,
    createTimeSeriesChart,
    updateChartData,
    initChartSection,
  };
}