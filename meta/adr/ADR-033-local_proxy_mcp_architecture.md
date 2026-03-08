---
title: "ADR-033: Local Proxy Architecture for MCP Integration"
status: "Proposed"
date: "2026-03-08"
tags:
  - "mcp"
  - "architecture"
  - "security"
  - "cost-optimization"
---

## Context

* **Problem:** The Hoopstat Haus project needs an architecture for exposing Gold layer basketball analytics to AI agents via the Model Context Protocol (MCP). Earlier planning documents (`meta/plans/mcp-server-architecture.md`) assumed a cloud-hosted model using AWS Lambda and API Gateway to serve MCP requests dynamically. This approach introduces unnecessary cloud compute costs, operational complexity, and — critically — a security surface where runaway AI agent loops could trigger unbounded Lambda invocations against our AWS infrastructure.

* **Constraints:**
  - Our Gold layer already produces pre-computed, static JSON artifacts served publicly via S3/CloudFront (per ADR-027 and ADR-028).
  - Our single-environment strategy (ADR-012) and development philosophy favor minimal moving parts and static-first design.
  - MCP clients (Claude Desktop, Cursor, etc.) natively support local adapter execution via `uvx` (Python) and `npx` (Node.js) package executors.
  - Zero additional cloud compute cost is strongly preferred — our AWS bill should not scale with the number of AI agents consuming our data.

## Decision

**We will use a Local Proxy Pattern for MCP integration.** All MCP JSON-RPC compute will execute on the AI client's local machine via a lightweight, open-source adapter script. Our cloud infrastructure will serve only static, pre-computed JSON artifacts — no Lambda functions, no API Gateway endpoints, and no dynamic server-side compute for MCP.

The architecture has three components:

1. **The Cloud (Zero Compute):** The Hoopstat Haus AWS infrastructure terminates at the Gold layer. The `served/` prefix of the Gold S3 bucket is exposed via CloudFront for public HTTP GET access. No server-side request processing occurs.

2. **The Client (Local Compute):** We provide a lightweight, open-source adapter package. AI clients execute this adapter locally using a standard package executor (`uvx` for Python or `npx` for Node.js). The adapter implements the MCP JSON-RPC interface that the AI client expects.

3. **The Data Flow:** The local adapter receives MCP JSON-RPC requests from the AI agent, translates them into standard HTTP GET requests to our CloudFront/S3 endpoint, retrieves the static JSON artifacts, and returns them to the agent in MCP-compliant format.

**This decision explicitly rejects deploying AWS Lambda functions or API Gateway endpoints for MCP compute.**

## Considered Options

1. **Local Proxy Adapter (Chosen):** MCP compute runs on the user's machine; cloud serves only static files.
   * *Pros:* Zero cloud compute costs regardless of agent volume; eliminates the attack surface for runaway AI agent loops and backend prompt injection; perfectly aligns with our static-first philosophy (ADR-027); adapter updates are transparent via `uvx`/`npx` auto-fetch; minimal operational burden.
   * *Cons:* Requires users to have a local Python or Node.js runtime; adapter must be published and maintained as an open-source package; no server-side query flexibility (by design).

2. **AWS Lambda + API Gateway (Cloud-Hosted MCP Server):** A serverless function processes MCP requests dynamically in the cloud.
   * *Pros:* Familiar serverless pattern; could support dynamic queries beyond pre-computed artifacts; no client-side runtime dependency.
   * *Cons:* Introduces per-request Lambda and API Gateway costs that scale with agent usage; creates a security surface where recursive AI agent loops could generate unbounded invocations and costs; requires API key management, rate limiting, and abuse prevention infrastructure; contradicts our static-first design philosophy; adds operational complexity for monitoring, alerting, and scaling.

3. **Self-Hosted MCP Server (EC2/ECS):** A persistent server handles MCP requests.
   * *Pros:* Full control over the runtime environment; could support complex queries.
   * *Cons:* Highest ongoing cost (always-on compute); maximum operational burden; completely contradicts our static-first and cost-optimized principles; massive overkill for serving pre-computed JSON files.

## Consequences

* **Positive:**
  - **Zero cloud compute costs:** AWS bill is unaffected by MCP agent usage. We pay only for S3/CloudFront data transfer, which is pennies for small JSON artifacts.
  - **Enhanced security:** By removing all dynamic cloud compute from the MCP path, we completely eliminate the risk of backend prompt injection, recursive agent-loop DDoS attacks, and runaway Lambda cost escalation. Malicious agents can only ever download static files.
  - **Static-first alignment:** This architecture is a natural extension of ADR-027 (stateless JSON artifacts) and our development philosophy's emphasis on static over dynamic solutions.
  - **Transparent updates:** Distributing the adapter via a package registry (`uvx`/`npx`) means users automatically get the latest adapter version on each launch, making bug fixes and new endpoint support seamless.
  - **Simplicity:** No new AWS resources, IAM roles, monitoring dashboards, or operational runbooks are needed for MCP serving.

* **Negative:**
  - Users must have a local Python or Node.js runtime to use the MCP adapter (standard for AI agent users).
  - No server-side ad-hoc querying capability (by design — all data is pre-computed).
  - The adapter package must be maintained and published as a separate open-source artifact.

* **Future Implications:**
  - A separate ADR (ADR-034) should decide the adapter's runtime language (Python via `uvx` for consistency with ADR-002, vs. TypeScript via `npx` for broader MCP ecosystem alignment).
  - A separate ADR (ADR-035) should formalize the Gold S3 public access strategy (direct S3 vs. CloudFront, security boundaries).
  - The `meta/plans/mcp-server-architecture.md` planning document, which assumed a cloud-hosted Lambda model, is superseded by this decision and has been archived.
  - The Gold layer `served/` prefix and its JSON artifact schema (defined in ADR-027 and ADR-028) become the sole data contract for MCP consumption.
