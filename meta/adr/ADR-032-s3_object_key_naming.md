---
title: "ADR-032: S3 Object Key Naming - Avoid URL-Encoded Characters"
status: "Accepted"
date: "2026-01-01"
tags:
  - "data-pipeline"
  - "bronze-layer"
  - "silver-layer"
  - "s3"
  - "infrastructure"
---

## Context

* **Problem:** S3 object keys that contain characters requiring URL encoding (such as `=`, `_`, spaces, etc.) cause issues with S3 event notification filters. In PR #462, we discovered that filter prefix and suffix patterns don't work correctly with URL-encoded characters. Specifically, paths like `raw/box_scores/date=2025-12-31/` use both underscore (`_`) in `box_scores` and equals sign (`=`) in the date partition, which must be URL-encoded in S3 event notification configurations.

* **Constraints:** 
  - S3 allows a wide range of characters in object keys, but not all are web-safe
  - S3 event notification filters use string matching on the raw key, but when configured via Terraform/API, special characters may need URL encoding
  - Existing data uses the current naming pattern and will need migration or coexistence strategy
  - AWS S3 best practices recommend avoiding special characters in object keys

* **Impact:** 
  - S3 event notifications fail to trigger when filters contain URL-encoded characters
  - Debugging and troubleshooting is harder when keys require URL encoding
  - Manual S3 operations (copying, moving, referencing) are more error-prone
  - External tools and integrations may have inconsistent handling of special characters

## Decision

**All S3 object keys in the hoopstat-haus data pipeline must use only URL-safe characters.**

**Allowed characters:**
- Lowercase letters: `a-z`
- Numbers: `0-9`
- Forward slash: `/` (for path hierarchy)
- Hyphen: `-` (for separators within path segments)

**Prohibited characters in object keys:**
- Underscore: `_`
- Equals: `=`
- Spaces
- Special characters requiring URL encoding: `!`, `*`, `'`, `(`, `)`, `;`, `:`, `@`, `&`, `+`, `$`, `,`, `?`, `#`, `[`, `]`, `%`, etc.

**New naming pattern for Bronze layer:**
```
raw/{entity-type}/{YYYY-MM-DD}/{filename}.json
```

**Specific examples:**
```
Old: raw/box_scores/date=2025-12-31/0022400123.json
New: raw/box/2025-12-31/0022400123.json

Old: raw/player_info/date=2025-12-31/data.json
New: raw/player/2025-12-31/data.json

Old: raw/team_stats/date=2025-12-31/data.json  
New: raw/team/2025-12-31/data.json
```

**Rationale:**
- Eliminates URL encoding issues in S3 event notifications and filters
- Simplifies debugging, logging, and manual S3 operations
- Improves compatibility with external tools and services
- Makes paths more readable and less error-prone
- Aligns with AWS S3 best practices
- Shorter entity names (`box` vs `box_scores`) reduce path length and improve readability

## Considered Options

1. **URL-safe characters only (chosen option):** Restrict all keys to characters that never need URL encoding
   * *Pros:* No encoding issues, simpler operations, better tool compatibility, clearer paths
   * *Cons:* Requires migration from existing naming, more restrictive naming

2. **Keep current naming with proper URL encoding:** Continue using `_` and `=` but ensure all filters properly URL-encode them
   * *Pros:* No migration needed, more descriptive names
   * *Cons:* Ongoing complexity in configuration, potential for encoding errors, harder to debug

3. **Hybrid approach:** Use URL-safe characters for new entities, keep existing for legacy
   * *Pros:* No migration, gradual transition
   * *Cons:* Inconsistent naming, confusing for developers, technical debt

4. **Use dot separators:** Replace `_` with `.` (e.g., `box.scores`)
   * *Pros:* Familiar pattern from domain names
   * *Cons:* Dots have special meaning in some contexts, still less clear than hyphens or short names

## Consequences

* **Positive:**
  - S3 event notification filters work reliably without URL encoding
  - Cleaner, more maintainable infrastructure code
  - Reduced cognitive load when working with S3 paths
  - Better compatibility with AWS services and third-party tools
  - Shorter, more readable paths
  - Prevents future encoding-related bugs

* **Negative:**
  - Requires updating all existing code, tests, and documentation
  - Entity names are abbreviated (`box` instead of `box_scores`)
  - Migration complexity if existing production data uses old patterns

* **Future Implications:**
  - All new entities must follow this naming convention
  - Code reviews should verify URL-safe naming in S3 keys
  - This pattern extends to Silver and Gold layers
  - Documentation and examples must reflect new naming

## Implementation Notes

### Path Migration

**Bronze layer:**
- `raw/box_scores/date=YYYY-MM-DD/` → `raw/box/YYYY-MM-DD/`
- `raw/schedule/date=YYYY-MM-DD/` → `raw/schedule/YYYY-MM-DD/`
- `raw/player_info/date=YYYY-MM-DD/` → `raw/player/YYYY-MM-DD/`

**Silver layer:**
- `silver/player_stats/date=YYYY-MM-DD/` → `silver/player-stats/YYYY-MM-DD/`
- `silver/team_stats/date=YYYY-MM-DD/` → `silver/team-stats/YYYY-MM-DD/`
- `silver/game_stats/date=YYYY-MM-DD/` → `silver/game-stats/YYYY-MM-DD/`

### Code Changes Required

1. **Bronze ingestion app:**
   - Update `BronzeS3Manager.store_json()` key generation
   - Update all test fixtures and assertions

2. **Silver processing app:**
   - Update Bronze data reading logic
   - Update Silver data writing logic
   - Update S3 event parsing
   - Update all test fixtures

3. **hoopstat-s3 library:**
   - Update `SilverS3Manager` path construction
   - Update all test cases

4. **Terraform infrastructure:**
   - Update S3 event notification filter prefix patterns
   - Update any hardcoded paths in configurations

5. **Documentation:**
   - Update all examples in ADRs, guides, and scripts
   - Update deployment and testing documentation

### Migration Strategy

- No migration needed for transient Bronze layer (data can be regenerated)
- For production: run parallel processing with both old and new paths during transition
- Update S3 event filters to match new pattern
- Monitor for 24-48 hours to ensure no issues
- Gradually deprecate old path support

### Validation

- All tests must pass with new paths
- S3 event notifications must trigger correctly
- Manual verification of end-to-end pipeline
- Infrastructure apply must succeed without URL encoding in filters
