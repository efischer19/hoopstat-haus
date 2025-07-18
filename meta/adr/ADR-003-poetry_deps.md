---
title: "ADR-003: Use Poetry for Dependency Management"
status: "Accepted"
date: "2025-07-16"
tags:
  - "python"
  - "dependencies"
  - "tooling"
---

## Context

* **Problem:** Python applications require a robust dependency management system to handle package installation, version resolution, virtual environments, and dependency locking for reproducible builds.
* **Constraints:** The chosen tool must support modern Python packaging standards, provide deterministic builds, integrate well with CI/CD pipelines, and offer a good developer experience.

## Decision

We will use **Poetry** for dependency management across all Python applications in the Hoopstat Haus project.

## Considered Options

1. **Poetry (The Chosen One):** Modern dependency management and packaging tool.
   * *Pros:* Excellent dependency resolution, built-in virtual environment management, lock file for reproducible builds, modern pyproject.toml configuration, great developer experience, active development
   * *Cons:* Additional tool to learn, slightly more complex for simple projects, can be slower than pip for some operations

2. **pip + pip-tools:** Traditional pip with pip-tools for lock files.
   * *Pros:* Familiar to most Python developers, minimal learning curve, fast package installation
   * *Cons:* Manual virtual environment management, separate tools for different concerns, no built-in project configuration

3. **Pipenv:** Alternative modern dependency management tool.
   * *Pros:* Good dependency resolution, integrated virtual environment management
   * *Cons:* Slower performance, less active development recently, more complex dependency resolution can be problematic

## Consequences

* **Positive:** Reproducible builds through lock files, simplified virtual environment management, modern configuration through pyproject.toml, excellent dependency resolution preventing conflicts, integrated build and publish capabilities.
* **Negative:** Developers need to learn Poetry if unfamiliar, slightly longer initial setup time for simple projects, potential performance overhead for very large dependency sets.
* **Future Implications:** All Python projects will use pyproject.toml for configuration, enabling standardized tooling and scripts across projects. This decision supports our goal of creating consistent, maintainable Python applications.