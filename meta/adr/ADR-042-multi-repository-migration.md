---
title: "Record 042: Multi-Repository Migration Strategy"
status: "Proposed"
date: "2026-03-30"
tags:
  - "architecture"
  - "repository-structure"
  - "templates"
  - "migration"
---

## Context

* **Problem:** The hoopstat-haus monorepo has served as a successful proving ground for the data pipeline, frontend, infrastructure, and development practices. However, the repository now contains tightly coupled concerns (data pipeline, frontend app, infrastructure, documentation tooling, AI instructions) that would benefit from separation. Additionally, the patterns and conventions we've established are valuable beyond this single project and should be extractable as reusable templates for future work.

* **Constraints:**
  - The migration must not cause downtime for the live hoopstat.haus site or data pipeline.
  - Existing CI/CD patterns, ADRs, and development philosophy must be preserved and carried forward.
  - AWS infrastructure (S3, Lambda, CloudFront, ECR) must be cleanly transitioned to new repository contexts.
  - GitHub OIDC tokens (ADR-011) are repository-scoped and must be re-provisioned per new repo.
  - The migration should produce reusable template repositories, not just a one-time split.

## Decision

We will decompose the hoopstat-haus monorepo into a hierarchy of template ("blueprint") repositories and two product repositories, migrated in a specific sequence:

1. **`blueprint-repo-blueprints`** — Language-agnostic grandparent template containing development philosophy, meta structure, AI instructions, and common documentation scaffolding.
2. **`static-js-app-blueprint`** — Cut from (1); template for static frontend applications with GitHub Pages default and optional AWS S3/CloudFront deployment.
3. **`python-project-blueprint`** — Cut from (1); template for Python monorepo projects with Poetry, apps/libs structure, CI/CD, and stub PyPI/Docker publishing.
4. **`python-aws-data-blueprint`** — Extended from (3); adds AWS integration (Lambda, ECR, Terraform, S3, medallion architecture scaffolding).
5. **`hoopstat-data`** — Cut from (4); receives all data pipeline apps, shared libraries, and infrastructure from the current monorepo.
6. **`hoopstat-app`** — Cut from (2); receives the frontend application with AWS deployment configuration.

After both product repos are operational, the original hoopstat-haus repository will be archived.

## Considered Options

1. **Layered Blueprint + Product Repo Split (Chosen)**
   * *Pros:* Produces reusable templates that accelerate future projects; enforces separation of concerns; each repo has a clear, single purpose; templates can be independently versioned and improved; dogfoods the template system with the real product.
   * *Cons:* Significant upfront planning and execution effort; requires careful sequencing to avoid downtime; template repos need ongoing maintenance; increases the number of repositories to manage.

2. **Direct Monorepo Split (No Templates)**
   * *Pros:* Simpler and faster; fewer repositories to create; direct migration path.
   * *Cons:* Loses the reusability value; doesn't capture lessons learned as templates; future projects would start from scratch; doesn't address the "build a platform" goal.

3. **Keep Monorepo, Improve Internal Boundaries**
   * *Pros:* No migration needed; existing CI/CD continues to work; single repo simplifies discovery.
   * *Cons:* Doesn't address the cross-cutting concern problem; frontend and data pipeline remain coupled; no reusable templates produced; doesn't scale to additional projects.

## Consequences

* **Positive:**
  - Reusable template repos enable spinning up new projects in 5-10 minutes.
  - Clear separation of concerns: data pipeline, frontend, and infrastructure each have a dedicated home.
  - Each product repo can have independent CI/CD, secrets, and deployment lifecycles.
  - The template hierarchy ensures consistency across all derived projects.
  - Development philosophy and conventions are codified in templates rather than tribal knowledge.

* **Negative:**
  - Migration involves a coordination window where both old and new repos may be active.
  - GitHub OIDC tokens, secrets, and scheduled workflows must be re-provisioned for each new repo.
  - Cross-repo changes (e.g., shared library updates) require more coordination than monorepo changes.
  - Template maintenance becomes an ongoing responsibility.

* **Future Implications:**
  - New projects (beyond hoopstat) can be bootstrapped from the blueprint repos.
  - The blueprint-repo-blueprints template can evolve to support additional language ecosystems.
  - ADRs from hoopstat-haus should be selectively migrated to relevant repos; project-specific ADRs go to product repos, general ADRs go to blueprints.
  - The MCP proxy app may warrant its own repository or PyPI package in the future.
