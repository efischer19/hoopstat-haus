# Ticket 1: Strip Mock Backend Code from Frontend App

> **Epic:** [Frontend Simplification & Lightweight Visualization](00-executive-summary.md)
> **Sequence:** 1 of 5 (no dependencies -- can start immediately)
> **Governing ADRs:** ADR-019 (Vanilla Frontend), ADR-027 (Stateless Gold Access)

---

## What do you want to build?

Remove all mock backend code, simulated API calls, and dummy data generation from `frontend-app/scripts/app.js`. The current frontend was built around a Q&A interface that assumes a dynamic server-side backend (POST to `/api/v1/ask`). That backend will never be built -- our architecture uses pre-computed Gold JSON artifacts served statically via CloudFront (ADR-027, ADR-035). This ticket cleans the slate so subsequent tickets can rebuild the data layer and UI around the correct architecture.

## Acceptance Criteria

- [ ] `simulateAPICall()` function is removed from `app.js`
- [ ] `generateMockResponse()` function and its canned response array are removed from `app.js`
- [ ] `makeAPICall()` function (POST-based Q&A endpoint call) is removed from `app.js`
- [ ] `CONFIG.ENABLE_API_CALLS` feature flag is removed from the CONFIG object
- [ ] `CONFIG.API_BASE_URL` (pointing to the non-existent `api.hoopstat.haus`) is removed
- [ ] `processQuestion()` no longer references any mock or Q&A API logic
- [ ] The Q&A form submission handler (`handleFormSubmit`) is simplified or stubbed to prepare for the artifact-fetching UI in ticket #2
- [ ] Rate limiting logic tied to the Q&A pattern is removed (a simpler fetch-based pattern will be added in ticket #2 if needed)
- [ ] No JavaScript errors in the browser console after loading `index.html`
- [ ] The app still loads and renders the page skeleton (header, footer, empty main area) without errors

## Implementation Notes (Optional)

### Files to modify

- `frontend-app/scripts/app.js` -- primary target; remove ~100 lines of mock/API code
- `frontend-app/index.html` -- the Q&A form elements (`#question-form`, example buttons, response/error containers) can be left in place for now but are candidates for replacement in ticket #2

### What to remove from `app.js`

| Lines (approx) | Function/Block | Reason |
|-----------------|---------------|--------|
| 7-23 | `CONFIG` object | Remove `API_BASE_URL`, `ENABLE_API_CALLS`; keep `RESPONSE_TIMEOUT_MS` and `DEBOUNCE_MS` if useful |
| 26-31 | `state` object | Remove `currentQuestion`; simplify to loading state only |
| 34-60 | `rateLimiter` | Remove Q&A-pattern rate limiter (not needed for static GET fetches) |
| 150-176 | `processQuestion()` | Remove mock/API branching logic |
| 179-191 | `simulateAPICall()` | Remove entirely |
| 194-209 | `generateMockResponse()` | Remove entirely |
| 212-240 | `makeAPICall()` | Remove entirely |
| 342-347 | `retryLastQuestion()` | Remove (tied to Q&A pattern) |

### What to keep

- DOM initialization pattern (`initializeApp`, `attachEventListeners`)
- UI state management helpers (`setLoadingState`, `showError`, `hideError`)
- Utility functions (`escapeHtml`, `autoResizeTextarea`)
- The `formatResponse` function can be adapted in ticket #2

### Verification

1. Open `index.html` in a browser
2. Confirm no console errors
3. Confirm the page renders its skeleton (header, footer, main area)
4. Confirm removed functions are no longer callable from the console
