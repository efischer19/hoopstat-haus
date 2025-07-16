---
title: "ADR-007: Use GitHub Actions for CI/CD and Job Scheduling"
status: "Accepted"
date: "2025-07-16"
tags:
  - "ci-cd"
  - "automation"
  - "github-actions"
---

## Context

* **Problem:** We need a reliable CI/CD platform for automated testing, building, deployment, and scheduled job execution that integrates seamlessly with our GitHub-hosted repository and supports our containerized applications.
* **Constraints:** The platform should integrate natively with GitHub, support Docker builds, provide flexible workflow configuration, offer reasonable pricing/limits for open source projects, and support both push-triggered and scheduled workflows.

## Decision

We will use **GitHub Actions** for all CI/CD workflows and job scheduling in the Hoopstat Haus project.

## Considered Options

1. **GitHub Actions (The Chosen One):** Native GitHub CI/CD platform.
   * *Pros:* Native GitHub integration, no additional service setup required, excellent Docker support, flexible workflow configuration with YAML, large marketplace of pre-built actions, generous free tier for public repositories, supports both event-driven and scheduled workflows
   * *Cons:* Vendor lock-in to GitHub ecosystem, limited customization of runner environments, potential costs for private repositories with heavy usage

2. **Jenkins:** Self-hosted CI/CD server.
   * *Pros:* Highly customizable, extensive plugin ecosystem, complete control over infrastructure
   * *Cons:* Requires self-hosting and maintenance, more complex setup, additional infrastructure costs, requires DevOps expertise

3. **GitLab CI:** GitLab's integrated CI/CD platform.
   * *Pros:* Integrated with GitLab platform, good Docker support, flexible pipeline configuration
   * *Cons:* Would require migrating away from GitHub, additional platform to learn and manage

## Consequences

* **Positive:** Seamless integration with GitHub repository, automated testing and deployment on every push/PR, excellent Docker build and push capabilities, easy setup of scheduled jobs for data pipelines, large ecosystem of community actions, no additional infrastructure to maintain.
* **Negative:** Dependency on GitHub platform, limited control over runner environments, potential vendor lock-in, workflow configurations stored in repository (could be seen as coupling).
* **Future Implications:** All applications will include GitHub Actions workflows for testing, linting, building Docker images, and deployment. Scheduled data processing jobs will be configured as GitHub Actions workflows. This decision supports our goal of automated, reliable software delivery and reduces operational overhead by leveraging managed infrastructure.