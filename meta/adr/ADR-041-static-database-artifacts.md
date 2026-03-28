---
title: "ADR-041: Polyglot Static Database Artifacts (DuckDB & SQLite) for SQL-Native Analytics"
status: "Accepted"
date: "2026-03-28"
tags:
  - "data-architecture"
  - "duckdb"
  - "sqlite"
  - "analytics"
  - "mcp"
  - "cost-optimization"
---

## Context

* **Problem:** The Gold layer currently serves pre-computed JSON artifacts via CloudFront (per ADR-028 and ADR-035). While this JSON-first approach is highly cost-effective and works perfectly for our lightweight frontend and existing MCP proxy, it imposes a fundamental limitation: JSON files do not support arbitrary relational queries. If a developer or an AI Agent wants to answer a complex question that spans multiple datasets (e.g., "Which players averaged >25ppg and >5apg this season?"), they must download multiple JSON files and perform joins and aggregations in client-side code. This limits the analytical surface area for both human developers and AI agents.

* **Constraints:**
  - ADR-033 (Local Proxy Pattern) rejects cloud compute for data serving — any SQL execution must happen on the client, not in AWS.
  - ADR-012 (Single Environment) and the project's static-first philosophy require that this remain a build-time artifact, not a live database.
  - ADR-035 (CloudFront + OAC) means all public assets must be served via CloudFront from the Gold S3 bucket's `served/` prefix.
  - ADR-038 (Cache Tuning) establishes differentiated TTLs — the database files will need their own caching strategy.
  - DuckDB supports HTTP Range Requests, enabling SQL queries against a remote file without downloading the entire database — but this requires proper CORS and `Accept-Ranges` headers from the CDN.
  - SQLite is the most widely deployed database engine in the world, providing ubiquitous compatibility across every major platform, language, and framework.
  - Our dataset is microscopic: a single NBA season of box scores is only a few megabytes. The marginal cost of generating a second database format during the build step is ~2 seconds of compute and fractions of a penny in storage.
  - Hosting costs must remain near-zero. No live databases, no connection pools, no per-query compute.

## Decision

**We will adopt a Polyglot Data Distribution strategy: periodically compile Gold-layer data into both a static DuckDB (`.duckdb`) and a static SQLite (`.sqlite`) database file, publishing them alongside existing JSON artifacts under the `served/db/` prefix in S3.**

This dual-format approach maximizes Developer Experience (DX) across two distinct user bases without adding meaningful architectural complexity:

- **DuckDB** serves modern AI Agents, Data Scientists, and our MCP proxy by enabling HTTP Range Requests for zero-compute, remote analytical SQL.
- **SQLite** serves traditional web and mobile developers (e.g., iOS, Flask, PHP apps) by providing a ubiquitous, bulletproof artifact that requires zero third-party drivers or new mental models.

The architecture:

1. **Build-Time Compilation:** A Python script (`apps/db-compiler`) ingests the latest Gold JSON artifacts, loads them into an in-memory representation (e.g., via Pandas or a list of dicts), and performs two sequential writes: first a `.duckdb` file with DuckDB-optimized schemas and indexes, then a `.sqlite` file with equivalent SQLite-compatible schemas and indexes. Both files are produced from the same in-memory dataset in a single build invocation.

2. **Static Publishing:** Both files are uploaded to the Gold S3 bucket:
   - `served/db/nba_current_season.duckdb`
   - `served/db/nba_current_season.sqlite`

   Both inherit the existing CloudFront + OAC serving infrastructure (ADR-035).

3. **Client-Side SQL:** Developers choose the format that fits their stack:
   - **DuckDB users** query the `.duckdb` file remotely via HTTP Range Requests (DuckDB CLI, Python `duckdb` package, WASM).
   - **SQLite users** download the `.sqlite` file and query it locally with any SQLite-compatible tool (Python `sqlite3`, iOS Core Data, PHP PDO, the `sqlite3` CLI, sql.js in the browser, etc.).

4. **MCP Integration:** The MCP local proxy (per ADR-033) gains an `execute_nba_sql_query` tool that downloads/caches the DuckDB file locally and executes SQL queries, enabling AI agents to answer complex analytical questions natively.

**This decision explicitly maintains the zero-cloud-compute principle (ADR-033) — all SQL execution occurs on the client's machine.**

