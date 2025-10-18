---
title: "ADR-027: Stateless Gold Access via JSON Artifacts (Public)"
status: "Accepted"
date: "2025-10-01"
supersedes: "ADR-026"
tags:
  - "data-architecture"
  - "gold-layer"
  - "json-artifacts"
  - "public-access"
---

## Context

We need to expose read-only basketball analytics via a stateless, open (no-auth) public interface with strict rate limits and minimal moving parts. This ADR adopts a JSON-artifact serving approach optimized for small payloads and simple, direct access from browsers and apps. It supersedes ADR-026 (S3 Tables/Iceberg for public serving), which introduced complexity that isn't required for the public use case.

## Decision

**Implement a stateless JSON presentation layer inside Gold:**

- **Purpose**: Fast serving, simple consumption, direct browser/app access (no auth)
- **Technology**: Pre-computed JSON artifacts in S3 under a `served/` prefix
- **Access Pattern**: Direct S3 HTTPS GET requests (optionally through CDN); no Lambda required
- **Use Cases**: Frontend apps, mobile clients, dashboards, Slack webhooks
- **Audience**: General public, developers, LLM clients via MCP proxy if added later

### **Data Flow**
```
Silver → Gold Analytics Job → JSON Artifacts (S3 Public) → Direct HTTP GET → Browsers/Apps
```

Artifacts are generated from Gold computations and schema-versioned to allow evolution without breaking clients.

## Implementation Strategy

### **Implementation Outline**
1) Gold processing writes JSON artifacts (≤100KB):
  - `served/player_daily/{date}/{player_id}.json`
  - `served/team_daily/{date}/{team_id}.json`
  - `served/top_lists/{date}/{top_ts|top_per|top_efg|top_net}.json`
  - `served/index/latest.json` (or `latest_dates.json`)
2) S3 public read access to `served/` with CORS; optional CDN for caching
3) Optional later: small Lambda MCP adapter that fetches these artifacts

## Rationale

### **Benefits**
- **Simple and fast**: Direct GET of small JSON files; ideal for frontend consumption  
- **Cost control**: No per-request Lambda costs; small payloads and caching
- **Evolvable**: Schema versioned (`version: v1`), easy to extend
- **Low friction**: Public, no-auth experience for easy adoption
- **User adoption**: Easy JSON consumption removes barriers to entry
- **Scalability**: Each tier can scale independently based on usage patterns

### **Technical Notes**
- **Size limit**: ≤100KB per artifact; split/paginate if larger
- **Embed names**: Include `player_name`, `team_abbr` for UX  
- **Indices**: Maintain `served/index/latest.json` for discoverability
- **Observability**: Light logging on generation; CDN/S3 access logs optional

## Consequences

### **Positive**
- **Best of both worlds**: Sophisticated analytics + simple consumption
- **Resume differentiation**: Shows ability to design multi-tier systems
- **User adoption**: Lower barriers for casual users via JSON
- **Performance optimization**: Right-sized solutions for different use cases
- **Incremental delivery**: Can deliver value in phases

### **Consequences**
**Positive**
- Low latency and low cost public access
- Minimal moving parts; easy to maintain
- Clear contract via versioned JSON

**Negative**
- No ad-hoc querying server-side (by design)
- Requires careful payload budgeting

**Neutral**
- Future MCP adapter can proxy these artifacts if needed

### **Neutral**
- **Development effort**: ~50% more work than single-tier approach
- **Operational overhead**: Two MCP servers to monitor (but simple JSON server is minimal)

## Success Metrics

### **Phase 1 (Iceberg Foundation)**
- [ ] Complex analytical queries execute in <10 seconds
- [ ] Schema evolution demonstrated with backward compatibility
- [ ] PyIceberg integration with proper partitioning and performance

### **Success Criteria**
- [ ] JSON endpoints respond in <100ms via S3/CloudFront
- [ ] CORS properly configured for browser access
- [ ] Frontend applications consume data directly via HTTPS

### **Overall System**
- [ ] 95% of simple queries served from JSON layer
- [ ] Complex analytical queries demonstrate Iceberg capabilities
- [ ] Total monthly cost remains under $50

## Implementation Notes

### **JSON Artifact Schema**
- **Size limit**: ≤100KB per artifact
- **Versioning**: Include schema version in each JSON response
- **Embedding**: Include human-readable names (player_name, team_abbr) to minimize lookups

### **Iceberg Schema Evolution Example**
```python
# Demonstrate adding new metrics without breaking existing queries
schema_v1 = pa.schema([
    pa.field("player_id", pa.int64()),
    pa.field("date", pa.date32()),
    pa.field("points", pa.int32()),
    pa.field("true_shooting_pct", pa.float64())
])

schema_v2 = pa.schema([
    pa.field("player_id", pa.int64()),
    pa.field("date", pa.date32()), 
    pa.field("points", pa.int32()),
    pa.field("true_shooting_pct", pa.float64()),
    pa.field("player_impact_estimate", pa.float64())  # New metric
])
```

This approach maximizes both technical learning and practical utility while maintaining the project's focus on simplicity and cost-effectiveness.