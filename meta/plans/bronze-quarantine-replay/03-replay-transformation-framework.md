# Ticket 03: Replay Transformation Framework

## What do you want to build?

Create a pluggable transformation layer that can patch or adjust quarantined data before replaying it through the Silver validation pipeline. This is the "fix" step between "review" (Ticket 02) and "replay" (Ticket 04).

Not all quarantined data can be replayed as-is. Some cases require targeted transformations:
- **Transient errors:** No transformation needed -- replay the original payload (identity transform).
- **Rounding mismatches:** Apply a tolerance-aware normalization that adjusts player stat sums to match team totals within an acceptable epsilon.
- **Schema changes:** Apply a structural mapping to adapt the payload to the expected format.
- **Custom patches:** Allow ad-hoc transformation functions for one-off data fixes.

The framework should be simple, testable, and extensible without requiring code changes for each new error type.

## Acceptance Criteria

- [ ] A `ReplayTransform` abstract base class (or Protocol) is defined with a single method: `transform(quarantine_record: dict) -> dict` that takes a quarantine record and returns a transformed payload ready for Silver validation.
- [ ] At least three concrete implementations are provided:
  - `IdentityTransform` -- Returns the original data unchanged. Used for transient error replays.
  - `RoundingToleranceTransform` -- Adjusts player stat sums to reconcile with team totals within a configurable tolerance (default: 0.01 per ADR-028/Gold layer patterns). Logs all adjustments made.
  - `SchemaRemapTransform` -- Applies a field-mapping dictionary to adapt payloads from one API format version to another.
- [ ] A `get_transform_for_classification(classification: ErrorClassification) -> ReplayTransform` factory function maps error classifications to their default transform. Custom overrides are possible.
- [ ] Each transform is independently unit-tested with realistic quarantine record fixtures.
- [ ] Transforms are pure functions with no side effects (no S3 writes, no state mutations) -- they only modify and return data.
- [ ] Transform results include a `transform_metadata` dict documenting what changes were applied (for audit trail).

## Implementation Notes (Optional)

**Module location:** `apps/bronze-ingestion/app/transforms.py` (new file).

**RoundingToleranceTransform details:**
- Iterate over stat categories (points, rebounds, assists, etc.)
- For each category, compute `sum(player_values)` and compare to `team_value`
- If `abs(sum - team) <= tolerance`, adjust the last player's value to make the sum exact
- If `abs(sum - team) > tolerance`, raise a `TransformError` -- the discrepancy is too large to be a rounding issue
- Log every adjustment: `"Adjusted player {name} {stat} from {old} to {new} (delta: {delta})"`

**SchemaRemapTransform details:**
- Accept a `field_map: dict[str, str]` in the constructor
- Apply key renaming recursively
- Useful when the NBA API changes field names between versions (e.g., V3 `boxScoreTraditional` vs. legacy `resultSets`)

**Design principles:**
- Follow the Strategy pattern for clean extensibility
- Keep transforms stateless and side-effect-free for testability
- Each transform should document its purpose via docstrings
- Consider adding a `CompositeTransform` that chains multiple transforms if needed (YAGNI for now, but design should not preclude it)
