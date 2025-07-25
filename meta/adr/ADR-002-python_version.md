---
title: "ADR-002: Use Python 3.12+ for All Python Applications"
status: "Accepted"
date: "2025-07-16"
tags:
  - "python"
  - "runtime"
  - "standardization"
---

## Context

* **Problem:** As we begin building Python applications within the Hoopstat Haus project, we need to establish a consistent Python runtime version across all applications to ensure compatibility, security, and access to modern language features.
* **Constraints:** We need a version that provides stability for production use while offering modern features and performance improvements. The version should have good ecosystem support and be widely available in deployment environments.

## Decision

We will use **Python 3.12 or higher** as the minimum required Python version for all Python applications within the Hoopstat Haus project.

## Considered Options

1. **Python 3.12+ (The Chosen One):** Use Python 3.12 as the minimum version with support for newer versions.
   * *Pros:* Modern language features (improved error messages, f-string improvements, type hints enhancements), better performance, excellent security support, stable and mature
   * *Cons:* Some legacy libraries may not yet support 3.12, requires developers to upgrade if using older versions

2. **Python 3.11:** Use Python 3.11 as the minimum version.
   * *Pros:* Widely supported, good performance improvements over 3.10, stable
   * *Cons:* Missing some of the latest language improvements and performance enhancements from 3.12

3. **Python 3.10:** Use Python 3.10 as the minimum version.
   * *Pros:* Very stable, broad ecosystem support, pattern matching features
   * *Cons:* Missing performance improvements and language features from newer versions, will become outdated more quickly

## Consequences

* **Positive:** Access to the latest Python language features and performance improvements, excellent security support, future-proofing our applications, consistent development environment across all Python projects.
* **Negative:** May require developers to upgrade their local Python installations, some third-party packages may not yet fully support Python 3.12.
* **Future Implications:** This decision establishes Python 3.12+ as our baseline, allowing us to leverage modern Python features in all code. We will need to evaluate upgrading to newer Python versions (3.13+) as they become stable and widely adopted.