# feat: Review and finalize python-project-blueprint

## What do you want to build?

A thorough review and validation pass on the `python-project-blueprint` template repository. Test that it produces a working Python monorepo when used as a GitHub template.

## Acceptance Criteria

- [ ] Create a test repository from the template using GitHub's "Use this template" feature
- [ ] Verify `poetry install` works in both example app and example lib
- [ ] Verify `poetry run ruff format --check .` passes in both
- [ ] Verify `poetry run ruff check .` passes in both
- [ ] Verify `poetry run pytest` passes in both
- [ ] Verify the CI workflow runs and all jobs pass in the test repo
- [ ] Verify the Docker build workflow runs and produces an artifact
- [ ] Verify the PyPI publish workflow exists but does not trigger on push
- [ ] Verify pre-commit hooks run successfully
- [ ] Verify the templates in `templates/` can be used to scaffold a new app/lib
- [ ] Verify `scripts/local-ci-check.sh` works for the example app and lib
- [ ] No hoopstat-specific content remains
- [ ] Delete the test repository after validation
- [ ] Tag the repository as `v1.0.0` after all checks pass

## Implementation Notes (Optional)

Pay special attention to:
- Path dependencies between example app and example lib — these are the trickiest part of the monorepo pattern and must work correctly
- Poetry lock file generation — the template should either include lock files or document how to generate them
- CI caching — verify that the cache key strategy works (reference hoopstat-haus CI caching pattern)
- The `develop = true` flag in pyproject.toml for path dependencies (this ensures editable installs that always use current source)

Run `scripts/local-ci-check.sh apps/example-app` and `scripts/local-ci-check.sh libs/example-lib` to validate the full local development workflow.
