> **⚠️ ARCHIVED (2026-03-08):** This proposal has been formalized into Architecture Decision Records. See:
> - [ADR-033](../adr/ADR-033-local_proxy_mcp_architecture.md) -- Local Proxy Architecture for MCP Integration
> - [ADR-034](../adr/ADR-034-dual_runtime_mcp_adapter.md) -- Dual-Runtime MCP Adapter (Python + TypeScript)
> - [ADR-035](../adr/ADR-035-gold_s3_public_access.md) -- Gold S3 Public Access via CloudFront with OAC
>
> The original proposal content is retained below for historical context.

5 March 2026

---

# Proposal: Static MCP Server via Local Proxy Adapter

## Executive Summary

This proposal outlines a paradigm shift in our deployment strategy for the Hoopstat Haus MCP (Model Context Protocol) Server. Rather than building and maintaining dynamic cloud compute (AWS Lambda + API Gateway) to process AI agent requests, we will utilize a **Local Proxy Pattern**.

By serving purely static, pre-computed JSON artifacts directly from our Gold S3 bucket and shifting the MCP JSON-RPC compute to the user's local machine via an open-source adapter, we achieve a highly scalable, zero-cloud-compute data platform.

## The Architecture

1. **The Cloud (Zero Compute):** The Hoopstat Haus AWS infrastructure stops at the Gold layer. We expose the `served/` prefix of our Gold S3 bucket via public HTTP GET requests (optionally fronted by CloudFront).
2. **The Client (Local Compute):** We provide a lightweight, open-source adapter script. AI clients (Claude Desktop, Cursor) execute this script locally using a standard package executor (`npx` for Node.js, or `uvx` for Python).
3. **The Data Flow:** The local adapter receives JSON-RPC requests from the agent, translates them into standard HTTP GET requests to our S3 bucket, and hands the retrieved JSON text back to the agent.

## Key Benefits

### 1. Zero/Ultra-Low Cloud Cost

Because there is no API Gateway, no Lambda invocations, and no live database to query, our AWS bill remains virtually untouched regardless of how many AI agents use our server. We only pay pennies for S3/CloudFront data transfer out.

### 2. Maximum Security & Abuse Prevention

By removing dynamic cloud compute, we completely eliminate the risk of backend prompt injection, recursive agent-loop DDOS attacks, and expensive runaway dynamic queries. Malicious agents can only ever download static files.

### 3. High Adaptability & Easy Updates

Distributing the adapter via a package registry ensures users always have the latest logic. Using executors like `npx -y` or `uvx`, the AI client automatically fetches the newest version of the adapter script on boot, making bug fixes and new endpoint additions completely transparent.

### 4. Alignment with Project Principles

This strongly aligns with `ADR-012` (Single Environment Strategy) and our guiding philosophy of "Static-First Design" by pushing complexity away from our cloud infrastructure.

---

## Implementation Steps

To get from our current state (Gold layer writing to S3) to a live Local Proxy MCP Server, we need to execute the following phases:

### Phase 1: S3 & Networking Configuration

1. Update `infrastructure/main.tf` to attach a CORS (Cross-Origin Resource Sharing) policy to the Gold S3 bucket to allow `GET` requests.
2. Ensure the specific `served/` prefix in the Gold bucket is publicly readable via an S3 Bucket Policy (or provision a CloudFront distribution pointing to it to save on bandwidth costs).

### Phase 2: Adapter Development

1. Choose a runtime for the adapter. (Note: While `npx`/Node is standard, Anthropic's official SDKs heavily support Python via `uvx`. Given `ADR-002` establishes Python as our primary language, building the adapter in Python using the `mcp` package and distributing it via PyPI is highly recommended).
2. Create the adapter script with two primary capabilities:
* `resources/list`: Fetches an `index.json` from S3 and returns the available datasets.
* `resources/read`: Fetches a specific JSON file (e.g., `player_daily/2544.json`) and returns it to the agent.



### Phase 3: Distribution & Documentation

1. Publish the adapter to the chosen registry (PyPI or npm).
2. Update `MCP_CLIENT_SETUP.md` with the 5-line JSON configuration users need to paste into their AI clients.

---

## Gap Analysis: ADRs and Planning Docs

To successfully execute this pivot, we need to clean up our documentation and formalize these decisions.

### Missing Architecture Decision Records (ADRs)

We must draft and accept the following ADRs:

* **ADR-033: Local Proxy Architecture for MCP Integration:** Explicitly rejecting cloud-hosted Lambda compute for MCP in favor of a local adapter.
* **ADR-034: Adapter Runtime and Distribution:** Deciding whether to build the adapter in TypeScript (`npx`) for broader ecosystem alignment, or Python (`uvx`) to maintain consistency with `ADR-002: Python First`.
* **ADR-035: Gold S3 Public Access Strategy:** Defining the security and cost boundaries for exposing the Gold bucket over the open internet (e.g., direct S3 vs. CloudFront).

### Outdated Planning Documents (To be deleted/archived)

The following files in `meta/plans/` are now inaccurate based on this new direction and should be archived or heavily rewritten:

* ❌ `meta/plans/mcp-server-architecture.md`: Likely assumes a cloud-hosted API Gateway/Lambda model. Needs a total rewrite to reflect the local proxy pattern.
* ❌ `meta/plans/stateless-gold-access-plan.md`: Needs alignment to confirm access will happen exclusively via the local adapter.
* ❌ `examples/mcp-claude-desktop-config.json.deprecated`: Remove entirely.
* ❌ `docs-src/MCP_CLIENT_SETUP.md`: Needs to be updated to replace complex cloud connection steps with a simple `npx`/`uvx` configuration block.
