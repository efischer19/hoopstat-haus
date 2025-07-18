---
title: "ADR-004: Use pytest as the Testing Framework"
status: "Accepted"
date: "2025-07-16"
tags:
  - "python"
  - "testing"
  - "quality"
---

## Context

* **Problem:** We need a robust, feature-rich testing framework for all Python applications that supports unit tests, integration tests, and provides excellent debugging capabilities and extensibility.
* **Constraints:** The framework should be widely adopted, well-documented, support modern Python features, integrate well with CI/CD systems, and provide clear test output and reporting.

## Decision

We will use **pytest** as the standard testing framework for all Python applications in the Hoopstat Haus project.

## Considered Options

1. **pytest (The Chosen One):** Modern, feature-rich testing framework.
   * *Pros:* Excellent fixture system, powerful assertion introspection, extensive plugin ecosystem, supports parametrized tests, great error reporting, backward compatible with unittest, active development
   * *Cons:* Slightly more complex than unittest for very simple cases, additional dependency

2. **unittest:** Python's built-in testing framework.
   * *Pros:* Built into Python standard library, no additional dependencies, familiar to developers from other xUnit frameworks
   * *Cons:* More verbose syntax, limited fixture capabilities, less powerful assertion messages, fewer advanced features

3. **nose2:** Successor to the nose testing framework.
   * *Pros:* Extension of unittest with additional features, plugin support
   * *Cons:* Less active development, smaller ecosystem compared to pytest, not as feature-rich

## Consequences

* **Positive:** Powerful fixture system enables clean test setup and teardown, excellent assertion introspection provides clear failure messages, extensive plugin ecosystem for specialized testing needs, parametrized tests reduce code duplication, great integration with IDEs and CI/CD systems.
* **Negative:** Additional dependency beyond Python standard library, requires learning pytest-specific patterns and fixtures for developers unfamiliar with it.
* **Future Implications:** All Python projects will include pytest in their dependencies and use pytest patterns for testing. This enables consistent testing approaches across projects and leverages the rich pytest ecosystem for specialized testing needs (coverage, mocking, etc.).