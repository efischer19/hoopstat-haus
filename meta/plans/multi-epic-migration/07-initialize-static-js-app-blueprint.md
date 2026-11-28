# feat: Initialize static-js-app-blueprint from blueprint-repo-blueprints

## What do you want to build?

Create the `static-js-app-blueprint` repository using the `blueprint-repo-blueprints` template. This repo will serve as a template for building static frontend applications using HTML/CSS/JavaScript (framework-agnostic). Customize the inherited scaffolding for frontend development.

## Acceptance Criteria

- [ ] Repository `static-js-app-blueprint` is created from `blueprint-repo-blueprints` template
- [ ] Template repository setting is enabled
- [ ] Root `README.md` is updated to describe this as a static frontend app template
- [ ] `.gitignore` is updated with frontend-specific entries (node_modules, dist/, .cache, etc.)
- [ ] Directory structure includes a `src/` or `app/` directory for frontend source files
- [ ] `meta/DEVELOPMENT_PHILOSOPHY.md` is retained from the parent template
- [ ] `.github/copilot-instructions.md` is updated with frontend-specific guidance
- [ ] All `{{PROJECT_NAME}}` placeholders are replaced with appropriate defaults or re-templated for this level

## Implementation Notes (Optional)

This template should remain framework-agnostic. It does not enforce vanilla JS vs. React vs. Vue vs. Svelte. The default example should use vanilla HTML/CSS/JS (consistent with ADR-019 from hoopstat-haus), but the structure should accommodate any static build output.

Key decisions:
- Use a `src/` directory rather than `frontend-app/` for the source files (more conventional for general frontend projects)
- Include a minimal `index.html` with semantic HTML structure and basic accessibility attributes
- Do not include a build step by default (vanilla HTML doesn't need one), but document where to add bundler config (e.g., Vite, Webpack)
- ADR-019 (Vanilla HTML/CSS/JS) from hoopstat-haus should be adapted as an example ADR showing framework selection rationale
