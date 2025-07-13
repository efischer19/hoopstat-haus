---
title: "Record <number>: <Title of Decision>"
status: "Proposed | Accepted | Deprecated | Superseded"
date: "YYYY-MM-DD"
supersedes: "ADR-XXX"  # Optional: if this ADR replaces another
tags:
  - "data-pipeline"
  - "testing"
  - "ci-cd"
---

## Context

* **Problem:** What is the problem or issue we are facing? What is the context that forces this decision?
* **Constraints:** What are the technical or business constraints that limit our options?

## Decision

The clear, concise statement of the decision that has been made. For example: "We will use Poetry for dependency management for all Python sub-projects."

## Considered Options

1.  **Option 1 (The Chosen One):** Briefly describe the selected option.
    * *Pros:* What are the benefits of this choice?
    * *Cons:* What are the drawbacks or trade-offs?
2.  **Option 2:** Describe another option that was considered.
    * *Pros:* ...
    * *Cons:* ...
3.  **Option 3:** ...

## Consequences

* **Positive:** What are the expected positive outcomes? (e.g., "Developer onboarding will be simpler," "Builds will be more reproducible.")
* **Negative:** What are the known negative trade-offs? (e.g., "Requires all developers to install a new tool," "Slightly slower initial dependency resolution.")
* **Future Implications:** How does this decision impact future work or other parts of the system?
