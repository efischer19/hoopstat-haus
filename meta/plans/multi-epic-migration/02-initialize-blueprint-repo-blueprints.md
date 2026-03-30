# feat: Initialize blueprint-repo-blueprints repository structure

## What do you want to build?

Create the `blueprint-repo-blueprints` repository on GitHub as a **template repository**. This is the language-agnostic grandparent template from which all other blueprint repos will be derived. Set up the foundational directory structure and repository configuration.

## Acceptance Criteria

- [ ] Repository `blueprint-repo-blueprints` is created on GitHub with template repository enabled
- [ ] Top-level directory structure is in place: `meta/`, `meta/adr/`, `meta/plans/`, `docs-src/`, `scripts/`, `.github/`
- [ ] `.gitignore` covers common OS and editor artifacts (no language-specific entries yet)
- [ ] `LICENSE.md` is present (same license as hoopstat-haus)
- [ ] `CODE_OF_CONDUCT.md` is present
- [ ] `SECURITY.md` is present with placeholder contact info
- [ ] Root `README.md` explains the template's purpose and how to use it
- [ ] `.github/pull_request_template.md` is present
- [ ] `.github/ISSUE_TEMPLATE/feature-request.yml` is present
- [ ] ADR template (`meta/adr/TEMPLATE.md`) is present
- [ ] ADR-001 (Use ADRs) is present as an accepted ADR, adapted for general use

## Implementation Notes (Optional)

This is the first repository created in the migration. Everything here sets the tone for all downstream repos.

Key decisions:
- The README should clearly state this is a template repo and link to the "Use this template" GitHub feature.
- Keep the structure minimal — downstream blueprints will add language-specific content.
- The `.github/copilot-instructions.md` will be added in the next ticket (03), not here.
- No CI/CD workflows yet — those come in ticket 04.
- Consider including a `CONTRIBUTING.md` skeleton that downstream repos can customize.
