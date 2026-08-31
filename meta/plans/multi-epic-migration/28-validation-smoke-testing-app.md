# feat: Validation and smoke testing for hoopstat-app

## What do you want to build?

Comprehensive validation that the hoopstat-app repository is functional: the frontend renders correctly, CI passes, and the deployment workflow is ready (even if not yet deployed to real AWS resources).

## Acceptance Criteria

- [ ] The frontend renders correctly when served locally (`python -m http.server` in `src/`)
- [ ] All interactive elements work (chart rendering, navigation, data loading from current live endpoints)
- [ ] The health dashboard page renders correctly
- [ ] Pre-commit hooks pass on the entire repository
- [ ] The CI workflow runs and passes on a PR to main
- [ ] The AWS deployment workflow is syntactically valid
- [ ] Lighthouse accessibility audit scores >= 90 on all pages
- [ ] No JavaScript console errors when loading pages
- [ ] No broken links or missing assets
- [ ] README is accurate and complete
- [ ] No references to hoopstat-haus remain (except as historical references in ADRs)

## Implementation Notes (Optional)

For local testing:
1. `cd src && python -m http.server 8080`
2. Open `http://localhost:8080` in a browser
3. Verify the main dashboard loads and renders charts (it will fetch data from the live CloudFront endpoints)
4. Verify the health dashboard loads

For accessibility testing:
- Run Lighthouse in Chrome DevTools on both pages
- Check keyboard navigation
- Verify screen reader compatibility (basic check: all images have alt text, all interactive elements have labels)

For the deployment workflow:
- Don't actually deploy (no AWS credentials yet)
- Verify the workflow YAML is valid
- Check that all referenced secrets/variables are documented

Create follow-up tickets for any issues found. Non-blocking issues can be deferred; blocking issues must be resolved before marking this complete.
