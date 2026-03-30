# feat: Initialize python-aws-data-blueprint from python-project-blueprint

## What do you want to build?

Create the `python-aws-data-blueprint` repository using the `python-project-blueprint` template. This repo extends the Python monorepo pattern with AWS integration: Lambda deployment, ECR image management, S3 data storage, and Terraform infrastructure scaffolding.

## Acceptance Criteria

- [ ] Repository `python-aws-data-blueprint` is created from `python-project-blueprint` template
- [ ] Template repository setting is enabled
- [ ] Root `README.md` is updated to describe this as a Python + AWS data project template
- [ ] `.gitignore` is updated with Terraform-specific entries (.terraform/, *.tfstate, *.tfplan, .terraform.lock.hcl)
- [ ] `infrastructure/` directory is created with Terraform scaffolding
- [ ] `.github/copilot-instructions.md` is updated with AWS and Terraform guidance
- [ ] ADR for "AWS as Cloud Provider" is present (adapted from ADR-009)
- [ ] ADR for "Terraform for Infrastructure as Code" is present (adapted from ADR-010)
- [ ] ADR for "GitHub OIDC for AWS Authentication" is present (adapted from ADR-011)
- [ ] Example app from parent template is retained as a starting point

## Implementation Notes (Optional)

This template is the most complex blueprint and the one that directly feeds into `hoopstat-data`. It needs to be comprehensive enough that cutting a real project from it is a "fill in the blanks" exercise.

Key additions over `python-project-blueprint`:
- `infrastructure/` directory with Terraform files
- AWS-specific CI/CD workflows (ECR push, Lambda deployment, Terraform plan/apply)
- Docker build patterns that target Lambda runtime
- S3 interaction patterns in example code

Do NOT include actual AWS credentials, account IDs, or resource ARNs. Use placeholder values throughout.
