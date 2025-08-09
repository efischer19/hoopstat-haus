# hoopstat-data

**Version:** 0.1.0

## Description

Hoopstat Data Processing Utilities

A shared library for basketball statistics data processing, validation,
transformation, quality checking, and Gold layer partitioning.

## Installation

Add to your application's `pyproject.toml`:

```toml
[tool.poetry.dependencies]
hoopstat-data = {path = "../libs/hoopstat-data", develop = true}
```

## Usage

```python
from hoopstat_data import PlayerStats, TeamStats, GameStats, GoldPlayerDailyStats, GoldPlayerSeasonSummary, GoldTeamDailyStats, validate_player_stats, validate_team_stats, validate_game_stats, validate_stat_ranges, normalize_team_name, calculate_efficiency_rating, standardize_position, clean_and_transform_record, clean_batch, validate_and_standardize_season, check_data_completeness, detect_outliers, DataCleaningRulesEngine, TransformationResult, S3PartitionKey, PartitionType, FileSizeOptimizer, QueryPatternOptimizer, PartitionHealthChecker, create_player_daily_partition, create_player_season_partition, create_team_daily_partition
```

## API Reference

### Classes

#### TransformationResult

Result of a data transformation operation.

#### DataCleaningRulesEngine

Configurable rules engine for data cleaning and standardization.

Applies data cleaning, standardization, and conforming transformations
to NBA data based on configurable YAML rules.

**Methods:**

- `standardize_team_name(self, team_name: str, use_fuzzy_matching: bool) -> TransformationResult`
  - Standardize team name using mapping table and fuzzy matching.
- `standardize_position(self, position: str) -> TransformationResult`
  - Standardize player position using mapping table.
- `handle_null_values(self, data: Any, entity_type: str) -> Any`
  - Handle null values according to configured rules.
- `clean_numeric_field(self, value: Any, field_name: str) -> TransformationResult`
  - Clean and validate numeric field with business rules.
- `standardize_datetime(self, value: Any, field_name: str) -> TransformationResult`
  - Standardize date/time values to consistent format.
- `apply_fuzzy_matching(self, value: str, candidates: Any, field_name: str) -> TransformationResult`
  - Apply fuzzy string matching to find best candidate.
- `process_batch(self, records: Any, entity_type: str) -> Any`
  - Process a batch of records with all cleaning rules.
- `get_transformation_summary(self) -> Any`
  - Get summary of all transformations applied.
- `clear_transformation_log(self) -> None`
  - Clear the transformation log.

#### PartitionType

Supported partition types for Gold layer data.

#### S3PartitionKey

S3 partition key for Gold layer data with hierarchical structure.

**Methods:**

- `validate_season_format(cls, v: str) -> str`
  - Validate NBA season format.
- `validate_date_format(cls, v: Any) -> Any`
  - Validate date format if provided.
- `s3_prefix(self) -> str`
  - Generate S3 prefix from partition key components.
- `s3_path(self) -> str`
  - Generate full S3 path including bucket and filename.
- `local_path(self) -> Path`
  - Generate local file path structure matching S3 hierarchy.

#### FileSizeOptimizer

Utilities for optimizing file sizes for Lambda performance.

**Methods:**

- `estimate_parquet_size(row_count: int, avg_row_size_bytes: int) -> int`
  - Estimate Parquet file size based on row count.
- `should_split_file(cls, row_count: int, avg_row_size_bytes: int) -> bool`
  - Determine if file should be split based on estimated size.
- `recommend_split_strategy(cls, row_count: int, avg_row_size_bytes: int) -> Any`
  - Recommend splitting strategy for large files.

#### QueryPatternOptimizer

Utilities for optimizing data layout for common query patterns.

**Methods:**

- `get_optimal_partition_key(cls, query_pattern: str) -> S3PartitionKey`
  - Generate optimal partition key for a given query pattern.
- `list_query_patterns(cls) -> Any`
  - List available query patterns with descriptions.

#### PartitionHealthChecker

Utilities for monitoring partition health and performance.

**Methods:**

- `calculate_partition_hash(partition_key: S3PartitionKey) -> str`
  - Calculate a hash for partition identification and change detection.
- `validate_partition_structure(partition_key: S3PartitionKey) -> Any`
  - Validate partition structure against ADR-020 standards.

#### ValidationMode

