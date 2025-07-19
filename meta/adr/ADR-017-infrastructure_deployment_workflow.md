---
title: "ADR-017: Infrastructure Deployment Workflow"
status: "Proposed"
date: "2025-07-18"
tags:
  - "infrastructure"
  - "deployment"
  - "terraform"
  - "github-actions"
  - "automation"
---

## Context

* **Problem:** With Terraform selected as our Infrastructure as Code tool (ADR-010) and GitHub Actions as our CI/CD platform (ADR-007), we need to establish a secure, automated workflow for deploying and managing cloud infrastructure. Manual infrastructure deployment introduces inconsistency, security risks, and lacks proper change review processes.
* **Constraints:** Must integrate with existing GitHub Actions workflows, use secure OIDC authentication (ADR-011), support both automated and manual deployment scenarios, provide clear visibility into infrastructure changes, follow infrastructure-as-code best practices, and maintain the principle that the main branch is always deployable.

## Decision

We will implement a **dedicated GitHub Actions workflow for Terraform infrastructure deployment** that automatically plans infrastructure changes on pull requests and applies approved changes when merged to the main branch.

## Key Components

### Workflow Triggers
1. **Plan on Pull Request:** Automatically generate and display Terraform plan when PRs modify infrastructure files
2. **Apply on Main:** Automatically apply Terraform changes when merged to the main branch  
3. **Manual Deployment:** Support manual plan/apply operations via workflow_dispatch for emergency scenarios

### Security Implementation
- Use GitHub OIDC with AWS IAM roles for keyless authentication
- Temporary tokens with least-privilege access
- No long-lived credentials stored in GitHub secrets
- Proper IAM role trust relationships scoped to the repository

### Validation Pipeline
- Terraform format checking to ensure consistent code style
- Terraform validation to catch configuration errors early
- Plan generation with detailed change preview
- Automated apply only after successful plan validation

### Change Visibility
- Terraform plan output posted as PR comments for review
- Clear workflow status indicators in GitHub Actions UI
- Comprehensive logging of all infrastructure changes
- Integration with existing PR review processes

## Considered Alternatives

1. **Manual Terraform Execution:** Running Terraform commands manually from developer machines.
   * *Pros:* Simple setup, direct control over execution
   * *Cons:* Requires local AWS credentials, no audit trail, inconsistent execution environment, manual process prone to errors

2. **Separate CI/CD Platform:** Using Jenkins, GitLab CI, or other platforms for infrastructure deployment.
   * *Pros:* Potentially more powerful CI/CD features, separation of concerns
   * *Cons:* Additional infrastructure to maintain, contradicts ADR-007 decision, increases complexity

3. **Infrastructure Repository:** Separate repository dedicated to infrastructure code.
   * *Pros:* Clear separation of infrastructure and application code, dedicated access controls
   * *Cons:* Adds coordination complexity, contradicts monorepo approach, requires separate workflow setup

## Consequences

* **Positive:** Infrastructure changes follow the same review process as application code, automated validation prevents common configuration errors, clear audit trail of all infrastructure modifications, secure keyless authentication eliminates credential management overhead, consistent deployment environment across all changes, integration with existing GitHub-based workflows reduces context switching.

* **Negative:** Initial complexity in setting up OIDC trust relationships, debugging infrastructure deployment failures requires understanding of both Terraform and GitHub Actions, potential for workflow failures to block infrastructure updates, requires team familiarity with Terraform plan/apply workflow.

* **Future Implications:** All infrastructure changes will be version-controlled and code-reviewed, emergency infrastructure changes will follow the same automated workflow patterns, team expertise will develop around GitHub Actions + Terraform integration, infrastructure deployment patterns will be reusable for future services and environments, monitoring and alerting for infrastructure changes will integrate with GitHub Actions workflow status.
