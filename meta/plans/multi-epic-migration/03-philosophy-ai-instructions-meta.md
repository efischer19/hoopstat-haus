# feat: Development philosophy, AI instructions, and meta scaffolding for blueprint-repo-blueprints

## What do you want to build?

Populate the `blueprint-repo-blueprints` template with the core development philosophy, AI contributor instructions, and meta-level scaffolding that every derived repository should inherit. This content is the "soul" of the template system.

## Acceptance Criteria

- [ ] `meta/DEVELOPMENT_PHILOSOPHY.md` is present, adapted from hoopstat-haus (remove hoopstat-specific references, keep universal principles)
- [ ] `.github/copilot-instructions.md` is present with generalized AI contributor instructions (adapted from hoopstat-haus, no project-specific references)
- [ ] `CONTRIBUTING.md` is present with general contribution guidelines
- [ ] `meta/adr/` contains ADR-001 (Use ADRs) adapted for general use
- [ ] `meta/plans/` contains a README explaining the plans directory purpose
- [ ] All documents use consistent markdown formatting and follow the philosophy they describe
- [ ] No hoopstat-specific terminology remains in any template content (e.g., "NBA", "basketball", "bronze/silver/gold" pipeline)
- [ ] Template placeholders use clear markers (e.g., `{{PROJECT_NAME}}`, `{{DESCRIPTION}}`) where project-specific content is needed

## Implementation Notes (Optional)

Source material from hoopstat-haus to adapt:
- `meta/DEVELOPMENT_PHILOSOPHY.md` — Core principles (Humans First, Simplicity, Sacred Main, Testing, Boy Scout, Commit Hygiene). These are universal; copy and generalize.
- `.github/copilot-instructions.md` — AI contributor workflow. Remove hoopstat-specific paths and commands; keep the structured workflow (review philosophy → check ADRs → understand codebase → minimal changes → test → commit).
- `CONTRIBUTING.md` — Generalize for template usage.

The philosophy document should explicitly call out that it's inherited from the blueprint system and downstream repos should customize but not weaken the core principles.