Validation strictness levels for schema validation.

#### DataLineage

Data lineage tracking information.

#### BaseSilverModel

Base model for all Silver layer entities with common metadata.

#### PlayerStats

Player statistics data model.

**Methods:**

- `validate_field_goals(cls, v, info) -> Any`
  - Ensure field goals attempted >= field goals made.
- `validate_points_range(cls, v, info) -> Any`
  - Validate points are within reasonable NBA game ranges.
- `validate_player_name(cls, v) -> Any`
  - Ensure player name is properly formatted.
- `validate_shooting_consistency(self) -> Any`
  - Validate shooting statistics consistency.

#### TeamStats

Team statistics data model.

**Methods:**

- `validate_team_name(cls, v) -> Any`
  - Ensure team name is valid NBA team.
- `validate_points_range(cls, v, info) -> Any`
  - Validate team points are within reasonable NBA game ranges.
- `validate_team_shooting_stats(self) -> Any`
  - Validate team shooting statistics consistency.

#### GameStats

Game statistics data model.

**Methods:**

- `validate_game_date(cls, v) -> Any`
  - Ensure game date is in ISO format if provided.
- `validate_season_format(cls, v) -> Any`
  - Validate NBA season format (e.g., '2023-24').
- `validate_game_logic(self) -> Any`
  - Validate game logic and constraints.

#### BaseGoldModel

Base model for all Gold layer entities with computed metrics.

#### GoldPlayerDailyStats

Gold layer player daily statistics with pre-computed metrics.

**Methods:**

- `validate_ts_percentage(cls, v) -> Any`
  - Validate true shooting percentage is reasonable.
- `validate_season_format(cls, v) -> Any`
  - Validate NBA season format.

#### GoldPlayerSeasonSummary

Gold layer player season summary with aggregated statistics.

**Methods:**

- `validate_season_format(cls, v) -> Any`
  - Validate NBA season format.

#### GoldTeamDailyStats

Gold layer team daily statistics with computed metrics.

#### SchemaEvolution

Handles schema versioning and evolution.

**Methods:**

- `migrate_from_version(data: Any, from_version: str, to_version: str) -> Any`
  - Migrate data from one schema version to another.

### Functions

#### normalize_team_name

```python
normalize_team_name(team_name: str, use_rules_engine: bool) -> str
```

Normalize team names to a standard format.

Args:
    team_name: Raw team name
    use_rules_engine: Whether to use the configurable rules engine

Returns:
    Normalized team name

Example:
    >>> normalize_team_name("lakers")
    "Los Angeles Lakers"
    >>> normalize_team_name("LA Lakers")
    "Los Angeles Lakers"

#### calculate_efficiency_rating

```python
calculate_efficiency_rating(stats: Any) -> float
```

Calculate player efficiency rating (PER-like metric).

Simplified calculation:
(Points + Rebounds + Assists + Steals + Blocks - Turnovers) / Minutes

Args:
    stats: Dictionary containing player statistics

Returns:
    Efficiency rating as a float

Example:
    >>> stats = {
    ...     "points": 25, "rebounds": 10, "assists": 5,
    ...     "steals": 2, "blocks": 1, "turnovers": 3, "minutes_played": 35
    ... }
    >>> calculate_efficiency_rating(stats)
    1.14

#### standardize_position

```python
standardize_position(position: str, use_rules_engine: bool) -> str
```

Standardize player position to common abbreviations.

Args:
    position: Raw position string
    use_rules_engine: Whether to use the configurable rules engine

Returns:
    Standardized position abbreviation

Example:
    >>> standardize_position("Point Guard")
    "PG"
    >>> standardize_position("center")
    "C"

#### calculate_shooting_percentage

```python
calculate_shooting_percentage(made: int, attempted: int) -> Any
```

Calculate shooting percentage with proper handling of edge cases.

Args:
    made: Number of shots made
    attempted: Number of shots attempted

Returns:
    Shooting percentage as decimal (0.0 to 1.0), or None if invalid

Example:
    >>> calculate_shooting_percentage(8, 15)
    0.533
    >>> calculate_shooting_percentage(0, 0)
    None

#### convert_minutes_to_decimal

```python
convert_minutes_to_decimal(minutes_str: str) -> Any
```

Convert minutes from "MM:SS" format to decimal minutes.

