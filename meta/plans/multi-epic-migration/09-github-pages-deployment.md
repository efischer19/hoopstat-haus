# feat: GitHub Pages deployment workflow for static-js-app-blueprint

## What do you want to build?

Add a GitHub Actions workflow to the `static-js-app-blueprint` template that deploys the static frontend to GitHub Pages. This is the default, platform-agnostic deployment path that requires zero cloud provider configuration.

## Acceptance Criteria

- [ ] `.github/workflows/deploy-pages.yml` exists and deploys `src/` to GitHub Pages
- [ ] The workflow triggers on push to `main` branch
- [ ] The workflow uses `actions/upload-pages-artifact` and `actions/deploy-pages` (official GitHub Actions)
- [ ] The workflow includes a build step placeholder (commented out) for repos that need a build step (e.g., Vite)
- [ ] Environment protection rules are configured for the `github-pages` environment
- [ ] The deployment workflow includes a concurrency group to prevent parallel deploys
- [ ] README documents how to enable GitHub Pages in repository settings
- [ ] A manual workflow dispatch trigger is available for on-demand deploys
- [ ] All action versions are pinned to specific SHA or major version

## Implementation Notes (Optional)

This is the "zero config" deployment path. A user should be able to:
1. Create a repo from this template
2. Enable GitHub Pages in repository settings (Source: GitHub Actions)
3. Push to main
4. See their site live

The workflow should be structured so that adding a build step (e.g., `npm run build`) is a one-line uncomment. Include a comment block showing how to configure this.

Do NOT include any AWS-specific deployment in this workflow — that's ticket 10.
