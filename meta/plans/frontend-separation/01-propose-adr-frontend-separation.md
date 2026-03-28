# Ticket 01: Propose ADR-042 — Frontend Repository Separation

**Title:** `feat: propose ADR-042 for frontend repository separation`

## What do you want to build?

Create and merge ADR-042 documenting the decision to separate the frontend application into its own repository. This ADR formalizes the architectural rationale, enumerates what stays and what moves, and establishes the shared-infrastructure model (single CloudFront distribution, shared S3 bucket) as the chosen approach.

The ADR is already drafted at `meta/adr/ADR-042-frontend-repository-separation.md` with status `Proposed`. This ticket's scope is to review, refine, and accept it.

## Acceptance Criteria

- [ ] `meta/adr/ADR-042-frontend-repository-separation.md` exists with status `Proposed` (or `Accepted` after human review)
- [ ] ADR covers: context, decision, considered options (shared CloudFront, separate CloudFront, keep monorepo, git subtree), and consequences
- [ ] ADR explicitly states that the health dashboard (`health.html`) stays in this repo as a backend observability component
- [ ] ADR references relevant existing ADRs: ADR-008 (monorepo), ADR-019 (vanilla frontend), ADR-035 (CloudFront + OAC), ADR-036 (Chart.js), ADR-038 (cache tuning), ADR-040 (health dashboard)
- [ ] ADR is reviewed and approved by a human maintainer

## Implementation Notes (Optional)

- This is a prerequisite for all other tickets in the epic. No code changes are needed — only the ADR markdown file.
- The ADR draft is included in the same PR as the epic plan files. It can be accepted in a follow-up PR after human review.
- If the human reviewer prefers a different approach (e.g., separate CloudFront distributions instead of shared), update the ADR accordingly and re-sequence downstream tickets.
