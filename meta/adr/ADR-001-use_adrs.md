---
title: "ADR-001: Use Architecture Decision Records (ADRs) to Document Decisions"
status: "Accepted"
date: "2025-07-14"
tags:
  - "process"
  - "documentation"
  - "meta"
---

## Context

* **Problem:** As our project evolves, we need a consistent and transparent process for making, documenting, and communicating significant architectural decisions. This process must be clear for both human and AI contributors to ensure the project develops in a coherent and maintainable way.

## Decision

We will use **Architecture Decision Records (ADRs)** as the primary method for documenting all significant technical and architectural decisions.

1.  **What is an ADR?** An ADR is a short, text-based document that records a single architectural decision. It includes the context behind the decision, the different options considered, and the consequences of the chosen path. All ADRs will be stored in the `/meta/adr/` directory with descriptive filenames following the pattern `ADR-XXX-topic_name.md` (e.g., `ADR-001-use_adrs.md`).

2.  **When is an ADR Required?** Our guiding principle is: **a decision without an ADR is just an opinion.** An ADR is required for any "significant decision" to turn that opinion into a documented, agreed-upon standard. This includes, but is not limited to: adding a new service or dependency, choosing a technology or tool (e.g., a database or library), defining a core data model, or establishing a new development process.

3.  **The ADR Lifecycle:** Every ADR has a status:
    * **`Proposed`**: The decision is under consideration and open for discussion.
    * **`Accepted`**: The decision has been approved and **must** be followed by all future work.
    * **`Superseded by ADR-XXX`**: The decision is no longer active and has been replaced by a newer ADR. Superseded ADRs **must not** be followed.

4.  **The Logbook vs. The Map:** We use two types of architectural documents:
    * **ADRs (The Logbook):** The immutable, chronological log of *why* decisions were made.
    * **`meta/ARCHITECTURE.md` (The Map):** A living document visualizing the *current state* of the system, which evolves as a result of new, `Accepted` ADRs.

5.  **Linking Implementations to Decisions:** When a Pull Request is created, its description should link to any `Accepted` ADRs that provide significant context or constraints for the work being done. This creates a clear link between the implementation and the architectural principles it follows.

6.  **Proposing New ADRs:** Our attitude towards proposing new ADRs is **"yes, please."** We encourage all contributors (human or AI) to identify when a task requires a decision not covered by existing ADRs.

7.  **The Proposal and Acceptance Process:** An AI contributor can identify the need for a new ADR or be tasked with drafting one.
    * A `Proposed` ADR should be a complete document. The author is responsible for filling out the context, considered options, and a recommended decision to the best of their ability.
    * Only a human maintainer can formally approve a decision by changing the ADR's status from `Proposed` to `Accepted` and merging it into the `main` branch.

8.  **Superseding a Decision:** If a new ADR replaces a previous one, the author must:
    * Set the `supersedes: ADR-XXX-topic_name` field in the new ADR's frontmatter.
    * After the new ADR is accepted, create a follow-up PR to change the status of the old ADR file to `Superseded`.

9.  **Batching Related Proposals:** It is acceptable and encouraged to propose a set of related, interdependent ADRs within a single Pull Request. This allows for a holistic review of a larger architectural theme (e.g., establishing the initial Python tech stack). Each ADR must still be its own file and focus on a single decision. The acceptance of all proposed ADRs in the PR occurs when the PR is merged.

## Consequences

* **Positive:** This process creates a clear, transparent, and auditable history of our project's architecture. It provides essential context for all contributors and prevents the re-litigation of old debates.
* **Negative:** It requires the discipline to stop and write a new ADR whenever a significant, un-documented decision needs to be made.
