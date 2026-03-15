# feat: Add integration tests for JSON artifact writing in Gold processor

## What do you want to build?

Add comprehensive tests that verify the `GoldProcessor` correctly delegates to
`JSONArtifactWriter` for all artifact types. This covers daily writing (player
and team), top lists, latest index, and season aggregations.

The existing test file (`apps/gold-analytics/tests/test_processors.py`) already
contains a note indicating that storage tests were removed when the previous
storage approach was abandoned, and should be re-added once JSON artifact
writing is implemented.

## Acceptance Criteria

- [ ] Tests verify `_store_player_analytics` calls `write_player_daily_artifacts`
- [ ] Tests verify `_store_team_analytics` calls `write_team_daily_artifacts`
- [ ] Tests verify `process_date` calls `write_top_lists` and `write_latest_index` on success
- [ ] Tests verify `_store_season_aggregations` calls `write_player_season_artifacts`
- [ ] Tests verify `_store_team_season_aggregations` calls `write_team_season_artifacts`
- [ ] Tests verify dry-run mode skips all artifact writing
- [ ] Tests verify error handling when artifact writing fails
- [ ] The "Note: Re-add storage tests" comment in `test_processors.py` is removed
- [ ] All existing tests continue to pass

## Implementation Notes (Optional)

**Key files:**
- `apps/gold-analytics/tests/test_processors.py` — add new test class or methods

**Approach:**
- Mock `JSONArtifactWriter` to verify it is called with the correct arguments
- Test both happy path and error scenarios
- Follow existing test patterns in `test_processors.py` (uses `unittest.mock.patch`, `MagicMock`)
- Consider a dedicated test class like `TestGoldProcessorArtifactWriting`

**Depends on:** Tickets 01–05 (all artifact writing must be implemented first)

**Relevant ADR:** ADR-028 (Gold Layer Architecture)
