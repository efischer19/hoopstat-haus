---
title: "ADR-016: Shared Library Versioning Strategy"
status: "Accepted"
date: "2025-07-18"
tags:
  - "versioning"
  - "shared-libraries"
  - "monorepo"
  - "dependencies"
---

## Context

* **Problem:** As the Hoopstat Haus monorepo grows with multiple applications consuming shared libraries in `/libs`, we need a clear versioning strategy to manage dependencies, breaking changes, and ensure stable deployments. Without explicit versioning, applications cannot pin to specific library versions, making it difficult to manage breaking changes and rollbacks.
* **Constraints:** Must work within the existing monorepo structure, integrate with Poetry dependency management, support local development workflows, minimize complexity for developers, and align with the project's philosophy of simplicity and static-first design.

## Decision

We will use **Semantic Versioning (SemVer) with monorepo-specific adaptations** for shared libraries, implemented through Poetry's versioning and local path dependencies.

The versioning strategy includes:
1. **Semantic Versioning (MAJOR.MINOR.PATCH)** for all shared libraries
2. **Version synchronization** across library updates within the monorepo
3. **Local path dependencies** for development with optional version pinning for production
4. **Automated version management** through standardized processes

## Considered Options

1. **Semantic Versioning with monorepo adaptations (The Chosen One):** Use SemVer with Poetry and local dependencies.
   * *Pros:* Industry standard, clear breaking change communication, works with Poetry, supports both development and production workflows, minimal tooling overhead
   * *Cons:* Requires manual version management, need to maintain version discipline across team

2. **Git-based versioning with commit SHAs:** Use git commit hashes as version identifiers.
   * *Pros:* Automatic versioning, exact change tracking, no manual version bumps needed
   * *Cons:* Not human-readable, doesn't communicate breaking changes clearly, poor integration with Poetry, complex dependency resolution

3. **Date-based versioning (CalVer):** Use date-based versions like 2025.01.1.
   * *Pros:* Automatic progression, easy to understand release timing
   * *Cons:* Doesn't communicate breaking changes, no semantic meaning for compatibility, less familiar to developers

4. **No explicit versioning (status quo):** Continue with implicit latest versions.
   * *Pros:* Simple for development, no version management overhead
   * *Cons:* Cannot pin dependencies, difficult to manage breaking changes, no rollback capability, unstable applications

## Consequences

* **Positive:** Clear communication of breaking changes through major version bumps, ability to pin applications to specific library versions, support for gradual migration of breaking changes, better stability for production deployments, industry-standard approach familiar to developers.
* **Negative:** Requires manual version management and discipline, additional steps in release process, need for documentation and tooling to support version management workflow.
* **Future Implications:** Enables stable dependency management as the project scales, supports independent deployment timelines for applications, provides foundation for potential future library publishing outside the monorepo, establishes patterns that can be automated as the project grows.