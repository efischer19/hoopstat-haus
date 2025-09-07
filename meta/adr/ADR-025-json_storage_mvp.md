---
title: "ADR-025: JSON Storage for Simplified MVP Data Pipeline"
status: "Accepted"
date: "2025-09-07"
supersedes: "ADR-014"
tags:
  - "data-pipeline"
  - "data-storage"
  - "file-format"
  - "mvp"
---

## Context

* **Problem:** The simplified roadmap requires a storage format that prioritizes development velocity and debugging ease over analytical performance for the MVP phase. The current Parquet decision (ADR-014) optimizes for production analytics workloads but adds complexity that slows initial development and testing.
* **Changed Constraints:** MVP scope focuses on box score data (~30 games/day, ~1KB per game), development speed is more important than storage optimization, debugging and data inspection must be trivial for rapid iteration, AI assistants need easily parseable data formats, team size is effectively one developer requiring maximum simplicity.

## Decision

For the **MVP phase only**, we will use **JSON** as the storage format for all data pipeline artifacts (Bronze, Silver, and Gold layers), superseding the Parquet decision for this phase.

**Post-MVP Migration Path:** Once core functionality is proven, we will evaluate migrating to Parquet for production workloads, maintaining this as a format-agnostic architectural decision.

## Considered Options

1. **JSON (The MVP Choice):** Human-readable text format with universal compatibility.
   * *Pros:* Zero additional dependencies, human-readable for easy debugging, trivial S3 inspection via AWS console, universal tooling support, AI-friendly format, simple schema validation with Pydantic, rapid development and testing cycles
   * *Cons:* Larger storage footprint, slower analytical queries, less efficient compression, no columnar optimizations

2. **Maintain Parquet (Status Quo):** Continue with existing ADR-014 decision.
   * *Pros:* Production-ready performance, efficient storage, strong analytics ecosystem
   * *Cons:* Additional complexity slows MVP development, harder debugging, requires specialized tools for data inspection, steeper learning curve

3. **Hybrid Approach:** JSON for Bronze/Silver, Parquet for Gold.
   * *Pros:* Balances development speed with some performance benefits
   * *Cons:* Adds complexity with multiple formats, inconsistent data handling patterns

## Consequences

* **Positive:** Dramatically faster development cycles with immediate data inspection, zero additional dependencies reducing setup complexity, easier debugging of data pipeline issues, AI assistants can directly consume outputs, simplified local development workflow, trivial data validation and testing.
* **Negative:** Higher storage costs for production (estimated 3-5x larger files), slower analytical query performance, less efficient data transfer, manual schema enforcement required.
* **Future Implications:** Migration strategy needed for production scale, all pipeline components must support format-agnostic design, monitoring should track storage costs as scaling indicator for Parquet migration decision.

## MVP-Specific Rationale

This decision explicitly optimizes for:
- **Development Velocity:** Getting to working MVP faster
- **Debugging Ease:** Human-readable data at every pipeline stage  
- **Operational Simplicity:** No additional tools or dependencies
- **AI Integration:** JSON is the native format for LLM consumption

The performance and storage optimizations of Parquet remain valuable for production workloads and will be reconsidered post-MVP based on actual usage patterns and scale requirements.

## Migration Criteria

We will reconsider Parquet when any of these conditions are met:
- Storage costs exceed $50/month
- Query performance becomes a user-facing issue
- Data volume exceeds 10GB total
- Team grows beyond 2 developers requiring production tooling
