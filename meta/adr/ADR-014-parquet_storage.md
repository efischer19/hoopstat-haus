---
title: "ADR-014: Data Storage Format for Intermediate Pipeline Artifacts"
status: "Superseded"
date: "2025-07-16"
superseded_by: "ADR-025"
superseded_date: "2025-09-07"
tags:
  - "data-pipeline"
  - "data-storage"
  - "file-format"
---

## Context

* **Problem:** The data pipeline needs a standardized format for storing intermediate structured data artifacts between processing stages. This includes raw data from the NBA API, cleaned datasets, aggregated statistics, and transformed data ready for analysis or visualization.
* **Constraints:** Must support efficient storage and retrieval of structured basketball statistics, provide good compression to minimize storage costs, enable fast analytical queries on stored data, maintain compatibility with Python data science ecosystem, support schema evolution as data models change, and align with the project's static-first philosophy preferring build-time optimizations.

## Decision

We will use **Apache Parquet** as the standard format for storing all intermediate structured data artifacts in the data pipeline.

## Considered Options

1. **Apache Parquet (The Chosen One):** Columnar binary format optimized for analytics workloads.
   * *Pros:* Excellent compression ratios reducing storage costs, fast analytical query performance due to columnar structure, built-in schema support with evolution capabilities, wide compatibility with Python data tools (pandas, polars, PyArrow), self-describing format with embedded metadata, efficient I/O with support for predicate pushdown, industry standard for analytical data storage
   * *Cons:* Binary format not human-readable for debugging, requires specific libraries for reading/writing, slightly more complex than plain text formats, overhead for very small datasets

2. **CSV (Comma-Separated Values):** Simple text-based tabular format.
   * *Pros:* Human-readable and debuggable, universal compatibility across tools and languages, simple to implement and understand, no special libraries required
   * *Cons:* No built-in schema or type information, poor compression efficiency, slow parsing for large datasets, inconsistent handling of edge cases (nulls, special characters), no support for nested data structures

3. **JSON Lines (JSONL):** Newline-delimited JSON format.
   * *Pros:* Human-readable and debuggable, supports nested data structures, wide language support, schema-flexible for evolving data models
   * *Cons:* Verbose format leading to large file sizes, poor compression compared to binary formats, slower parsing for analytical workloads, no columnar optimizations for analytics queries

4. **Apache Arrow IPC:** Binary columnar format optimized for in-memory analytics.
   * *Pros:* Extremely fast serialization/deserialization, zero-copy reads in compatible systems, excellent integration with modern data tools, columnar format optimized for analytics
   * *Cons:* Less mature ecosystem compared to Parquet, primarily designed for in-memory rather than persistent storage, more complex implementation requirements, smaller community and tooling support

## Consequences

* **Positive:** Significant reduction in storage costs through efficient compression, faster data loading and query performance for analytics workloads, seamless integration with Python data science stack (pandas, polars, PyArrow), built-in schema management reducing data quality issues, future-proof format with strong industry adoption, enables efficient data partitioning strategies for large datasets.
* **Negative:** Requires additional libraries (PyArrow/fastparquet) increasing dependency complexity, binary format makes manual inspection and debugging more difficult, slight learning curve for developers unfamiliar with columnar formats, less optimal for row-by-row processing patterns.
* **Future Implications:** All data pipeline stages must implement Parquet read/write capabilities, storage architecture can leverage Parquet's partitioning features for scalable data organization, monitoring and debugging tools need to support Parquet inspection, integration with analytical engines and visualization tools simplified through standard format adoption.