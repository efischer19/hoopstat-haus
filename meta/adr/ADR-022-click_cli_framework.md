---
title: "ADR-022: Use Click for Command Line Interfaces"
status: "Proposed"
date: "2025-01-27"
tags:
  - "cli"
  - "user-interface"
  - "tooling"
  - "python"
---

## Context

* **Problem:** Data pipeline applications and administrative tools require command line interfaces for operation, debugging, and automation. A consistent, feature-rich CLI framework is needed to provide user-friendly interfaces for data ingestion jobs, system administration tasks, and development tooling across all applications.
* **Constraints:** The CLI solution must provide intuitive command grouping and subcommands, support for various argument types and validation, generate helpful documentation and help text automatically, integrate well with Python's ecosystem and typing, support for configuration files and environment variables, enable easy testing of CLI functionality, and maintain consistency across all applications in the monorepo.

## Decision

We will use **Click** as the standard framework for building command line interfaces across all Hoopstat Haus applications.

## Considered Options

1. **Click (The Chosen One):** Modern, composable command line interface creation toolkit.
   * *Pros:* Decorator-based interface for clean, readable code, excellent support for command groups and subcommands, automatic help generation and documentation, robust argument parsing with type validation, built-in support for configuration files and environment variables, excellent testing utilities for CLI applications, Unicode and color support for rich output, extensive plugin ecosystem, mature and actively maintained, strong integration with Flask ecosystem
   * *Cons:* Additional dependency to manage, slight learning curve for complex command structures, decorator syntax may be unfamiliar to some developers

2. **argparse:** Python's built-in command line parsing library.
   * *Pros:* No additional dependencies, part of Python standard library, familiar to most Python developers, well-documented and stable, sufficient for basic CLI needs
   * *Cons:* Verbose syntax for complex command structures, limited support for command groups and subcommands, manual help text generation, basic type validation, no built-in configuration file support, difficult to test, limited formatting options for output

3. **Typer:** Modern CLI framework built on top of Click with type hints.
   * *Pros:* Type hint-based interface, automatic validation from type annotations, built on Click foundation, modern Python syntax, excellent IDE support
   * *Cons:* Newer library with smaller ecosystem, additional abstraction layer over Click, requires Python 3.6+ type hint knowledge, less mature than Click, fewer examples and tutorials available

4. **Fire:** Google's Python library for automatically generating CLIs.
   * *Pros:* Automatic CLI generation from any Python object, minimal boilerplate code, easy to add CLI to existing functions, good for rapid prototyping
   * *Cons:* Less control over CLI structure and help text, magic behavior can be confusing, limited customization options, not designed for complex CLI applications, poor error handling and validation

## Consequences

* **Positive:** Consistent, professional command line interfaces across all applications, reduced development time through comprehensive CLI framework, automatic help generation and documentation, robust argument validation and error handling, excellent testing capabilities for CLI functionality, support for complex command structures and workflows, enhanced developer experience with rich output formatting, standardized approach to configuration and environment variable handling.
* **Negative:** Additional dependency to manage across applications, requires team familiarity with Click's decorator patterns, potential for over-engineering simple CLI tools, dependency on external library for core application functionality, need for consistent coding standards across CLI implementations.
* **Future Implications:** All applications requiring CLI interfaces must use Click for consistency, CLI testing strategies should leverage Click's testing utilities, command structure and help text standards should be established across applications, configuration management patterns should integrate with Click's configuration features, administrative and operational tooling can be rapidly developed using established Click patterns.