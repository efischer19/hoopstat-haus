/**
 * Hoopstat Haus - Frontend Application
 * Data browser for basketball analytics artifacts served via CloudFront
 */

// Configuration
const CONFIG = {
  // CloudFront distribution base URL for Gold JSON artifacts.
  // The CloudFront origin_path is "/served", so client paths omit that prefix.
  // Replace the placeholder domain with the actual Terraform output value.
  GOLD_BASE_URL: 'https://d1example.cloudfront.net',
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
    state.latestDate = data.date || data.latest_date || null;

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
  const dateStr = data.date || data.latest_date || 'Unknown';
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
    opt.value = item.id || item.player_id || item.team_id || '';
    opt.textContent = item.name || item.full_name || item.team_name || `ID ${opt.value}`;
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
    fetchArtifact,
  };
}