## Considered Options

1. **Polyglot: DuckDB + SQLite simultaneously (Chosen):** Compile Gold data into both formats from a single build step.
   * *Pros:* Maximizes developer reach — DuckDB for AI/analytics users, SQLite for traditional web/mobile developers; negligible marginal cost given our microscopic dataset (a few MB); single compilation pipeline loads data once and writes twice; both formats are self-contained single-file databases; DuckDB provides HTTP Range Requests for remote querying, SQLite provides universal local compatibility; no increase in architectural complexity.
   * *Cons:* Two files to publish, cache-invalidate, and document; SQLite file must be fully downloaded (no range-request support); minor additional CI time (~2 seconds).

2. **DuckDB only:** Compile Gold data into a single `.duckdb` file.
   * *Pros:* Single artifact to manage; HTTP Range Request support for remote queries; rich analytical SQL dialect.
   * *Cons:* Excludes developers who prefer or require SQLite; DuckDB is less universally known; misses the large traditional developer audience.

3. **SQLite only:** Compile Gold data into a single `.sqlite` file.
   * *Pros:* Most widely supported embedded database; universal tooling.
   * *Cons:* No HTTP Range Request support — clients must download the entire file; lacks DuckDB's analytical optimizations (columnar storage, vectorized execution); weaker analytical SQL dialect; misses the AI/data science audience.

4. **Parquet files with DuckDB remote queries:** Publish Gold data as Parquet files and let clients query them via DuckDB's Parquet reader.
   * *Pros:* Columnar format is efficient for analytical queries; Parquet is a widely understood format; no compilation step needed.
   * *Cons:* Requires clients to understand the file layout and join multiple Parquet files manually; no pre-built indexes or views; more complex client-side setup; less user-friendly than named tables; doesn't serve traditional web/mobile developers at all.

5. **Cloud-hosted SQL endpoint (Athena/RDS):** Provide a live SQL query endpoint.
   * *Pros:* Familiar SQL-as-a-service pattern; no client setup required.
   * *Cons:* Directly contradicts ADR-033 (zero cloud compute for data serving); introduces per-query costs; creates attack surface for runaway AI agent loops; violates static-first philosophy; operational complexity for monitoring and scaling.

## Consequences

* **Positive:**
  - Unlocks arbitrary SQL analytics against Gold-layer data without any cloud compute cost.
  - Maximizes Developer Experience across two distinct audiences: DuckDB for AI agents and data scientists, SQLite for traditional web/mobile developers.
  - AI agents (via MCP) can write and execute SQL natively, vastly expanding the analytical surface area beyond pre-computed JSON artifacts.
  - Developers get a familiar SQL interface with copy-paste examples for DuckDB CLI, SQLite CLI, Python, and WASM.
  - Maintains the zero-cloud-compute principle — all SQL runs on the client's machine.
  - Negligible marginal cost: generating the second format adds ~2 seconds and fractions of a penny per build.
  - DuckDB's HTTP Range Request support means most analytical queries only transfer a fraction of the file.
  - SQLite's ubiquity means any developer with a standard library can immediately use the data.

* **Negative:**
  - Adds a new build step (compilation workflow) to the data pipeline.
  - Two database files to publish, version, and cache-invalidate (mitigated by identical schemas and a single build step).
  - CloudFront requires configuration for proper range-request and CORS support for DuckDB (one-time infrastructure work).
  - SQLite file must be fully downloaded by clients (acceptable given the few-MB file size).
  - File sizes will grow as the season progresses; may need monitoring for future seasons.

* **Future Implications:**
  - Historical seasons can be compiled into separate database files (e.g., `nba_2024_25.duckdb`, `nba_2024_25.sqlite`) once the pattern is established.
  - The MCP proxy's `execute_nba_sql_query` tool positions the project as an "AI-native data product" — LLMs can answer complex basketball questions via SQL.
  - If DuckDB WASM matures, the frontend could offer a browser-based SQL playground against the same static file.
  - The SQLite file could power a sql.js-based browser query tool with minimal effort.
  - The compilation script can be extended to include additional data sources (play-by-play, etc.) as the Bronze layer expands.
  - ADR-038's caching strategy should be extended with a new cache behavior for the `db/*` path pattern.
