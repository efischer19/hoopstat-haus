/**
 * Hoopstat Haus - Frontend Application
 * Minimal JavaScript for basketball analytics interface
 */

// Configuration
const CONFIG = {
  // UI timeouts
  RESPONSE_TIMEOUT_MS: 30000, // 30 seconds
  DEBOUNCE_MS: 300,
};

// Application state
const state = {
  isLoading: false,
};

// DOM elements
let elements = {};

// Initialize the application
function initializeApp() {
  // Cache DOM elements
  elements = {
    form: document.getElementById('question-form'),
    textarea: document.getElementById('basketball-question'),
    submitBtn: document.getElementById('submit-btn'),
    btnText: document.querySelector('.btn-text'),
    btnLoading: document.querySelector('.btn-loading'),
    responseContainer: document.getElementById('response-container'),
    responseContent: document.getElementById('response-content'),
    errorContainer: document.getElementById('error-container'),
    errorMessage: document.getElementById('error-message'),
    newQuestionBtn: document.getElementById('new-question-btn'),
    retryBtn: document.getElementById('retry-btn'),
    exampleBtns: document.querySelectorAll('.example-btn'),
  };
  
  // Attach event listeners
  attachEventListeners();
  
  // Set initial focus
  elements.textarea.focus();
  
  console.log('Hoopstat Haus app initialized');
}

// Attach all event listeners
function attachEventListeners() {
  // Form submission
  elements.form.addEventListener('submit', handleFormSubmit);
  
  // Example button clicks
  elements.exampleBtns.forEach(btn => {
    btn.addEventListener('click', handleExampleClick);
  });
  
  // New question button
  elements.newQuestionBtn.addEventListener('click', resetToNewQuestion);
  
  // Retry button
  elements.retryBtn.addEventListener('click', resetToNewQuestion);
  
  // Auto-resize textarea
  elements.textarea.addEventListener('input', autoResizeTextarea);
  
  // Prevent double submission
  elements.form.addEventListener('submit', e => {
    if (state.isLoading) {
      e.preventDefault();
    }
  });
}

// Handle form submission (stubbed for artifact-fetching UI)
function handleFormSubmit(event) {
  event.preventDefault();
  
  const question = elements.textarea.value.trim();
  if (!question) {
    showError('Please enter a basketball question.');
    return;
  }
  
  // Data fetching will be implemented in a future ticket
}

// Handle example question clicks
function handleExampleClick(event) {
  const question = event.target.dataset.question;
  if (question) {
    elements.textarea.value = question;
    autoResizeTextarea();
    elements.textarea.focus();
  }
}

// UI State Management
function setLoadingState(loading) {
  state.isLoading = loading;
  elements.submitBtn.disabled = loading;
  
  if (loading) {
    elements.btnText.style.display = 'none';
    elements.btnLoading.style.display = 'flex';
  } else {
    elements.btnText.style.display = 'block';
    elements.btnLoading.style.display = 'none';
  }
}

function showResponse(response) {
  elements.responseContent.innerHTML = formatResponse(response);
  elements.responseContainer.style.display = 'block';
  elements.responseContainer.scrollIntoView({ behavior: 'smooth' });
}

function hideResponse() {
  elements.responseContainer.style.display = 'none';
}

function showError(message) {
  elements.errorMessage.textContent = message;
  elements.errorContainer.style.display = 'block';
  elements.errorContainer.scrollIntoView({ behavior: 'smooth' });
}

function hideError() {
  elements.errorContainer.style.display = 'none';
}

// Format response for display
function formatResponse(response) {
  const answer = response.answer || 'No answer available.';
  const confidence = response.confidence ? Math.round(response.confidence * 100) : null;
  const sources = response.sources || [];
  
  let html = `<div class="response-text">${escapeHtml(answer).replace(/\n/g, '<br>')}</div>`;
  
  if (confidence) {
    html += `<div class="response-meta">
      <p><strong>Confidence:</strong> ${confidence}%</p>
    </div>`;
  }
  
  if (sources.length > 0) {
    html += `<div class="response-sources">
      <p><strong>Sources:</strong> ${sources.map(escapeHtml).join(', ')}</p>
    </div>`;
  }
  
  return html;
}

// Utility functions
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function getErrorMessage(error) {
  if (error.name === 'AbortError') {
    return 'Request timed out. Please try again.';
  }
  
  if (error.message?.startsWith('HTTP_')) {
    const status = error.message.split('_')[1];
    switch (status) {
      case '429': return 'Too many requests. Please wait a moment and try again.';
      case '500': return 'Server error. Please try again later.';
      case '503': return 'Service temporarily unavailable. Please try again later.';
      default: return 'Network error. Please check your connection and try again.';
    }
  }
  
  return 'Something went wrong. Please try again.';
}

function autoResizeTextarea() {
  const textarea = elements.textarea;
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

function resetToNewQuestion() {
  elements.textarea.value = '';
  elements.textarea.focus();
  hideResponse();
  hideError();
  autoResizeTextarea();
}

// Initialize when DOM is ready
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
    formatResponse,
    getErrorMessage,
  };
}