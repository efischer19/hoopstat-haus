---
title: "ADR-031: Bronze Layer File Granularity - One File Per Game"
status: "Accepted"
date: "2025-12-31"
tags:
  - "data-pipeline"
  - "bronze-layer"
  - "data-storage"
  - "file-format"
---

## Context

* **Problem:** The bronze-ingestion app currently writes all games for a given date to the exact same S3 key (`raw/box_scores/date=YYYY-MM-DD/data.json`). This causes each subsequent game processed for that day to overwrite the previous one, resulting in data loss. Only the last game processed is actually stored in the Bronze layer.
* **Constraints:** ADR-025 (JSON Storage MVP) specifies JSON format but does not define the file naming convention or cardinality (one file per day vs. per game). This ambiguity led to the current incorrect implementation where multiple entity instances (games) are stored to a single file path.
* **Impact:** The silver-processing app is coupled to this bug, as it expects to read a single file at `raw/box_scores/date=YYYY-MM-DD/data.json` and parse it as a single `BoxScoreRaw` object. Multiple games on the same day cannot be processed correctly.

## Decision

Bronze layer storage will use **one file per entity instance** (e.g., per game), not one file per date.

**File naming pattern:**
```
raw/{entity}/date={YYYY-MM-DD}/{entity_id}.json
```

**Specific example for box scores:**
```
raw/box_scores/date=2025-10-25/0022400001.json
raw/box_scores/date=2025-10-25/0022400002.json
raw/box_scores/date=2025-10-25/0022400003.json
```

**Rationale:**
- Each game is a distinct entity instance that should be stored independently
- Prevents data loss when multiple games occur on the same day
- Enables granular processing, reprocessing, and debugging of individual games
- Aligns with the principle that Bronze layer should preserve all raw data
- Supports future requirements like game-specific reprocessing or validation

## Considered Options

1. **One File Per Game (The Chosen One):** Store each game as a separate JSON file using the game ID in the filename.
   * *Pros:* No data loss, granular control, easy to debug specific games, supports partial reprocessing, clear one-to-one mapping between API response and stored file
   * *Cons:* More S3 objects (minimal cost impact at current scale), requires listing files to process all games for a date

2. **One File Per Date (Status Quo):** Continue storing all games for a date in a single `data.json` file.
   * *Pros:* Fewer S3 objects, single file read per date
   * *Cons:* Current implementation loses data by overwriting, would require refactoring to store array of games, makes debugging individual games harder, all-or-nothing processing

3. **Append to Single File:** Modify the ingestion to append each game to the same file.
   * *Pros:* Single file per date
   * *Cons:* S3 doesn't support append operations natively, would require read-modify-write pattern (race conditions, more complex, higher latency), still has all-or-nothing processing issues

## Consequences

* **Positive:** 
  - All games for a date are preserved without data loss
  - Individual games can be reprocessed or validated independently
  - Debugging is easier with one file per game
  - Clear, predictable storage pattern for Bronze layer
  - Aligns with Bronze layer principle of preserving raw data
  - Future-proof for game-level operations

* **Negative:** 
  - More S3 objects (estimated ~30 games/day → ~900 objects/month, minimal cost impact)
  - Silver processing must list files under date prefix and iterate (minor complexity increase)
  - Requires migration for any existing Bronze data (if any)

* **Future Implications:** 
  - This pattern should extend to other Bronze layer entities that have multiple instances per date
  - Silver layer must implement file listing and iteration for date-based processing
  - Establishes a precedent for entity-level granularity in Bronze layer
  - Enables future optimizations like parallel processing of individual games

## Implementation Notes

### Bronze Layer Changes
- `BronzeS3Manager.store_json()` accepts optional `game_id` parameter
- File key format: `raw/{entity}/date={date}/{game_id}.json`
- Backward compatibility: if `game_id` is None, use `data.json` (for non-game entities like schedule)

### Silver Layer Changes
- `BronzeToSilverProcessor.read_bronze_json()` lists all objects under `date=YYYY-MM-DD/` prefix
- Iterates through each file and yields/returns list of `BoxScoreRaw` objects
- Main processing loop handles list of games rather than single game object

### Migration Strategy
- No migration needed for MVP (Bronze layer is transient and can be repopulated)
- If historical data exists, can be regenerated from source API or left as-is
- New data follows new pattern immediately after deployment