Args:
    minutes_str: Time string in "MM:SS" format

Returns:
    Decimal minutes, or None if invalid format

Example:
    >>> convert_minutes_to_decimal("35:30")
    35.5
    >>> convert_minutes_to_decimal("12:45")
    12.75

#### normalize_stat_per_game

```python
normalize_stat_per_game(stat_value: float, games_played: int) -> Any
```

Normalize a cumulative stat to per-game average.

Args:
    stat_value: Cumulative statistic value
    games_played: Number of games played

Returns:
    Per-game average, or None if invalid

Example:
    >>> normalize_stat_per_game(250, 10)
    25.0

#### clean_and_transform_record

```python
clean_and_transform_record(record: Any, entity_type: str, use_rules_engine: bool) -> Any
```

Apply comprehensive cleaning and transformation to a single record.

Args:
    record: Dictionary containing raw data
    entity_type: Type of entity (player_stats, team_stats, game_stats)
    use_rules_engine: Whether to use the configurable rules engine

Returns:
    Cleaned and transformed record

Example:
    >>> record = {"team_name": "lakers", "points": "25", "position": "point guard"}
    >>> clean_and_transform_record(record)
    {"team_name": "Los Angeles Lakers", "points": 25, "position": "PG"}

#### clean_batch

```python
clean_batch(records: Any, entity_type: str, batch_size: int) -> Any
```

Clean a batch of records efficiently.

Args:
    records: List of records to clean
    entity_type: Type of entity (player_stats, team_stats, game_stats)
    batch_size: Number of records to process in each batch

Returns:
    List of cleaned records

Example:
    >>> records = [{"team_name": "lakers"}, {"team_name": "warriors"}]
    >>> clean_batch(records)
    [{"team_name": "Los Angeles Lakers"}, {"team_name": "Golden State Warriors"}]

#### validate_and_standardize_season

```python
validate_and_standardize_season(season_str: str) -> Any
```

Validate and standardize NBA season format.

Args:
    season_str: Raw season string

Returns:
    Standardized season string (e.g., "2023-24") or None if invalid

Example:
    >>> validate_and_standardize_season("2023-2024")
    "2023-24"
    >>> validate_and_standardize_season("23-24")
    "2023-24"

#### check_data_completeness

```python
check_data_completeness(data: Any, required_fields: Any) -> Any
```

Check data completeness and return completion metrics.

Args:
    data: Dictionary containing data to check
    required_fields: Optional list of required field names

Returns:
    Dictionary with completeness metrics

Example:
    >>> data = {"points": 25, "rebounds": None, "assists": 5}
    >>> result = check_data_completeness(data)  # doctest: +SKIP
    # Returns completeness metrics dict

#### detect_outliers

```python
detect_outliers(values: Any, method: str, threshold: float) -> Any
```

Detect outliers in a list of numerical values.

Args:
    values: List of numerical values
    method: Detection method ("iqr" or "zscore")
    threshold: Threshold for outlier detection

Returns:
    List of indices of detected outliers

Example:
    >>> values = [10, 12, 11, 13, 15, 50, 14]
    >>> detect_outliers(values)
    [5]  # Index of the value 50

#### validate_stat_consistency

```python
validate_stat_consistency(player_stats: Any) -> Any
```

Validate consistency across multiple player stat records.

Args:
    player_stats: List of player statistics dictionaries

Returns:
    List of consistency issues found

Example:
    >>> stats = [
    ...     {"player_id": "123", "points": 25, "field_goals_made": 10},
    ...     {"player_id": "123", "points": -5, "field_goals_made": 15}
    ... ]
    >>> issues = validate_stat_consistency(stats)  # doctest: +SKIP
    # Returns list of consistency issues

#### calculate_data_quality_score

```python
calculate_data_quality_score(data: Any, weights: Any) -> float
```

Calculate an overall data quality score (0.0 to 1.0).

Args:
    data: Dictionary containing data to assess
    weights: Optional weights for different quality factors

Returns:
    Quality score from 0.0 (poor) to 1.0 (excellent)

Example:
    >>> data = {"points": 25, "rebounds": 10, "assists": 5}
    >>> calculate_data_quality_score(data)
    0.85

#### identify_missing_critical_stats

```python
identify_missing_critical_stats(data: Any) -> Any
```

Identify missing statistics that are critical for analysis.

