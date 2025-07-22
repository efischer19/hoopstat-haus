/**
 * Hoopstat Haus - Frontend Application
 * Minimal JavaScript for basketball analytics interface
 */

// Configuration
const CONFIG = {
  // API endpoints (to be configured when backend is ready)
  API_BASE_URL: window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://api.hoopstat.haus',
  
  // Rate limiting
  MAX_REQUESTS_PER_MINUTE: 10,
  REQUEST_COOLDOWN_MS: 6000, // 6 seconds between requests
  
  // UI timeouts
  RESPONSE_TIMEOUT_MS: 30000, // 30 seconds
  DEBOUNCE_MS: 300,
  
  // Feature flags
  ENABLE_API_CALLS: false, // Will be enabled when backend is ready
};

// Application state
const state = {
  isLoading: false,
  lastRequestTime: 0,
  requestCount: 0,
  currentQuestion: '',
};

// Rate limiting tracker
const rateLimiter = {
  requests: [],
  
  canMakeRequest() {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;
    
    // Clean old requests
    this.requests = this.requests.filter(time => time > oneMinuteAgo);
    
    // Check if under limit
    if (this.requests.length >= CONFIG.MAX_REQUESTS_PER_MINUTE) {
      return false;
    }
    
    // Check cooldown period
    const timeSinceLastRequest = now - state.lastRequestTime;
    return timeSinceLastRequest >= CONFIG.REQUEST_COOLDOWN_MS;
  },
  
  recordRequest() {
    const now = Date.now();
    this.requests.push(now);
    state.lastRequestTime = now;
    state.requestCount++;
  }
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
  elements.retryBtn.addEventListener('click', retryLastQuestion);
  
  // Auto-resize textarea
  elements.textarea.addEventListener('input', autoResizeTextarea);
  
  // Prevent double submission
  elements.form.addEventListener('submit', e => {
    if (state.isLoading) {
      e.preventDefault();
    }
  });
}

// Handle form submission
async function handleFormSubmit(event) {
  event.preventDefault();
  
  const question = elements.textarea.value.trim();
  if (!question) {
    showError('Please enter a basketball question.');
    return;
  }
  
  // Rate limiting check
  if (!rateLimiter.canMakeRequest()) {
    const waitTime = Math.ceil((CONFIG.REQUEST_COOLDOWN_MS - (Date.now() - state.lastRequestTime)) / 1000);
    showError(`Please wait ${waitTime} seconds before asking another question.`);
    return;
  }
  
  state.currentQuestion = question;
  await processQuestion(question);
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

// Process a basketball question
async function processQuestion(question) {
  try {
    setLoadingState(true);
    hideError();
    hideResponse();
    
    // Record request for rate limiting
    rateLimiter.recordRequest();
    
    // Simulate API call if backend not ready
    if (!CONFIG.ENABLE_API_CALLS) {
      await simulateAPICall(question);
      return;
    }
    
    // Make actual API call when backend is ready
    const response = await makeAPICall(question);
    showResponse(response);
    
  } catch (error) {
    console.error('Error processing question:', error);
    showError(getErrorMessage(error));
  } finally {
    setLoadingState(false);
  }
}

// Simulate API call for development/demo purposes
async function simulateAPICall(question) {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 1000));
  
  // Simulate occasional errors for testing
  if (Math.random() < 0.1) {
    throw new Error('NETWORK_ERROR');
  }
  
  // Generate a mock response based on the question
  const mockResponse = generateMockResponse(question);
  showResponse(mockResponse);
}

// Generate mock response for development
function generateMockResponse(question) {
  const responses = [
    {
      answer: `Great question about basketball statistics! Based on your query "${question}", here's what I found:\n\nThis is a simulated response for development purposes. When the backend API is ready, this will be replaced with real basketball analytics powered by AI and comprehensive NBA/WNBA data.\n\nThe system will analyze player statistics, team performance, historical trends, and provide insights in natural language.`,
      confidence: 0.95,
      sources: ['NBA Stats API', 'Historical Database'],
    },
    {
      answer: `Thanks for asking about "${question}"!\n\nThis frontend application is ready to connect to our basketball analytics backend. The interface supports:\n\n• Natural language questions about player performance\n• Team statistics and comparisons\n• Historical data analysis\n• Playoff and season statistics\n\nOnce the API integration is complete, you'll get real-time insights from comprehensive basketball data.`,
      confidence: 0.88,
      sources: ['NBA Official Data', 'WNBA Statistics'],
    }
  ];
  
  return responses[Math.floor(Math.random() * responses.length)];
}

// Make actual API call (for future implementation)
async function makeAPICall(question) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), CONFIG.RESPONSE_TIMEOUT_MS);
  
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/v1/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: question,
        timestamp: new Date().toISOString(),
      }),
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`HTTP_${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
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
  
  if (error.message === 'NETWORK_ERROR') {
    return 'Network error. Please check your connection and try again.';
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

function retryLastQuestion() {
  if (state.currentQuestion) {
    hideError();
    processQuestion(state.currentQuestion);
  }
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
    rateLimiter,
    processQuestion,
    generateMockResponse,
  };
}