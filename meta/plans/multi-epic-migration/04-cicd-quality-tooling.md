# feat: CI/CD quality tooling for blueprint-repo-blueprints

## What do you want to build?

Add CI/CD configuration and code quality tooling to the `blueprint-repo-blueprints` template. Since this is language-agnostic, the tooling focuses on general file hygiene, markdown linting, and a minimal GitHub Actions workflow.

## Acceptance Criteria

- [ ] `.pre-commit-config.yaml` is present with language-agnostic hooks: trailing whitespace, end-of-file fixer, YAML/JSON/TOML validation, check merge conflicts, mixed line ending check
- [ ] `.github/workflows/ci.yml` exists with a basic quality check job: pre-commit hooks run, markdown lint (optional)
- [ ] The CI workflow triggers on push to `main` and on pull requests
- [ ] `.github/dependabot.yml` is present with GitHub Actions ecosystem monitoring
- [ ] `.github/workflows/accept-adrs.yml` or equivalent ADR status workflow is present (adapted from hoopstat-haus)
- [ ] `.github/workflows/dependabot-auto-merge.yml` is present (copy as-is from hoopstat-haus — general convenience workflow)
- [ ] `.github/workflows/validate-dependabot.yml` is present (copy as-is from hoopstat-haus — general CI convenience)
- [ ] All workflows use pinned action versions (not `@latest` or `@main`)
- [ ] A `scripts/local-ci-check.sh` stub exists explaining how to run checks locally
- [ ] The CI pipeline passes on the template repo itself (no false failures from placeholder content)

## Implementation Notes (Optional)

Adapt from hoopstat-haus but strip Python-specific hooks:
- Keep: trailing-whitespace, end-of-file-fixer, check-yaml, check-toml, check-json, check-merge-conflict
- Remove: ruff, black, pytest (these belong in language-specific blueprints)
- The ADR acceptance workflow should check that ADRs in `meta/adr/` don't have status "Proposed" on the main branch — this is a good general practice to carry forward.
- Dependabot should monitor `github-actions` ecosystem only at this level.
- Consider adding a markdown linter (markdownlint) as an optional step for documentation-heavy repos.