Args:
    data: Dictionary containing player/team statistics

Returns:
    List of missing critical statistics

Example:
    >>> data = {"rebounds": 10, "assists": 5}
    >>> identify_missing_critical_stats(data)
    ['points']

#### compare_stat_distributions

```python
compare_stat_distributions(dataset1: Any, dataset2: Any, stat_name: str) -> Any
```

Compare statistical distributions between two datasets.

Args:
    dataset1: First dataset
    dataset2: Second dataset
    stat_name: Name of the statistic to compare

Returns:
    Dictionary with comparison metrics

Example:
    >>> data1 = [{"points": 20}, {"points": 25}]
    >>> data2 = [{"points": 15}, {"points": 30}]
    >>> compare_stat_distributions(data1, data2, "points")
    {'mean_diff': 0.0, 'std_diff': 3.54, 'sample_sizes': [2, 2]}

#### extract_values

```python
extract_values(dataset, stat) -> Any
```

#### validate_player_stats

```python
validate_player_stats(stats_data: Any) -> bool
```

Validate player statistics data for consistency and logical constraints.

Args:
    stats_data: Dictionary containing player statistics

Returns:
    bool: True if all validations pass, False otherwise

Example:
    >>> stats = {"points": 25, "rebounds": 10, "assists": 5}
    >>> validate_player_stats(stats)
    True

#### validate_team_stats

```python
validate_team_stats(stats_data: Any) -> bool
```

Validate team statistics data for consistency and logical constraints.

Args:
    stats_data: Dictionary containing team statistics

Returns:
    bool: True if all validations pass, False otherwise

Example:
    >>> stats = {"team_name": "Lakers", "points": 120, "field_goals_made": 45}
    >>> validate_team_stats(stats)
    True

#### validate_game_stats

```python
validate_game_stats(stats_data: Any) -> bool
```

Validate game statistics data for consistency and logical constraints.

Args:
    stats_data: Dictionary containing game statistics

Returns:
    bool: True if all validations pass, False otherwise

Example:
    >>> stats = {"home_score": 110, "away_score": 105, "game_id": "game_123"}
    >>> validate_game_stats(stats)
    True

#### validate_stat_ranges

```python
validate_stat_ranges(stats_data: Any, stat_ranges: Any) -> Any
```

Validate that statistics fall within expected ranges.

Args:
    stats_data: Dictionary containing statistics to validate
    stat_ranges: Optional dictionary of (min, max) ranges for each stat

Returns:
    List of validation error messages (empty if all valid)

Example:
    >>> stats = {"points": 25, "rebounds": -5}
    >>> validate_stat_ranges(stats)
    ['rebounds value -5 is outside expected range (0, 50)']

#### standardize_team_name

```python
standardize_team_name(self, team_name: str, use_fuzzy_matching: bool) -> TransformationResult
```

Standardize team name using mapping table and fuzzy matching.

Args:
    team_name: Raw team name
    use_fuzzy_matching: Whether to use fuzzy matching as fallback

Returns:
    TransformationResult with standardized team name

#### standardize_position

```python
standardize_position(self, position: str) -> TransformationResult
```

Standardize player position using mapping table.

Args:
    position: Raw position string

Returns:
    TransformationResult with standardized position

#### handle_null_values

```python
handle_null_values(self, data: Any, entity_type: str) -> Any
```

Handle null values according to configured rules.

Args:
    data: Dictionary containing data to clean
    entity_type: Type of entity (player_stats, team_stats, game_stats)

Returns:
    Cleaned data dictionary

#### clean_numeric_field

```python
clean_numeric_field(self, value: Any, field_name: str) -> TransformationResult
```

Clean and validate numeric field with business rules.

Args:
    value: Raw numeric value
    field_name: Name of the field for validation rules

Returns:
    TransformationResult with cleaned numeric value

#### standardize_datetime

```python
standardize_datetime(self, value: Any, field_name: str) -> TransformationResult
```

Standardize date/time values to consistent format.

Args:
    value: Raw datetime value
    field_name: Name of the field (for specific handling)

Returns:
    TransformationResult with standardized datetime

#### apply_fuzzy_matching

```python
apply_fuzzy_matching(self, value: str, candidates: Any, field_name: str) -> TransformationResult
```

Apply fuzzy string matching to find best candidate.

