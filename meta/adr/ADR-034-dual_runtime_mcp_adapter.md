---
title: "ADR-034: Dual-Runtime MCP Adapter (Python + TypeScript)"
status: "Proposed"
date: "2026-03-08"
tags:
  - "mcp"
  - "adapter"
  - "python"
  - "typescript"
  - "distribution"
---

## Context

* **Problem:** ADR-033 established that MCP integration will use a Local Proxy Pattern -- a lightweight adapter running on the AI client's local machine. We need to decide which language runtime(s) to use for this adapter and how to distribute it to end users.

* **Constraints:**
  - ADR-002 establishes Python 3.12+ as our primary language. All data pipeline code (Bronze, Silver, Gold) is Python.
  - The MCP ecosystem is split: Anthropic's official Python SDK (`mcp` package) supports `uvx` execution, while much of the broader MCP community tooling uses TypeScript/Node.js with `npx`.
  - The adapter's job is minimal -- translate MCP JSON-RPC requests into HTTP GET calls to our CloudFront endpoint and return the results. This is not data-moving code; it is a thin protocol translation layer.
  - Maximum adoption is a priority. We want AI agent users on both Python and Node.js runtimes to be able to use our data with zero friction.

## Decision

**We will build and maintain MCP adapters in both Python (distributed via PyPI, executed via `uvx`) and TypeScript (distributed via npm, executed via `npx`).**

Both adapters will implement identical MCP capabilities:

- `resources/list`: Fetch `served/index/latest.json` from CloudFront and return the available datasets.
- `resources/read`: Fetch a specific JSON artifact (e.g., `player_daily/{date}/{player_id}.json`) and return it to the agent.

The Python adapter is the **primary** implementation, consistent with ADR-002. The TypeScript adapter provides ecosystem reach for users whose AI clients prefer `npx`.

All upstream data pipeline code (ingestion, processing, analytics) remains exclusively Python per ADR-002. The TypeScript adapter is scoped strictly to the MCP protocol translation layer -- it does not process, transform, or move data.

## Considered Options

1. **Dual-runtime: Python + TypeScript (Chosen):** Build both adapters for maximum adoption.
   * *Pros:* Reaches the full MCP client ecosystem (Claude Desktop, Cursor, and others support both `uvx` and `npx`); users can pick the runtime they already have installed; the adapter logic is trivial (HTTP GET + JSON formatting), so maintaining two implementations is low-cost; Python adapter aligns with ADR-002 for internal consistency.
   * *Cons:* Two packages to maintain and publish; must keep feature parity between them; slightly more CI/CD surface area.

2. **Python-only (`uvx`):** Build only the Python adapter, consistent with ADR-002.
   * *Pros:* Single codebase; consistent with our Python-first philosophy; Anthropic's SDK natively supports `uvx`.
   * *Cons:* Excludes users whose AI clients are configured for `npx`-only adapters; narrower adoption; misses the large Node.js MCP ecosystem.

3. **TypeScript-only (`npx`):** Build only the TypeScript adapter for broader ecosystem reach.
   * *Pros:* Largest existing MCP adapter ecosystem is TypeScript; `npx` is widely available.
   * *Cons:* Introduces a non-Python runtime into the project without the balancing benefit of ADR-002 alignment; requires TypeScript expertise for maintenance; feels inconsistent with our Python-first identity.

## Consequences

* **Positive:**
  - Maximum adoption: any AI agent user with either Python or Node.js can consume our data.
  - Low maintenance burden: the adapter logic is a thin HTTP GET wrapper, so both implementations are small and simple.
  - Python adapter keeps the project consistent with ADR-002; TypeScript adapter is pragmatically scoped.
  - Users get automatic updates via `uvx`/`npx` auto-fetch on each launch (per ADR-033).

* **Negative:**
  - Two packages to publish (PyPI and npm) and keep in sync.
  - TypeScript adapter introduces a second language into the repository, though only for the MCP adapter scope.
  - Feature parity testing needed across both runtimes.

* **Future Implications:**
  - The Python adapter should live in `apps/` (e.g., `apps/mcp-adapter-python/`) following the monorepo pattern.
  - The TypeScript adapter should live alongside it (e.g., `apps/mcp-adapter-ts/`) or in a separate lightweight directory.
  - Both adapters depend on the Gold `served/` JSON artifact contract defined in ADR-027 and ADR-028.
  - If the MCP protocol evolves significantly, both adapters must be updated in tandem.
  - The adapter packages should be named consistently (e.g., `hoopstat-haus-mcp` on both PyPI and npm).
