---
title: "ADR-005: Use Ruff for Linting and Black for Formatting"
status: "Accepted"
date: "2025-07-16"
tags:
  - "python"
  - "code-quality"
  - "tooling"
  - "formatting"
---

## Context

* **Problem:** We need consistent code formatting and linting across all Python applications to maintain code quality, readability, and catch potential issues early in development.
* **Constraints:** Tools should be fast, configurable, integrate well with editors and CI/CD, follow modern Python best practices, and minimize configuration overhead.

## Decision

We will use **Ruff** for linting and **Black** for code formatting across all Python applications in the Hoopstat Haus project.

## Considered Options

1. **Ruff + Black (The Chosen One):** Modern, fast linter with established formatter.
   * *Pros:* Ruff is extremely fast (written in Rust), covers many linting rules from flake8/pylint/etc., Black is the de facto standard formatter with minimal configuration, excellent IDE integration, very fast execution
   * *Cons:* Two separate tools to manage, Ruff is relatively new (though rapidly adopted)

2. **Ruff alone:** Use Ruff for both linting and formatting (Ruff has formatting capabilities).
   * *Pros:* Single tool for both concerns, extremely fast, comprehensive rule coverage
   * *Cons:* Ruff's formatting is newer and less established than Black, may have different formatting choices than the widely-adopted Black standard

3. **flake8 + Black:** Traditional linter with Black formatter.
   * *Pros:* Well-established tools, Black is the standard formatter, extensive plugin ecosystem for flake8
   * *Cons:* flake8 is significantly slower than Ruff, requires multiple plugins for comprehensive linting

4. **pylint + Black:** Comprehensive linter with Black formatter.
   * *Pros:* Very comprehensive analysis, Black is the standard formatter
   * *Cons:* pylint is very slow, can be overly verbose, requires extensive configuration

## Consequences

* **Positive:** Extremely fast linting and formatting cycles, consistent code style across all projects, comprehensive linting rules catch potential issues early, minimal configuration required, excellent CI/CD integration, Black's opinionated formatting eliminates style debates.
* **Negative:** Developers need to install and configure both tools, potential for rule conflicts between tools (though both are designed to work together), dependency on two separate tool ecosystems.
* **Future Implications:** All Python projects will include both Ruff and Black in their development dependencies, with consistent configuration across projects. Code style discussions are minimized due to Black's opinionated approach. The combination provides fast, comprehensive code quality checks suitable for CI/CD pipelines.