Args:
    value: String value to match
    candidates: List of candidate values to match against
    field_name: Field name for configuration lookup

Returns:
    TransformationResult with best match or original value

#### process_batch

```python
process_batch(self, records: Any, entity_type: str) -> Any
```

Process a batch of records with all cleaning rules.

Args:
    records: List of record dictionaries to process
    entity_type: Type of entity (player_stats, team_stats, game_stats)

Returns:
    Tuple of (cleaned_records, transformation_results)

#### get_transformation_summary

```python
get_transformation_summary(self) -> Any
```

Get summary of all transformations applied.

Returns:
    Dictionary with transformation statistics

#### clear_transformation_log

```python
clear_transformation_log(self) -> None
```

Clear the transformation log.

#### create_player_daily_partition

```python
create_player_daily_partition(season: str, player_id: str, date: str, bucket: str, filename: str) -> S3PartitionKey
```

Create partition key for player daily stats.

#### create_player_season_partition

```python
create_player_season_partition(season: str, player_id: str, bucket: str, filename: str) -> S3PartitionKey
```

Create partition key for player season summary.

#### create_team_daily_partition

```python
create_team_daily_partition(season: str, team_id: str, date: str, bucket: str, filename: str) -> S3PartitionKey
```

Create partition key for team daily stats.

#### validate_season_format

```python
validate_season_format(cls, v: str) -> str
```

Validate NBA season format.

#### validate_date_format

```python
validate_date_format(cls, v: Any) -> Any
```

Validate date format if provided.

#### s3_prefix

```python
s3_prefix(self) -> str
```

Generate S3 prefix from partition key components.

#### s3_path

```python
s3_path(self) -> str
```

Generate full S3 path including bucket and filename.

#### local_path

```python
local_path(self) -> Path
```

Generate local file path structure matching S3 hierarchy.

#### estimate_parquet_size

```python
estimate_parquet_size(row_count: int, avg_row_size_bytes: int) -> int
```

Estimate Parquet file size based on row count.

Args:
    row_count: Number of rows in the dataset
    avg_row_size_bytes: Average size per row in bytes

Returns:
    Estimated file size in bytes

#### should_split_file

```python
should_split_file(cls, row_count: int, avg_row_size_bytes: int) -> bool
```

Determine if file should be split based on estimated size.

Args:
    row_count: Number of rows in the dataset
    avg_row_size_bytes: Average size per row in bytes

Returns:
    True if file should be split

#### recommend_split_strategy

```python
recommend_split_strategy(cls, row_count: int, avg_row_size_bytes: int) -> Any
```

Recommend splitting strategy for large files.

Args:
    row_count: Number of rows in the dataset
    avg_row_size_bytes: Average size per row in bytes

Returns:
    Dictionary with splitting recommendations

#### get_optimal_partition_key

```python
get_optimal_partition_key(cls, query_pattern: str) -> S3PartitionKey
```

Generate optimal partition key for a given query pattern.

Args:
    query_pattern: Name of the query pattern
    **kwargs: Parameters for partition key generation

Returns:
    Optimized S3PartitionKey

Raises:
    ValueError: If query pattern is unknown or required parameters missing

#### list_query_patterns

```python
list_query_patterns(cls) -> Any
```

List available query patterns with descriptions.

Returns:
    Dictionary mapping pattern names to descriptions

#### calculate_partition_hash

```python
calculate_partition_hash(partition_key: S3PartitionKey) -> str
```

Calculate a hash for partition identification and change detection.

Args:
    partition_key: S3 partition key

Returns:
    MD5 hash of the partition key

#### validate_partition_structure

```python
validate_partition_structure(partition_key: S3PartitionKey) -> Any
```

Validate partition structure against ADR-020 standards.

Args:
    partition_key: S3 partition key to validate

Returns:
    Validation result with warnings and recommendations

#### get_schema_version

```python
get_schema_version() -> str
```

Get current schema version.

#### generate_json_schema

```python
generate_json_schema(model_class: Any) -> Any
```

Generate JSON schema for a Silver layer model.

#### validate_field_goals

```python
validate_field_goals(cls, v, info) -> Any
```

Ensure field goals attempted >= field goals made.

#### validate_points_range

```python
validate_points_range(cls, v, info) -> Any
```

Validate points are within reasonable NBA game ranges.

#### validate_player_name

