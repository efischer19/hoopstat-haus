# feat: Update Gold analytics documentation for JSON artifact integration

## What do you want to build?

Update the Gold analytics README and any related documentation to reflect the
completed JSON artifact integration. Replace "not yet implemented" and
"Planned" markers with accurate descriptions of the implemented functionality.

## Acceptance Criteria

- [ ] `apps/gold-analytics/README.md` "Storage & Partitions" section reflects implemented JSON artifacts
- [ ] `apps/gold-analytics/README.md` "Public JSON Artifacts (Planned)" section is updated to describe actual behavior, usage, and artifact paths
- [ ] README includes examples of artifact keys and their JSON structure
- [ ] README documents the Cache-Control strategy (5-min index, 1-year historical)
- [ ] Any remaining "(not yet implemented)" text in the README is removed or updated
- [ ] Documentation is consistent with ADR-028 and ADR-038

## Implementation Notes (Optional)

**Key files:**
- `apps/gold-analytics/README.md`

**Content to add:**
- Artifact path conventions: `served/player_daily/{date}/{player_id}.json`, etc.
- Cache-Control behavior (ADR-038)
- How the `status` command validates artifacts
- Example JSON snippets for each artifact type (player daily, team daily, top lists, season aggregations)

**Depends on:** Tickets 01–06 (all implementation and tests complete)

**Relevant ADR:** ADR-028 (Gold Layer Architecture), ADR-038 (CloudFront Cache Tuning)
