# feat: CI/CD with PyPI stub and Docker build for python-project-blueprint

## What do you want to build?

Add CI/CD workflows to the `python-project-blueprint` template that demonstrate the full Python project lifecycle: linting, testing, publishing to PyPI (stubbed), and building Docker images (built but not pushed).

## Acceptance Criteria

- [ ] `.github/workflows/ci.yml` exists with jobs for: install dependencies, ruff format check, ruff lint, pytest for each app and lib
- [ ] `.github/actions/setup-python-poetry/action.yml` exists as a reusable composite action (adapted from hoopstat-haus)
- [ ] CI workflow uses caching for Poetry virtual environments (keyed on poetry.lock hash)
- [ ] `.github/workflows/publish.yml` exists with a PyPI publish job that is commented out at the key `twine upload` / `poetry publish` step, with clear instructions on how to enable
- [ ] `.github/workflows/build-docker.yml` exists, builds Docker images for apps with Dockerfiles, and uploads as GitHub Actions artifacts (no ECR push)
- [ ] `.github/workflows/documentation.yml` exists to build and deploy MkDocs documentation (adapted from hoopstat-haus — generalized for any Python project with docs)
- [ ] A minimal `Dockerfile` exists in the example app showing the multi-stage build pattern
- [ ] `.github/dependabot.yml` is updated to monitor pip ecosystem for each app/lib directory
- [ ] All workflows pass on the template repo with the example app/lib
- [ ] ADR for CI/CD strategy is present (adapted from ADR-007)

## Implementation Notes (Optional)

The PyPI publishing workflow should show (but not actually execute) the publish step. Use comments like:
```yaml
# Uncomment the following to enable PyPI publishing:
# - name: Publish to PyPI
#   run: poetry publish --build
#   env:
#     POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
```

The Docker build workflow should:
1. Build the image using the example app's Dockerfile
2. Upload the image as a GitHub Actions artifact (using `docker save` and `actions/upload-artifact`)
3. NOT push to any registry (no ECR, Docker Hub, etc.)
4. Include comments showing how to add a push step

Adapt from hoopstat-haus:
- `.github/actions/setup-python-poetry/action.yml` — Direct copy with minor generalization
- `.github/workflows/ci.yml` — Simplify from the hoopstat-haus version (fewer apps to test)
- `.github/dependabot.yml` — Adapt structure for example app/lib paths

The Dockerfile should use the multi-stage pattern from hoopstat-haus apps (builder stage with Poetry, runtime stage with minimal image).
