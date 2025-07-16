---
title: "ADR-008: Use Monorepo Structure with Top-Level /apps Directory"
status: "Accepted"
date: "2025-07-16"
tags:
  - "repository-structure"
  - "monorepo"
  - "organization"
---

## Context

* **Problem:** As the Hoopstat Haus project grows to include multiple applications (web services, data pipelines, utilities), we need a clear organizational structure that promotes code sharing, consistent tooling, and efficient development workflows.
* **Constraints:** The structure should support multiple related applications, enable shared tooling and configuration, allow for independent deployment of applications, and remain manageable as the project scales.

## Decision

We will use a **monorepo structure with a top-level `/apps` directory** to organize all applications within the Hoopstat Haus project.

The structure will be:
```
/
├── apps/
│   ├── web-dashboard/
│   ├── data-pipeline/
│   └── stats-api/
├── templates/
├── meta/
└── shared/ (future)
```

## Considered Options

1. **Monorepo with /apps directory (The Chosen One):** Single repository with organized application directories.
   * *Pros:* Centralized tooling and configuration, easy code sharing, atomic cross-application changes, single CI/CD setup, shared documentation and standards, simplified dependency management for shared code
   * *Cons:* Larger repository size over time, potential for tighter coupling between applications, single point of failure for repository access

2. **Multi-repo approach:** Separate repository for each application.
   * *Pros:* Clear separation of concerns, independent versioning and deployment, smaller repository sizes, can have different access controls per application
   * *Cons:* Duplicated tooling configuration, difficult to share code between applications, complex dependency management for shared libraries, fragmented documentation

3. **Flat monorepo:** All applications in repository root without organization.
   * *Pros:* Simple structure, easy to navigate initially
   * *Cons:* Becomes cluttered as project grows, no clear separation between different types of applications, difficult to apply different policies to different application types

## Consequences

* **Positive:** Simplified development workflow with shared tooling, easy code sharing between applications, atomic changes across multiple services, centralized documentation and standards, efficient CI/CD with selective building based on changed applications.
* **Negative:** Repository grows larger over time, potential for unintended coupling between applications, requires tooling to handle selective building/testing, all developers need access to entire codebase.
* **Future Implications:** All new applications will be created in the `/apps` directory following consistent patterns. Shared code and utilities can be placed in a future `/shared` directory. CI/CD workflows will be designed to detect changes and build/deploy only affected applications. This structure supports the project's growth while maintaining organization and enabling efficient development practices.