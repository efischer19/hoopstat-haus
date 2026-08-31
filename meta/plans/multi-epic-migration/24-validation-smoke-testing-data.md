# feat: Validation and smoke testing for hoopstat-data

## What do you want to build?

Comprehensive validation that the hoopstat-data repository is functional: all code passes quality checks, CI runs green, Docker images build, and the pipeline can be invoked locally (without real AWS resources).

## Acceptance Criteria

- [ ] `scripts/local-ci-check.sh` passes for every app and lib directory
- [ ] The CI workflow runs and all jobs pass on a PR to main
- [ ] Docker images build successfully for all apps with Dockerfiles
- [ ] `terraform validate` passes for the infrastructure directory
- [ ] MkDocs documentation builds successfully
- [ ] Pre-commit hooks pass on the entire repository
- [ ] At least one app can be invoked locally with mock data (e.g., using hoopstat-mock-data fixtures)
- [ ] The MCP proxy's TypeScript component builds (if applicable)
- [ ] All tests pass (unit and integration where applicable)
- [ ] No references to the old hoopstat-haus repository remain in code (except in ADRs/docs as historical references)
- [ ] README accurately describes the project and its setup

## Implementation Notes (Optional)

This is the "definition of done" for the hoopstat-data migration. Run through this checklist methodically:

1. **Quality checks:** Run `scripts/local-ci-check.sh` for each app and lib
2. **Docker builds:** Run `docker build` for each app with a Dockerfile
3. **Terraform:** Run `terraform init -backend=false && terraform validate`
4. **Documentation:** Run `mkdocs build`
5. **Local invocation:** Use hoopstat-mock-data to create test fixtures, then run one pipeline stage locally

For the local invocation test:
- The bronze-ingestion app probably can't run without the real NBA API, but the silver-processing and gold-analytics apps can process mock data
- Use the `hoopstat-e2e-testing` library's LocalStack setup for S3 operations
- This validates the code actually works, not just that it compiles

Document any issues found and create follow-up tickets for non-blocking items. Blocking issues should be fixed before declaring this ticket complete.
