---
title: "ADR-015: Logging Strategy for Application Observability"
status: "Accepted"
date: "2025-07-16"
tags:
  - "logging"
  - "observability"
  - "monitoring"
  - "data-pipeline"
---

## Context

* **Problem:** The Hoopstat Haus data pipeline and applications require a comprehensive logging strategy to ensure observability, debugging capabilities, and operational monitoring. Effective logging is critical for identifying data quality issues, performance bottlenecks, API failures, and system health in production.
* **Constraints:** Must provide structured, searchable log data for effective debugging, enable automated monitoring and alerting on system health, support efficient log aggregation and analysis, maintain performance with minimal overhead, align with the single production environment strategy requiring excellent observability, and integrate well with common log management tools and practices.

## Decision

We will use **structured JSON logging** as the standard format for all application logs across the Hoopstat Haus platform.

## Considered Options

1. **Structured JSON Logging (The Chosen One):** Machine-readable JSON format with consistent field structure.
   * *Pros:* Machine-parseable enabling automated log analysis and alerting, consistent structure across all applications and services, excellent integration with modern log aggregation tools (ELK stack, Fluentd, etc.), supports rich context with nested objects and arrays, enables efficient filtering and searching on specific fields, facilitates correlation tracking across distributed components, excellent support in Python logging ecosystem
   * *Cons:* Less human-readable in raw form compared to plain text, slightly larger log size due to JSON overhead, requires log viewers that can format JSON for readability

2. **Plain Text Logging:** Traditional unstructured text-based log messages.
   * *Pros:* Highly human-readable in raw form, minimal overhead and processing requirements, simple implementation with standard logging libraries, universal compatibility with all log viewing tools
   * *Cons:* Difficult to parse automatically for monitoring and alerting, inconsistent format leading to parsing challenges, limited context and metadata capabilities, poor integration with modern log analysis tools, difficult to implement correlation tracking

3. **Key-Value Pair Logging:** Semi-structured format using consistent key=value patterns.
   * *Pros:* More structured than plain text while remaining human-readable, easier to parse than free-form text, good balance between readability and structure
   * *Cons:* Less structured than JSON limiting analysis capabilities, inconsistent parsing between different tools, limited support for nested data structures, lacks standardization leading to format drift

4. **Binary Logging Formats (e.g., Protocol Buffers, MessagePack):** Highly efficient binary serialization formats.
   * *Pros:* Extremely compact reducing storage and transmission costs, very fast serialization/deserialization, strong schema enforcement
   * *Cons:* Not human-readable requiring special tools for inspection, additional complexity in implementation and tooling, limited ecosystem support for log analysis, overkill for typical application logging needs

## Standard Fields for Data Pipeline Jobs

All data pipeline jobs must include the following standard fields in their JSON log output to enable performance monitoring and alerting:

* **`duration_in_seconds`** (number): The total execution time of the data pipeline job in seconds with decimal precision for sub-second accuracy
* **`records_processed`** (number): The total count of records processed by the data pipeline job (e.g., rows read, documents transformed, records written)

These fields enable:
- Performance baseline establishment and regression detection
- Automated monitoring and alerting on execution time anomalies
- Capacity planning based on throughput metrics
- Cost optimization through execution time analysis

### Example Log Entry

```json
{
  "timestamp": "2025-01-27T14:30:45.123Z",
  "level": "INFO",
  "message": "Data pipeline job completed successfully",
  "job_name": "daily_stats_aggregation", 
  "duration_in_seconds": 45.67,
  "records_processed": 15420,
  "correlation_id": "job-20250127-143000-abc123"
}
```

## Consequences

* **Positive:** Enables sophisticated monitoring and alerting through automated log analysis, facilitates rapid debugging through structured field searches, supports correlation tracking across data pipeline stages, integrates seamlessly with modern observability tooling, enables rich contextual information in log entries, improves operational visibility critical for single environment strategy, provides standardized performance metrics for data pipeline monitoring and cost optimization.
* **Negative:** Requires developers to adopt structured logging practices and mindset, slightly reduced human readability in raw log files, potential for inconsistent field naming without proper standards, increased log size compared to minimal text logging, additional overhead to track and calculate performance metrics.
* **Future Implications:** All applications must implement consistent JSON logging schemas with standard fields, log aggregation and analysis tooling selection should prioritize JSON parsing capabilities, monitoring and alerting systems can leverage structured data for sophisticated rules, development processes must include log message design and field standardization, correlation IDs and tracing become feasible across the entire data pipeline, performance monitoring and alerting can be automated based on the standardized duration and record count fields.