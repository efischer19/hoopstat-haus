# feat: Initialize hoopstat-data from python-aws-data-blueprint

## What do you want to build?

Create the `hoopstat-data` repository using the `python-aws-data-blueprint` template. This is the first product repository — it will house the NBA data pipeline, shared libraries, infrastructure, and MCP proxy. Perform initial customization to replace template placeholders with hoopstat-specific values.

## Acceptance Criteria

- [ ] Repository `hoopstat-data` is created from `python-aws-data-blueprint` template
- [ ] Template repository setting is NOT enabled (this is a product repo, not a template)
- [ ] Root `README.md` is updated with hoopstat-data project description
- [ ] All `{{PROJECT_NAME}}` and similar placeholders are replaced with `hoopstat-data` values
- [ ] Repository description and topics are set on GitHub
- [ ] Branch protection rules are configured for `main` (require PR, require CI pass)
- [ ] Example apps from the template are removed (will be replaced by real apps in ticket 21)
- [ ] Example libs from the template are removed (will be replaced by real libs in ticket 21)
- [ ] `.github/copilot-instructions.md` is customized for the hoopstat-data project

## Implementation Notes (Optional)

This is where the template system gets dogfooded. The goal is to validate that cutting a real project from `python-aws-data-blueprint` is indeed a 5-10 minute exercise.

Track how long the initialization actually takes and note any friction points. This feedback should be used to improve the template (file issues against `python-aws-data-blueprint` for any improvements needed).

Key customizations:
- Project name: `hoopstat-data`
- AWS region: Same as current hoopstat-haus (likely `us-east-1`)
- Python version: 3.12+ (same as current)
- The medallion architecture example structure should be left in place temporarily — real apps will replace it in ticket 21

Do NOT migrate any code yet — that's tickets 21-23. This ticket is only about creating the repo and replacing placeholders.
