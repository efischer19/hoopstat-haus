# Plan: MCP Server Architecture for AI-Native Data Access

> **⚠️ ARCHIVED (2026-03-08):** This document previously described a cloud-hosted MCP server using AWS Lambda and API Gateway. That approach has been rejected in favor of a **Local Proxy Architecture** — see [ADR-033](../adr/ADR-033-local_proxy_mcp_architecture.md) for the accepted architectural direction.
>
> The original content has been removed to prevent confusion. The key decision is that all MCP JSON-RPC compute runs on the AI client's local machine via a lightweight adapter, and our cloud infrastructure serves only static, pre-computed JSON artifacts (per ADR-027 and ADR-028).

**Status:** ~~Planning~~ → Archived (superseded by ADR-033)  
**Date:** 2025-01-18 (Archived 2026-03-08)  
**Author:** AI Contributor  
**Scope:** ~~Design and specify the Model Context Protocol (MCP) server architecture for exposing Gold layer basketball data to AI agents~~ → See ADR-033