```python
validate_player_name(cls, v) -> Any
```

Ensure player name is properly formatted.

#### validate_shooting_consistency

```python
validate_shooting_consistency(self) -> Any
```

Validate shooting statistics consistency.

#### validate_team_name

```python
validate_team_name(cls, v) -> Any
```

Ensure team name is valid NBA team.

#### validate_points_range

```python
validate_points_range(cls, v, info) -> Any
```

Validate team points are within reasonable NBA game ranges.

#### validate_team_shooting_stats

```python
validate_team_shooting_stats(self) -> Any
```

Validate team shooting statistics consistency.

#### validate_game_date

```python
validate_game_date(cls, v) -> Any
```

Ensure game date is in ISO format if provided.

#### validate_season_format

```python
validate_season_format(cls, v) -> Any
```

Validate NBA season format (e.g., '2023-24').

#### validate_game_logic

```python
validate_game_logic(self) -> Any
```

Validate game logic and constraints.

#### validate_ts_percentage

```python
validate_ts_percentage(cls, v) -> Any
```

Validate true shooting percentage is reasonable.

#### validate_season_format

```python
validate_season_format(cls, v) -> Any
```

Validate NBA season format.

#### validate_season_format

```python
validate_season_format(cls, v) -> Any
```

Validate NBA season format.

#### migrate_from_version

```python
migrate_from_version(data: Any, from_version: str, to_version: str) -> Any
```

Migrate data from one schema version to another.

## Examples

### normalize_team_name

```python
>>> normalize_team_name("lakers")
```

### calculate_efficiency_rating

```python
>>> stats = {
...     "points": 25, "rebounds": 10, "assists": 5,
...     "steals": 2, "blocks": 1, "turnovers": 3, "minutes_played": 35
... }
>>> calculate_efficiency_rating(stats)
```

### standardize_position

```python
>>> standardize_position("Point Guard")
```

### calculate_shooting_percentage

```python
>>> calculate_shooting_percentage(8, 15)
```

### convert_minutes_to_decimal

```python
>>> convert_minutes_to_decimal("35:30")
```

### normalize_stat_per_game

```python
>>> normalize_stat_per_game(250, 10)
```

### clean_and_transform_record

```python
>>> record = {"team_name": "lakers", "points": "25", "position": "point guard"}
>>> clean_and_transform_record(record)
```

### clean_batch

```python
>>> records = [{"team_name": "lakers"}, {"team_name": "warriors"}]
>>> clean_batch(records)
```

### validate_and_standardize_season

```python
>>> validate_and_standardize_season("2023-2024")
```

### check_data_completeness

```python
>>> data = {"points": 25, "rebounds": None, "assists": 5}
>>> result = check_data_completeness(data)  # doctest: +SKIP
```

### detect_outliers

```python
>>> values = [10, 12, 11, 13, 15, 50, 14]
>>> detect_outliers(values)
```

### validate_stat_consistency

```python
>>> stats = [
...     {"player_id": "123", "points": 25, "field_goals_made": 10},
...     {"player_id": "123", "points": -5, "field_goals_made": 15}
... ]
>>> issues = validate_stat_consistency(stats)  # doctest: +SKIP
```

### calculate_data_quality_score

```python
>>> data = {"points": 25, "rebounds": 10, "assists": 5}
>>> calculate_data_quality_score(data)
```

### identify_missing_critical_stats

```python
>>> data = {"rebounds": 10, "assists": 5}
>>> identify_missing_critical_stats(data)
```

### compare_stat_distributions

```python
>>> data1 = [{"points": 20}, {"points": 25}]
>>> data2 = [{"points": 15}, {"points": 30}]
>>> compare_stat_distributions(data1, data2, "points")
```

### validate_player_stats

```python
>>> stats = {"points": 25, "rebounds": 10, "assists": 5}
>>> validate_player_stats(stats)
```

### validate_team_stats

```python
>>> stats = {"team_name": "Lakers", "points": 120, "field_goals_made": 45}
>>> validate_team_stats(stats)
```

### validate_game_stats

```python
>>> stats = {"home_score": 110, "away_score": 105, "game_id": "game_123"}
>>> validate_game_stats(stats)
```

### validate_stat_ranges

```python
>>> stats = {"points": 25, "rebounds": -5}
>>> validate_stat_ranges(stats)
```
