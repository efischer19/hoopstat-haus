---
title: "ADR-023: Use MkDocs with Material Theme for Documentation Generation"
status: "Proposed"
date: "2025-08-09"
tags:
  - "documentation"
  - "api-docs"
  - "static-site"
  - "mkdocs"
  - "github-pages"
---

## Context

* **Problem:** Shared libraries in the monorepo lack discoverable, accessible API documentation, making it difficult for developers to understand and effectively use existing functionality across applications.
* **Constraints:** Documentation solution must integrate with existing Python toolchain (Poetry, Ruff), support automatic generation from code docstrings, deploy seamlessly via GitHub Actions, be searchable and mobile-friendly, and require minimal manual maintenance overhead.

## Decision

We will use **MkDocs with Material theme** for automated documentation generation, combined with custom Python scripts for API extraction and GitHub Pages for hosting.

## Considered Options

1. **MkDocs + Material Theme (The Chosen One):** Modern static site generator with API documentation automation.
   * *Pros:* Lightweight and fast, excellent Material theme with search/navigation, markdown-based content is developer-friendly, integrates well with GitHub Pages, supports custom Python scripts for API extraction, responsive design, minimal configuration overhead, strong community support
   * *Cons:* Requires custom scripting for API documentation (not built-in like Sphinx), less mature ecosystem than Sphinx, theme customization is more limited

2. **Sphinx + autodoc:** Python's traditional documentation system with automatic API extraction.
   * *Pros:* Industry standard for Python documentation, excellent autodoc extension for automatic API documentation, extensive theme ecosystem, powerful cross-referencing, excellent for complex projects
   * *Cons:* Steeper learning curve, reStructuredText syntax is less accessible than Markdown, more complex configuration, heavier runtime requirements, can be overkill for library documentation

3. **GitBook:** Commercial documentation platform with GitHub integration.
   * *Pros:* Beautiful UI, excellent collaborative editing, built-in analytics, good GitHub integration
   * *Cons:* Commercial platform with costs, less control over hosting, potential vendor lock-in, limited customization, not designed specifically for API documentation

4. **Docusaurus:** Facebook's modern documentation platform.
   * *Pros:* React-based with modern UI, excellent performance, good versioning support, active development
   * *Cons:* Requires Node.js ecosystem (conflicts with Python-first approach), more complex for simple documentation sites, overkill for API documentation

## Consequences

* **Positive:** Automatic API documentation generation from docstrings reduces maintenance overhead, Material theme provides excellent search and navigation experience, GitHub Pages integration ensures documentation is always accessible and up-to-date, markdown-based content is developer-friendly and version-controllable, minimal learning curve for contributors, fast site generation and loading.
* **Negative:** Custom AST parsing scripts require maintenance, less powerful than Sphinx for complex documentation structures, theme customization options are more limited, requires separate toolchain from main Python development.
* **Future Implications:** All shared libraries will have automatically generated API documentation, developers can easily discover and understand library functionality, documentation deployment is fully automated via CI/CD, establishes pattern for potential application-level documentation, creates foundation for more comprehensive developer documentation portal.