# Ticket 3: Propose ADR-036 for Lightweight Charting Library

> **Epic:** [Frontend Simplification & Lightweight Visualization](00-executive-summary.md)
> **Sequence:** 3 of 5 (no dependencies -- can be worked in parallel with ticket #1)
> **Related ADR:** ADR-019 (Vanilla Frontend)

---

## What do you want to build?

Write and propose ADR-036 documenting the decision to use Chart.js via CDN as the lightweight charting library for the frontend. This ADR should evaluate alternatives, justify the choice against our development philosophy (simplicity, static-first, YAGNI), and establish conventions for how charts are integrated into the vanilla frontend.

## Acceptance Criteria

- [ ] `meta/adr/ADR-036-lightweight_charting_library.md` is created following the ADR template (`meta/adr/TEMPLATE.md`)
- [ ] ADR status is `Proposed` (only humans can set `Accepted`)
- [ ] The ADR uses standard double-hyphens (`--`) instead of em dashes, per project convention
- [ ] The Context section explains why visualization is needed and what constraints apply (vanilla JS, no build process, CDN-only, small payload budget)
- [ ] The Decision section clearly states the chosen library (Chart.js) and the CDN delivery mechanism
- [ ] At least 3 alternatives are evaluated in the Considered Options section (e.g., Chart.js, uPlot, D3.js, Plotly, vanilla Canvas/SVG)
- [ ] Consequences address both positive outcomes (easy integration, good docs) and negative trade-offs (CDN dependency, library size)
- [ ] The ADR references ADR-019 (vanilla frontend decision) and explains how Chart.js aligns with it
- [ ] The ADR specifies the Chart.js version pinning strategy for CDN inclusion (e.g., pin to major version)

## Implementation Notes (Optional)

### ADR file location

`meta/adr/ADR-036-lightweight_charting_library.md`

### Key points to cover

**Why Chart.js over alternatives:**
- **vs. D3.js:** D3 is a low-level visualization toolkit, not a charting library. Requires significantly more code to produce a simple line chart. Overkill for our needs.
- **vs. uPlot:** Lighter weight (~35KB vs ~65KB for Chart.js), but smaller community, fewer chart types, and less documentation. Good alternative if size becomes critical.
- **vs. Plotly:** Full-featured but heavy (~1MB minified). Violates our simplicity and payload constraints.
- **vs. vanilla Canvas/SVG:** Maximum control and zero dependencies, but requires significant effort to build responsive, interactive charts from scratch. Violates YAGNI in the opposite direction.

**CDN integration pattern:**
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
```

**Version pinning:** Pin to major version (`@4`) for automatic patch/minor updates while avoiding breaking changes.

**Alignment with ADR-019:**
- No build process required -- CDN script tag only
- No npm/node dependencies added
- Chart.js works with vanilla JS (no framework adapters needed)
- Progressive enhancement -- page works without charts if CDN is unavailable

### Verification

1. ADR follows the template structure in `meta/adr/TEMPLATE.md`
2. YAML frontmatter includes title, status, date, and tags
3. All sections (Context, Decision, Considered Options, Consequences) are complete
4. References to ADR-019 are accurate
