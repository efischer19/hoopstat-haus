---
title: "ADR-021: Use Tenacity for Retry Logic and Resilience"
status: "Accepted"
date: "2025-08-09"
tags:
  - "resilience"
  - "error-handling"
  - "data-pipeline"
  - "reliability"
---

## Context

* **Problem:** Data pipeline applications need robust retry logic to handle transient failures when interacting with external APIs (NBA API), cloud storage (S3), and other distributed systems. Network timeouts, rate limiting, temporary service unavailability, and other ephemeral issues require intelligent retry strategies to ensure pipeline reliability.
* **Constraints:** The retry solution must support various retry strategies (exponential backoff, fixed delay, etc.), integrate well with Python async/await patterns, provide configurable retry conditions, enable monitoring and logging of retry attempts, and maintain simplicity for common use cases while allowing customization for complex scenarios.

## Decision

We will use **Tenacity** as the standard library for implementing retry logic and resilience patterns across all Hoopstat Haus applications.

## Considered Options

1. **Tenacity (The Chosen One):** Modern, feature-rich Python retry library with decorator and functional interfaces.
   * *Pros:* Comprehensive retry strategies (exponential backoff, fixed delay, custom), excellent async/await support, highly configurable retry conditions and stop criteria, built-in logging and statistics collection, decorator-based interface for clean code, supports custom retry callbacks for monitoring, active maintenance and modern Python support, extensive documentation and examples
   * *Cons:* Additional dependency to manage, slight learning curve for advanced features, potential for over-engineering simple retry scenarios

2. **urllib3.util.retry:** Built-in retry functionality from the urllib3 library.
   * *Pros:* No additional dependencies, well-tested and stable, integrated with HTTP libraries, simple configuration for basic use cases
   * *Cons:* Limited to HTTP requests only, basic retry strategies, poor async support, limited customization options, no built-in logging or monitoring features

3. **Custom Retry Implementation:** Hand-written retry logic tailored to specific use cases.
   * *Pros:* Full control over retry behavior, no external dependencies, optimized for specific use cases, minimal overhead
   * *Cons:* High maintenance burden, prone to bugs and edge cases, code duplication across applications, no standardization, requires significant testing, reinventing well-solved problems

4. **Backoff Library:** Alternative Python retry library with simpler interface.
   * *Pros:* Simpler decorator-based interface, good for basic retry scenarios, minimal configuration required
   * *Cons:* Less feature-rich than Tenacity, limited async support, fewer retry strategies available, less active development, limited monitoring capabilities

## Consequences

* **Positive:** Improved reliability of data pipeline operations through intelligent retry handling, standardized approach to resilience across all applications, reduced code duplication and maintenance burden, enhanced observability through built-in logging and statistics, support for both simple and complex retry scenarios, excellent integration with async data pipeline operations, protection against transient failures in NBA API and AWS services.
* **Negative:** Additional dependency to manage and keep updated, potential for misuse leading to excessive retry attempts, requires team education on proper retry strategy configuration, adds complexity to simple operations that may not need retry logic, potential for masking underlying system issues with aggressive retry policies.
* **Future Implications:** All external API calls and distributed system interactions should implement appropriate retry strategies using Tenacity, monitoring and alerting systems can leverage Tenacity's statistics for observability, retry configuration should be externalized for production tuning, rate limiting strategies must coordinate with retry policies to avoid API abuse, documentation and examples needed for common retry patterns across different data sources.