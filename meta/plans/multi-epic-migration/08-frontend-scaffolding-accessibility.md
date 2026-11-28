# feat: Frontend scaffolding with accessibility foundations for static-js-app-blueprint

## What do you want to build?

Add a complete frontend scaffolding to the `static-js-app-blueprint` template with accessibility best practices baked in from the start. The example app should be a minimal but functional static page that demonstrates the template's conventions.

## Acceptance Criteria

- [ ] `src/index.html` exists with semantic HTML5 structure (header, main, nav, footer, etc.)
- [ ] `src/assets/styles.css` exists with a minimal, responsive CSS reset/base
- [ ] `src/scripts/app.js` exists as a minimal JS entry point (or empty placeholder)
- [ ] `src/assets/favicon.svg` exists (generic placeholder)
- [ ] All HTML includes proper accessibility attributes: lang, viewport meta, skip-to-content link, ARIA landmarks, alt text on images
- [ ] Color contrast meets WCAG 2.1 AA minimum (4.5:1 for normal text)
- [ ] The example page is fully navigable via keyboard
- [ ] A `src/README.md` documents the file structure and conventions
- [ ] An `.htmlhintrc` or equivalent HTML linting config is present (optional but recommended)
- [ ] The example page renders correctly in a browser with no JS errors

## Implementation Notes (Optional)

Accessibility is explicitly in scope for this template per the issue description. This means the default scaffolding should make it easy to do the right thing and hard to do the wrong thing.

Include in the README or as inline comments:
- How to test accessibility locally (e.g., using browser DevTools Lighthouse audit)
- Links to WCAG 2.1 quick reference
- Explanation of the semantic HTML structure choices

The CSS should use modern features (custom properties, flexbox/grid) but avoid framework dependencies. Consider including a minimal dark mode toggle as a demonstration of accessible interactive patterns.

Reference hoopstat-haus's `frontend-app/` for patterns that worked well, but generalize the content. The hoopstat-specific Chart.js CDN usage (ADR-036) should NOT be included — that's a project-specific choice.
