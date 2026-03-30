# feat: Initialize hoopstat-app from static-js-app-blueprint

## What do you want to build?

Create the `hoopstat-app` repository using the `static-js-app-blueprint` template. This is the second product repository — it will house the hoopstat.haus frontend analytics dashboard. Perform initial customization to replace template placeholders with hoopstat-specific values.

## Acceptance Criteria

- [ ] Repository `hoopstat-app` is created from `static-js-app-blueprint` template
- [ ] Template repository setting is NOT enabled (this is a product repo, not a template)
- [ ] Root `README.md` is updated with hoopstat-app project description and link to hoopstat.haus
- [ ] All `{{PROJECT_NAME}}` and similar placeholders are replaced with `hoopstat-app` values
- [ ] Repository description and topics are set on GitHub (e.g., "NBA analytics dashboard", "hoopstat")
- [ ] Branch protection rules are configured for `main` (require PR, require CI pass)
- [ ] The GitHub Pages deployment workflow is disabled (hoopstat-app uses AWS, not Pages)
- [ ] The AWS deployment workflow is enabled and configured with placeholder secrets
- [ ] `.github/copilot-instructions.md` is customized for the hoopstat-app project

## Implementation Notes (Optional)

Like ticket 20 (hoopstat-data), this validates the template system. Track how long initialization takes and note friction points for feedback to the `static-js-app-blueprint` template.

Key customizations:
- Project name: `hoopstat-app`
- Deployment target: AWS S3/CloudFront (not GitHub Pages)
- The example `src/` scaffolding should be left in place temporarily — real content replaces it in ticket 26

Do NOT migrate any frontend code yet — that's ticket 26. This ticket is only about creating the repo and replacing placeholders.
