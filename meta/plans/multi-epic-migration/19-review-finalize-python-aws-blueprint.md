# feat: Review and finalize python-aws-data-blueprint

## What do you want to build?

A thorough review and validation pass on the `python-aws-data-blueprint` template repository. Verify that the AWS integration scaffolding, medallion architecture example, and CI/CD workflows are correct and complete.

## Acceptance Criteria

- [ ] Create a test repository from the template using GitHub's "Use this template" feature
- [ ] Verify all example apps pass `poetry install && poetry run ruff format --check . && poetry run ruff check . && poetry run pytest`
- [ ] Verify the CI workflow runs and passes (linting, testing)
- [ ] Verify Terraform files are syntactically valid (`terraform validate` with placeholder values)
- [ ] Verify all Dockerfiles build successfully
- [ ] Verify all AWS placeholder values are clearly marked and documented
- [ ] Verify the medallion architecture documentation is clear and accurate
- [ ] Verify no hoopstat-specific content, credentials, or account IDs remain
- [ ] Verify the infrastructure workflow is syntactically valid
- [ ] All pre-commit hooks pass
- [ ] Delete the test repository after validation
- [ ] Tag the repository as `v1.0.0` after all checks pass

## Implementation Notes (Optional)

This is the most complex blueprint and the one with the highest risk of containing hoopstat-specific content that shouldn't be there. Be especially thorough in checking for:
- AWS account IDs (should be `123456789012` or similar placeholder)
- S3 bucket names (should be generic, using `var.project_name`)
- IAM role ARNs (should use placeholder format)
- Region-specific values (should use `var.aws_region`)
- Any references to NBA, basketball, hoopstat, or specific data sources

For Terraform validation:
- Run `terraform init -backend=false` and `terraform validate` to check syntax
- Don't try to `plan` or `apply` — there are no credentials

For Docker builds:
- Build each example app's Docker image locally
- Verify the Lambda handler entry point is correctly configured
- Don't try to deploy — just verify the image builds

Cross-reference against the file-mapping document (ticket 01) to ensure the template includes everything mapped to `python-aws-data-blueprint`.
