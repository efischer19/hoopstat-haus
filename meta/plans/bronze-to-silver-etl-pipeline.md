# Bronze-to-Silver ETL Pipeline Design

## Executive Summary

This document defines the comprehensive design for the Bronze-to-Silver ETL pipeline that transforms raw NBA data from our immutable Bronze layer into clean, validated, and conformed Silver layer datasets. This pipeline serves as the critical data quality gateway, converting potentially unreliable raw API data into a trustworthy "source of truth" for all downstream analytics and the MCP server.

The design leverages our established technology stack including Pydantic for schema validation (aligned with ADR-003 Poetry dependencies), GitHub Actions for orchestration (per ADR-007), AWS S3 for storage (per ADR-009), and Parquet format for data persistence (per ADR-014).

## Pipeline Architecture Overview

### Core ETL Flow
```
Bronze Layer (Raw JSON + Parquet)
    ↓ [Extract & Validate]
Schema Validation Layer (Pydantic)
    ↓ [Transform & Clean]
Business Rules Engine (Custom Logic)
    ↓ [Deduplicate & Conform]
Data Quality Validation (Quality Checks)
    ↓ [Load & Partition]
Silver Layer (Clean Parquet + Metadata)
    ↓ [Error Handling]
Dead Letter Queue (Failed Records)
```

### Processing Patterns
- **Incremental Processing**: Process only new Bronze layer data since last successful run
- **Idempotent Operations**: Pipeline can be safely re-run without data corruption
- **Atomic Commits**: All-or-nothing processing for data consistency
- **Quality-First**: Invalid data is quarantined rather than corrupting Silver layer

## Schema Definition & Enforcement Framework

### Pydantic Schema Architecture

We will implement a comprehensive schema validation framework using Pydantic models that enforce data types, constraints, and business rules.

#### Core Schema Modules
```python
# schemas/bronze_models.py - Raw data from NBA API
# schemas/silver_models.py - Cleaned, validated data
# schemas/validation_models.py - Quality check results
# schemas/metadata_models.py - Pipeline execution metadata
```

#### Key Schema Definitions

**Player Schema (Silver Layer)**
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import date, datetime
from decimal import Decimal

class SilverPlayer(BaseModel):
    player_id: int = Field(..., description="NBA API player ID")
    full_name: str = Field(..., min_length=1, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    position: Literal["PG", "SG", "SF", "PF", "C", "G", "F"] = Field(...)
    height_inches: Optional[int] = Field(None, ge=60, le=96)
    weight_lbs: Optional[int] = Field(None, ge=120, le=400)
    birth_date: Optional[date] = Field(None)
    team_id: Optional[int] = Field(None)
    jersey_number: Optional[int] = Field(None, ge=0, le=99)
    years_experience: Optional[int] = Field(None, ge=0, le=30)
    is_active: bool = Field(True)
    
    # Metadata fields
    effective_date: date = Field(..., description="Date this record became effective")
    source_system: str = Field(default="nba-api")
    ingestion_timestamp: datetime = Field(...)
    data_quality_score: Decimal = Field(..., ge=0.0, le=1.0)
    
    @validator('full_name')
    def validate_full_name(cls, v, values):
        first = values.get('first_name', '')
        last = values.get('last_name', '')
        expected = f"{first} {last}".strip()
        if v != expected:
            raise ValueError(f"Full name '{v}' doesn't match '{expected}'")
        return v
    
    @validator('birth_date')
    def validate_birth_date(cls, v):
        if v and v > date.today():
            raise ValueError("Birth date cannot be in the future")
        if v and v < date(1950, 1, 1):
            raise ValueError("Birth date unreasonably old")
        return v
```

**Game Schema (Silver Layer)**
```python
class SilverGame(BaseModel):
    game_id: str = Field(..., regex=r"^\d{8}_[A-Z]{3}_[A-Z]{3}$")
    season: str = Field(..., regex=r"^\d{4}-\d{2}$")
    game_date: date = Field(...)
    home_team_id: int = Field(...)
    away_team_id: int = Field(...)
    home_score: Optional[int] = Field(None, ge=0)
    away_score: Optional[int] = Field(None, ge=0)
    game_status: Literal["scheduled", "live", "final", "postponed", "cancelled"]
    period: Optional[int] = Field(None, ge=1, le=4)
    game_time: Optional[str] = Field(None, regex=r"^\d{2}:\d{2}$")
    arena: Optional[str] = Field(None, max_length=100)
    attendance: Optional[int] = Field(None, ge=0, le=50000)
    
    # Quality and lineage
    data_completeness_score: Decimal = Field(..., ge=0.0, le=1.0)
    source_api_endpoint: str = Field(...)
    ingestion_timestamp: datetime = Field(...)
    
    @validator('game_date')
    def validate_game_date(cls, v):
        if v < date(1946, 11, 1):  # NBA founding
            raise ValueError("Game date before NBA founding")
        if v > date.today() + timedelta(days=365):
            raise ValueError("Game date too far in future")
        return v
```

#### Schema Evolution Strategy
- **Version Management**: Schema versions tracked in metadata
- **Backward Compatibility**: New fields added as optional
- **Migration Scripts**: Automated schema migration tools
- **Validation Profiles**: Different validation strictness levels

### Validation Framework Implementation
```python
class DataValidator:
    def __init__(self, schema_class, strictness: Literal["strict", "lenient"]):
        self.schema_class = schema_class
        self.strictness = strictness
    
    def validate_batch(self, records: List[Dict]) -> ValidationResult:
        """Validate a batch of records with detailed error reporting"""
        valid_records = []
        failed_records = []
        warnings = []
        
        for record in records:
            try:
                validated = self.schema_class(**record)
                valid_records.append(validated.dict())
            except ValidationError as e:
                if self.strictness == "strict":
                    failed_records.append({
                        "record": record,
                        "errors": e.errors(),
                        "error_count": len(e.errors())
                    })
                else:
                    # Lenient mode: attempt partial validation
                    cleaned_record = self._partial_validation(record, e)
                    if cleaned_record:
                        valid_records.append(cleaned_record)
                        warnings.append(f"Partial validation applied to record")
                    else:
                        failed_records.append({"record": record, "errors": e.errors()})
        
        return ValidationResult(
            valid_records=valid_records,
            failed_records=failed_records,
            warnings=warnings,
            success_rate=len(valid_records) / len(records)
        )
```

## Data Cleaning & Conforming Rules

### Text Standardization Rules

**Team Name Standardization**
```python
TEAM_NAME_MAPPINGS = {
    # Handle common variations and abbreviations
    "LA Lakers": "Los Angeles Lakers",
    "LA Clippers": "Los Angeles Clippers", 
    "GSW": "Golden State Warriors",
    "GS Warriors": "Golden State Warriors",
    "NY Knicks": "New York Knicks",
    "SA Spurs": "San Antonio Spurs",
    "NO Pelicans": "New Orleans Pelicans",
    "PHX Suns": "Phoenix Suns",
    # Historical team names
    "Seattle SuperSonics": "Oklahoma City Thunder",  # For historical data
    "Charlotte Bobcats": "Charlotte Hornets",
    "New Jersey Nets": "Brooklyn Nets",
}

def standardize_team_name(raw_name: str) -> str:
    """Apply team name standardization rules"""
    if not raw_name:
        return None
    
    # Clean whitespace and capitalize properly
    cleaned = re.sub(r'\s+', ' ', raw_name.strip())
    
    # Apply direct mappings
    if cleaned in TEAM_NAME_MAPPINGS:
        return TEAM_NAME_MAPPINGS[cleaned]
    
    # Apply fuzzy matching for typos
    best_match = process.extractOne(cleaned, OFFICIAL_TEAM_NAMES)
    if best_match and best_match[1] > 85:  # 85% similarity threshold
        return best_match[0]
    
    return cleaned  # Return cleaned version if no mapping found
```

**Player Position Standardization**
```python
POSITION_MAPPINGS = {
    "Point Guard": "PG",
    "Shooting Guard": "SG", 
    "Small Forward": "SF",
    "Power Forward": "PF",
    "Center": "C",
    "Guard": "G",
    "Forward": "F",
    # Handle variations
    "PG/SG": "G",
    "SG/SF": "G",  # Based on primary position
    "SF/PF": "F",
    "PF/C": "F",
    # Legacy/unusual positions
    "Guard-Forward": "G",
    "Forward-Center": "F",
}
```

### Null Value Handling Strategy

**Field-Specific Null Handling**
```python
class NullHandlingRules:
    REQUIRED_FIELDS = {
        'player_id', 'game_id', 'team_id', 'game_date', 'ingestion_timestamp'
    }
    
    DEFAULT_VALUES = {
        'jersey_number': None,  # Allow null for jersey numbers
        'height_inches': None,  # Missing player physical data is acceptable
        'weight_lbs': None,
        'birth_date': None,
        'years_experience': 0,  # Default to rookie
    }
    
    DERIVED_FIELDS = {
        'age': lambda birth_date, game_date: calculate_age(birth_date, game_date),
        'full_name': lambda first, last: f"{first} {last}".strip(),
        'season': lambda game_date: get_nba_season(game_date),
    }
    
    @staticmethod
    def handle_nulls(record: Dict) -> Dict:
        """Apply null handling rules to a single record"""
        cleaned = record.copy()
        
        # Validate required fields
        missing_required = [f for f in NullHandlingRules.REQUIRED_FIELDS 
                          if not cleaned.get(f)]
        if missing_required:
            raise ValueError(f"Missing required fields: {missing_required}")
        
        # Apply default values
        for field, default in NullHandlingRules.DEFAULT_VALUES.items():
            if field not in cleaned or cleaned[field] is None:
                cleaned[field] = default
        
        # Calculate derived fields
        for field, calculator in NullHandlingRules.DERIVED_FIELDS.items():
            try:
                if field not in cleaned or cleaned[field] is None:
                    cleaned[field] = calculator(**cleaned)
            except (KeyError, TypeError, ValueError):
                # Skip derived field if calculation fails
                pass
        
        return cleaned
```

### Data Type Conversion & Validation

**Numeric Field Cleaning**
```python
def clean_numeric_field(value: Any, field_name: str, 
                       min_val: Optional[float] = None,
                       max_val: Optional[float] = None) -> Optional[float]:
    """Clean and validate numeric fields with business rules"""
    if value is None or value == "":
        return None
    
    # Handle string representations
    if isinstance(value, str):
        # Remove common formatting characters
        cleaned = re.sub(r'[,$%]', '', value.strip())
        if not cleaned:
            return None
        try:
            value = float(cleaned)
        except ValueError:
            raise ValueError(f"Invalid numeric value for {field_name}: {value}")
    
    # Validate ranges with business logic
    if min_val is not None and value < min_val:
        raise ValueError(f"{field_name} below minimum: {value} < {min_val}")
    if max_val is not None and value > max_val:
        raise ValueError(f"{field_name} above maximum: {value} > {max_val}")
    
    return float(value)
```

**Date/Time Standardization**
```python
def standardize_datetime(value: Any, timezone: str = "UTC") -> Optional[datetime]:
    """Convert various datetime formats to standardized UTC datetime"""
    if value is None:
        return None
    
    # Handle common formats
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with microseconds
        "%Y-%m-%dT%H:%M:%SZ",     # ISO format
        "%Y-%m-%d %H:%M:%S",      # SQL format
        "%m/%d/%Y %H:%M:%S",      # US format
        "%Y-%m-%d",               # Date only
    ]
    
    if isinstance(value, str):
        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=pytz.UTC)
                return dt.astimezone(pytz.UTC)
            except ValueError:
                continue
        raise ValueError(f"Unable to parse datetime: {value}")
    
    elif isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=pytz.UTC)
        return value.astimezone(pytz.UTC)
    
    else:
        raise ValueError(f"Invalid datetime type: {type(value)}")
```

## Deduplication Strategy

### Record Identification Framework

**Primary Key Definitions**
```python
class DeduplicationKeys:
    PLAYER_RECORDS = ['player_id', 'effective_date']
    GAME_RECORDS = ['game_id']  # Games are naturally unique
    GAME_STATS = ['game_id', 'player_id']
    TEAM_RECORDS = ['team_id', 'effective_date']
    
    # Composite keys for complex entities
    PLAYER_GAME_STATS = ['game_id', 'player_id', 'stat_type']
```

**Duplicate Detection Algorithm**
```python
class DuplicateDetector:
    def __init__(self, primary_keys: List[str], similarity_threshold: float = 0.95):
        self.primary_keys = primary_keys
        self.similarity_threshold = similarity_threshold
    
    def find_duplicates(self, records: List[Dict]) -> DuplicateReport:
        """Identify exact and fuzzy duplicates in record set"""
        exact_duplicates = []
        fuzzy_duplicates = []
        unique_records = []
        
        # Group by primary key for exact duplicate detection
        key_groups = defaultdict(list)
        for record in records:
            key = tuple(record.get(k) for k in self.primary_keys)
            key_groups[key].append(record)
        
        for key, group in key_groups.items():
            if len(group) == 1:
                unique_records.extend(group)
            else:
                # Handle exact duplicates
                if self._records_identical(group):
                    exact_duplicates.append({
                        'primary_key': key,
                        'records': group,
                        'resolution': 'keep_latest_ingestion'
                    })
                else:
                    # Analyze fuzzy duplicates
                    fuzzy_analysis = self._analyze_fuzzy_duplicates(group)
                    fuzzy_duplicates.append(fuzzy_analysis)
        
        return DuplicateReport(
            exact_duplicates=exact_duplicates,
            fuzzy_duplicates=fuzzy_duplicates,
            unique_records=unique_records,
            total_records=len(records),
            duplicate_rate=len(exact_duplicates + fuzzy_duplicates) / len(records)
        )
    
    def resolve_duplicates(self, duplicate_report: DuplicateReport) -> List[Dict]:
        """Apply deduplication rules to resolve conflicts"""
        resolved_records = duplicate_report.unique_records.copy()
        
        # Handle exact duplicates
        for dup_group in duplicate_report.exact_duplicates:
            if dup_group['resolution'] == 'keep_latest_ingestion':
                latest_record = max(dup_group['records'], 
                                  key=lambda x: x['ingestion_timestamp'])
                resolved_records.append(latest_record)
        
        # Handle fuzzy duplicates
        for fuzzy_group in duplicate_report.fuzzy_duplicates:
            resolved_record = self._merge_fuzzy_duplicates(fuzzy_group)
            resolved_records.append(resolved_record)
        
        return resolved_records
    
    def _merge_fuzzy_duplicates(self, fuzzy_group: Dict) -> Dict:
        """Merge fuzzy duplicate records using business rules"""
        records = fuzzy_group['records']
        base_record = records[0].copy()
        
        # Merge strategy: prefer non-null values from most recent ingestion
        for record in sorted(records, key=lambda x: x['ingestion_timestamp'], reverse=True):
            for field, value in record.items():
                if value is not None and (base_record.get(field) is None):
                    base_record[field] = value
        
        # Add deduplication metadata
        base_record['_dedup_metadata'] = {
            'merged_from': len(records),
            'source_records': [r.get('ingestion_timestamp') for r in records],
            'merge_timestamp': datetime.utcnow().isoformat()
        }
        
        return base_record
```

### Business Rules for Deduplication

**Player Record Deduplication**
```python
class PlayerDeduplicationRules:
    @staticmethod
    def resolve_player_conflicts(records: List[Dict]) -> Dict:
        """Apply business rules for conflicting player data"""
        # Sort by data quality score and ingestion timestamp
        sorted_records = sorted(records, 
                              key=lambda x: (x.get('data_quality_score', 0), 
                                           x.get('ingestion_timestamp')), 
                              reverse=True)
        
        base_record = sorted_records[0].copy()
        
        # Apply field-specific merge rules
        for record in sorted_records[1:]:
            # Height/Weight: prefer non-zero values
            if not base_record.get('height_inches') and record.get('height_inches'):
                base_record['height_inches'] = record['height_inches']
            if not base_record.get('weight_lbs') and record.get('weight_lbs'):
                base_record['weight_lbs'] = record['weight_lbs']
            
            # Jersey number: prefer most recent
            if record.get('jersey_number') and record['ingestion_timestamp'] > base_record['ingestion_timestamp']:
                base_record['jersey_number'] = record['jersey_number']
        
        return base_record
```

## Job Orchestration with GitHub Actions

### Workflow Architecture

**Main ETL Workflow** (`.github/workflows/bronze-to-silver-etl.yml`)
```yaml
name: Bronze to Silver ETL Pipeline

on:
  schedule:
    # Run daily at 6 AM UTC (after NBA games typically finish)
    - cron: '0 6 * * *'
  workflow_dispatch:
    inputs:
      force_full_refresh:
        description: 'Force full data refresh (not incremental)'
        required: false
        default: 'false'
        type: boolean
      date_range:
        description: 'Specific date range (YYYY-MM-DD:YYYY-MM-DD)'
        required: false
        type: string

env:
  AWS_REGION: us-east-1
  BRONZE_BUCKET: hoopstat-haus-bronze
  SILVER_BUCKET: hoopstat-haus-silver

jobs:
  validate-inputs:
    runs-on: ubuntu-latest
    outputs:
      processing_mode: ${{ steps.determine-mode.outputs.mode }}
      date_range: ${{ steps.determine-mode.outputs.date_range }}
    steps:
      - name: Determine processing mode
        id: determine-mode
        run: |
          if [ "${{ github.event.inputs.force_full_refresh }}" = "true" ]; then
            echo "mode=full_refresh" >> $GITHUB_OUTPUT
          elif [ -n "${{ github.event.inputs.date_range }}" ]; then
            echo "mode=date_range" >> $GITHUB_OUTPUT
            echo "date_range=${{ github.event.inputs.date_range }}" >> $GITHUB_OUTPUT
          else
            echo "mode=incremental" >> $GITHUB_OUTPUT
          fi

  extract-and-validate:
    needs: validate-inputs
    runs-on: ubuntu-latest
    outputs:
      bronze_files: ${{ steps.extract.outputs.files }}
      validation_report: ${{ steps.validate.outputs.report }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install --only main
      
      - name: Extract Bronze layer data
        id: extract
        run: |
          poetry run python -m etl.extract \
            --mode ${{ needs.validate-inputs.outputs.processing_mode }} \
            --date-range "${{ needs.validate-inputs.outputs.date_range }}" \
            --output-manifest bronze_files.json
          echo "files=$(cat bronze_files.json)" >> $GITHUB_OUTPUT
      
      - name: Validate schemas
        id: validate
        run: |
          poetry run python -m etl.validate \
            --input-manifest bronze_files.json \
            --validation-report validation_report.json
          echo "report=$(cat validation_report.json)" >> $GITHUB_OUTPUT
      
      - name: Upload validation artifacts
        uses: actions/upload-artifact@v4
        with:
          name: validation-results
          path: |
            bronze_files.json
            validation_report.json
            logs/

  transform-and-clean:
    needs: [validate-inputs, extract-and-validate]
    runs-on: ubuntu-latest
    if: ${{ fromJson(needs.extract-and-validate.outputs.validation_report).success_rate >= 0.8 }}
    outputs:
      silver_files: ${{ steps.transform.outputs.files }}
      quality_report: ${{ steps.quality.outputs.report }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Download validation artifacts
        uses: actions/download-artifact@v4
        with:
          name: validation-results
      
      - name: Set up Python and dependencies
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: |
          pip install poetry
          poetry install --only main
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Apply data transformations
        id: transform
        run: |
          poetry run python -m etl.transform \
            --input-manifest bronze_files.json \
            --output-manifest silver_files.json \
            --enable-deduplication \
            --quality-threshold 0.95
          echo "files=$(cat silver_files.json)" >> $GITHUB_OUTPUT
      
      - name: Generate quality report
        id: quality
        run: |
          poetry run python -m etl.quality_check \
            --silver-manifest silver_files.json \
            --quality-report quality_report.json
          echo "report=$(cat quality_report.json)" >> $GITHUB_OUTPUT
      
      - name: Upload transformation artifacts
        uses: actions/upload-artifact@v4
        with:
          name: transformation-results
          path: |
            silver_files.json
            quality_report.json
            logs/

  load-to-silver:
    needs: [validate-inputs, extract-and-validate, transform-and-clean]
    runs-on: ubuntu-latest
    if: ${{ fromJson(needs.transform-and-clean.outputs.quality_report).overall_quality >= 0.9 }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Download transformation artifacts
        uses: actions/download-artifact@v4
        with:
          name: transformation-results
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Load to Silver layer
        run: |
          poetry run python -m etl.load \
            --input-manifest silver_files.json \
            --target-bucket ${{ env.SILVER_BUCKET }} \
            --partition-strategy season_month \
            --enable-atomic-commit
      
      - name: Update data catalog
        run: |
          poetry run python -m etl.catalog \
            --update-silver-metadata \
            --manifest silver_files.json
      
      - name: Cleanup temporary files
        run: |
          poetry run python -m etl.cleanup \
            --remove-temp-files \
            --preserve-logs

  handle-failures:
    needs: [extract-and-validate, transform-and-clean, load-to-silver]
    runs-on: ubuntu-latest
    if: failure()
    steps:
      - name: Process failed records
        run: |
          poetry run python -m etl.dead_letter_queue \
            --process-failures \
            --notify-on-critical
      
      - name: Create failure report
        run: |
          poetry run python -m etl.reporting \
            --generate-failure-report \
            --include-recovery-steps

  notify-completion:
    needs: [load-to-silver]
    runs-on: ubuntu-latest
    if: success()
    steps:
      - name: Send success notification
        run: |
          echo "ETL pipeline completed successfully" | \
          poetry run python -m etl.notifications \
            --channel slack \
            --include-metrics
```

### Error Recovery Workflows

**Dead Letter Queue Processing** (`.github/workflows/dlq-processing.yml`)
```yaml
name: Dead Letter Queue Processing

on:
  workflow_dispatch:
    inputs:
      processing_date:
        description: 'Date to process DLQ records (YYYY-MM-DD)'
        required: true
        type: string
      auto_recover:
        description: 'Attempt automatic recovery'
        required: false
        default: 'true'
        type: boolean

jobs:
  analyze-dlq:
    runs-on: ubuntu-latest
    outputs:
      recoverable_count: ${{ steps.analyze.outputs.recoverable }}
      total_count: ${{ steps.analyze.outputs.total }}
    steps:
      - name: Analyze DLQ records
        id: analyze
        run: |
          poetry run python -m etl.dlq_analyzer \
            --date ${{ github.event.inputs.processing_date }} \
            --output-analysis dlq_analysis.json
          
          recoverable=$(jq '.recoverable_records | length' dlq_analysis.json)
          total=$(jq '.total_records' dlq_analysis.json)
          
          echo "recoverable=$recoverable" >> $GITHUB_OUTPUT
          echo "total=$total" >> $GITHUB_OUTPUT

  auto-recovery:
    needs: analyze-dlq
    runs-on: ubuntu-latest
    if: ${{ github.event.inputs.auto_recover == 'true' && needs.analyze-dlq.outputs.recoverable_count > 0 }}
    steps:
      - name: Attempt automatic recovery
        run: |
          poetry run python -m etl.dlq_recovery \
            --date ${{ github.event.inputs.processing_date }} \
            --auto-fix-common-issues \
            --max-recovery-attempts 3
```

## Error Handling & Dead Letter Queue Strategy

### Error Classification Framework

**Error Categories and Handling**
```python
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass

class ErrorSeverity(Enum):
    LOW = "low"           # Data quality warnings, non-critical missing fields
    MEDIUM = "medium"     # Schema validation failures, data type errors
    HIGH = "high"         # Business rule violations, critical field missing
    CRITICAL = "critical" # System errors, API failures, infrastructure issues

class ErrorCategory(Enum):
    SCHEMA_VALIDATION = "schema_validation"
    DATA_QUALITY = "data_quality"
    BUSINESS_RULE = "business_rule"
    SYSTEM_ERROR = "system_error"
    EXTERNAL_API = "external_api"

@dataclass
class ErrorRecord:
    record_id: str
    error_category: ErrorCategory
    error_severity: ErrorSeverity
    error_message: str
    field_name: Optional[str]
    original_value: Optional[str]
    suggested_fix: Optional[str]
    timestamp: datetime
    pipeline_stage: str
    retry_count: int = 0
    recoverable: bool = True

class ErrorHandler:
    def __init__(self, dlq_bucket: str, dlq_prefix: str):
        self.dlq_bucket = dlq_bucket
        self.dlq_prefix = dlq_prefix
        self.error_thresholds = {
            ErrorSeverity.LOW: 0.1,      # 10% acceptable
            ErrorSeverity.MEDIUM: 0.05,   # 5% acceptable
            ErrorSeverity.HIGH: 0.02,     # 2% acceptable
            ErrorSeverity.CRITICAL: 0.0   # 0% acceptable
        }
    
    def handle_batch_errors(self, errors: List[ErrorRecord], 
                           total_records: int) -> ErrorHandlingDecision:
        """Determine how to handle a batch of errors"""
        error_summary = self._analyze_error_batch(errors, total_records)
        
        # Check if error rates exceed thresholds
        for severity, rate in error_summary.error_rates.items():
            if rate > self.error_thresholds[severity]:
                if severity == ErrorSeverity.CRITICAL:
                    return ErrorHandlingDecision.ABORT_PIPELINE
                elif severity == ErrorSeverity.HIGH:
                    return ErrorHandlingDecision.QUARANTINE_BATCH
        
        # Separate recoverable from non-recoverable errors
        recoverable_errors = [e for e in errors if e.recoverable]
        
        if len(recoverable_errors) > 0:
            self._send_to_dlq(recoverable_errors, "recoverable")
        
        non_recoverable = [e for e in errors if not e.recoverable]
        if len(non_recoverable) > 0:
            self._send_to_dlq(non_recoverable, "manual_review")
        
        return ErrorHandlingDecision.CONTINUE_PROCESSING
    
    def _send_to_dlq(self, errors: List[ErrorRecord], queue_type: str):
        """Send failed records to appropriate dead letter queue"""
        partition = datetime.now().strftime("%Y/%m/%d")
        dlq_path = f"{self.dlq_prefix}/{queue_type}/date={partition}"
        
        # Group errors by category for easier analysis
        categorized_errors = defaultdict(list)
        for error in errors:
            categorized_errors[error.error_category].append(error)
        
        for category, category_errors in categorized_errors.items():
            file_path = f"{dlq_path}/{category.value}/errors_{int(time.time())}.json"
            
            error_data = {
                "metadata": {
                    "category": category.value,
                    "queue_type": queue_type,
                    "error_count": len(category_errors),
                    "processing_timestamp": datetime.utcnow().isoformat(),
                    "pipeline_run_id": os.environ.get("GITHUB_RUN_ID")
                },
                "errors": [asdict(error) for error in category_errors]
            }
            
            # Upload to S3 DLQ
            s3_client = boto3.client('s3')
            s3_client.put_object(
                Bucket=self.dlq_bucket,
                Key=file_path,
                Body=json.dumps(error_data, indent=2),
                ContentType='application/json'
            )
```

### Dead Letter Queue Processing

**DLQ Recovery Engine**
```python
class DLQRecoveryEngine:
    def __init__(self, dlq_bucket: str):
        self.dlq_bucket = dlq_bucket
        self.recovery_strategies = {
            ErrorCategory.SCHEMA_VALIDATION: self._recover_schema_errors,
            ErrorCategory.DATA_QUALITY: self._recover_quality_errors,
            ErrorCategory.BUSINESS_RULE: self._recover_business_rule_errors,
        }
    
    def process_dlq_batch(self, dlq_date: str, auto_recover: bool = True) -> RecoveryReport:
        """Process a batch of DLQ records for potential recovery"""
        dlq_records = self._load_dlq_records(dlq_date)
        recovery_results = []
        
        for record in dlq_records:
            if auto_recover and record.error_category in self.recovery_strategies:
                recovery_result = self.recovery_strategies[record.error_category](record)
                recovery_results.append(recovery_result)
            else:
                # Flag for manual review
                recovery_results.append(
                    RecoveryResult(
                        record_id=record.record_id,
                        recovery_status=RecoveryStatus.MANUAL_REVIEW_REQUIRED,
                        recovered_record=None,
                        recovery_notes="Automatic recovery not available"
                    )
                )
        
        return RecoveryReport(
            processing_date=dlq_date,
            total_records=len(dlq_records),
            auto_recovered=sum(1 for r in recovery_results 
                             if r.recovery_status == RecoveryStatus.RECOVERED),
            manual_review=sum(1 for r in recovery_results 
                             if r.recovery_status == RecoveryStatus.MANUAL_REVIEW_REQUIRED),
            unrecoverable=sum(1 for r in recovery_results 
                             if r.recovery_status == RecoveryStatus.UNRECOVERABLE),
            recovery_details=recovery_results
        )
    
    def _recover_schema_errors(self, error_record: ErrorRecord) -> RecoveryResult:
        """Attempt to automatically fix schema validation errors"""
        original_data = error_record.original_value
        
        # Common schema fixes
        fixes_applied = []
        
        # Fix date format issues
        if "date" in error_record.field_name.lower():
            fixed_date = self._fix_date_format(original_data)
            if fixed_date:
                fixes_applied.append(f"Converted date format: {original_data} -> {fixed_date}")
                original_data = fixed_date
        
        # Fix numeric formatting
        if error_record.error_message.find("numeric") >= 0:
            fixed_number = self._fix_numeric_format(original_data)
            if fixed_number is not None:
                fixes_applied.append(f"Fixed numeric format: {original_data} -> {fixed_number}")
                original_data = fixed_number
        
        if fixes_applied:
            return RecoveryResult(
                record_id=error_record.record_id,
                recovery_status=RecoveryStatus.RECOVERED,
                recovered_record=original_data,
                recovery_notes="; ".join(fixes_applied)
            )
        else:
            return RecoveryResult(
                record_id=error_record.record_id,
                recovery_status=RecoveryStatus.MANUAL_REVIEW_REQUIRED,
                recovered_record=None,
                recovery_notes="No automatic fixes available"
            )
```

### Monitoring and Alerting

**Error Rate Monitoring**
```python
class ErrorMonitor:
    def __init__(self, notification_channels: List[str]):
        self.notification_channels = notification_channels
        self.alert_thresholds = {
            "error_rate_spike": 0.1,    # 10% error rate triggers alert
            "critical_errors": 1,       # Any critical error triggers alert
            "dlq_backlog": 1000,       # DLQ backlog size threshold
        }
    
    def check_pipeline_health(self, pipeline_metrics: PipelineMetrics) -> List[Alert]:
        """Monitor pipeline health and generate alerts"""
        alerts = []
        
        # Check error rates
        if pipeline_metrics.error_rate > self.alert_thresholds["error_rate_spike"]:
            alerts.append(Alert(
                severity=AlertSeverity.HIGH,
                message=f"Error rate spike: {pipeline_metrics.error_rate:.2%}",
                recommended_action="Investigate recent data changes or pipeline modifications"
            ))
        
        # Check for critical errors
        if pipeline_metrics.critical_error_count > self.alert_thresholds["critical_errors"]:
            alerts.append(Alert(
                severity=AlertSeverity.CRITICAL,
                message=f"Critical errors detected: {pipeline_metrics.critical_error_count}",
                recommended_action="Immediate investigation required - pipeline may be failing"
            ))
        
        # Check DLQ backlog
        if pipeline_metrics.dlq_record_count > self.alert_thresholds["dlq_backlog"]:
            alerts.append(Alert(
                severity=AlertSeverity.MEDIUM,
                message=f"DLQ backlog growing: {pipeline_metrics.dlq_record_count} records",
                recommended_action="Schedule DLQ processing and recovery session"
            ))
        
        # Send alerts if any were generated
        if alerts:
            self._send_alerts(alerts)
        
        return alerts
```

## Required ADRs for Implementation

Based on this comprehensive Bronze-to-Silver ETL design, the following ADRs need to be created to support implementation:

### ADR-016: Pydantic Schema Validation Framework
- **Decision Scope**: Establish Pydantic as the standard for data schema definition and validation
- **Key Areas**: Schema versioning, validation strictness levels, error handling patterns
- **Dependencies**: ADR-003 (Poetry), ADR-014 (Parquet format)

### ADR-017: Bronze-to-Silver Data Transformation Rules
- **Decision Scope**: Define standardized data cleaning, conforming, and transformation rules
- **Key Areas**: Team name standardization, position mapping, null value handling, type conversions
- **Dependencies**: ADR-013 (NBA API), ADR-016 (Schema validation)

### ADR-018: Deduplication Strategy and Business Rules
- **Decision Scope**: Establish algorithms and business rules for identifying and resolving duplicate records
- **Key Areas**: Primary key definitions, fuzzy matching thresholds, conflict resolution strategies
- **Dependencies**: ADR-017 (Transformation rules)

### ADR-019: ETL Pipeline Orchestration with GitHub Actions
- **Decision Scope**: Define GitHub Actions workflow patterns for ETL job scheduling and execution
- **Key Areas**: Workflow triggers, error handling, retry logic, artifact management
- **Dependencies**: ADR-007 (GitHub Actions), ADR-009 (AWS)

### ADR-020: Dead Letter Queue and Error Recovery Framework
- **Decision Scope**: Establish error classification, DLQ structure, and recovery mechanisms
- **Key Areas**: Error severity levels, DLQ partitioning, automatic recovery strategies
- **Dependencies**: ADR-009 (AWS S3), ADR-019 (ETL orchestration)

### ADR-021: Data Quality Monitoring and Alerting Strategy
- **Decision Scope**: Define data quality metrics, monitoring approaches, and alerting thresholds
- **Key Areas**: Quality score calculations, pipeline health monitoring, notification channels
- **Dependencies**: ADR-015 (JSON logging), ADR-020 (Error handling)

## Phase-Based Implementation Roadmap

### Phase 1: Foundation and Schema Framework (Weeks 1-2)
Focus on establishing the core validation and schema infrastructure.

### Phase 2: Core ETL Pipeline (Weeks 3-4)
Implement the main transformation and loading logic.

### Phase 3: Error Handling and Quality Assurance (Weeks 5-6)
Build robust error handling and data quality monitoring.

### Phase 4: Automation and Operations (Weeks 7-8)
Complete GitHub Actions integration and operational monitoring.

## Next Steps: Actionable Feature Requests

### Phase 1: Foundation and Schema Framework

#### 1. Implement Pydantic Schema Validation Framework
```
Title: feat(etl): implement Pydantic schema validation framework for Bronze-to-Silver ETL

Description:
Create a comprehensive schema validation framework using Pydantic models to enforce data quality and consistency in the Bronze-to-Silver ETL pipeline.

Acceptance Criteria:
- [ ] Create Pydantic models for all Silver layer entities (players, teams, games, statistics)
- [ ] Implement schema versioning and evolution strategy
- [ ] Add validation strictness levels (strict/lenient modes)
- [ ] Create comprehensive unit tests for all schema models
- [ ] Add field-level validation with business rules
- [ ] Implement custom validators for NBA-specific data constraints
- [ ] Generate JSON schemas for documentation and external validation

Technical Requirements:
- Use Pydantic v2 with performance optimizations
- Include data lineage fields in all schemas  
- Support for incremental schema evolution
- Comprehensive error messages for validation failures

Definition of Done:
- All schemas pass validation tests with sample NBA data
- Schema documentation generated and reviewed
- Performance benchmarks meet requirements (<100ms per 1000 records)
- Error handling covers all identified edge cases
```

#### 2. Create Data Cleaning and Standardization Rules Engine
```
Title: feat(etl): implement data cleaning and standardization rules for NBA data

Description:
Build a configurable rules engine that applies data cleaning, standardization, and conforming transformations to raw NBA data from the Bronze layer.

Acceptance Criteria:
- [ ] Implement team name standardization with mapping tables
- [ ] Create player position normalization logic
- [ ] Add comprehensive null value handling rules
- [ ] Implement data type conversion and validation
- [ ] Create date/time standardization functions
- [ ] Add numeric field cleaning with business rule validation
- [ ] Support for fuzzy string matching on player/team names

Technical Requirements:
- Rules configurable via YAML/JSON configuration files
- Support for custom business rules per data entity
- Performance optimized for batch processing
- Comprehensive logging of all transformations applied

Definition of Done:
- All cleaning rules tested against historical NBA data samples
- Configuration system allows easy rule updates
- Transformation logging enables full data lineage tracking
- Performance meets requirements (>10,000 records/minute)
```

### Phase 2: Core ETL Pipeline

#### 3. Build Deduplication Engine with Business Logic
```
Title: feat(etl): implement intelligent deduplication engine for NBA data

Description:
Create a sophisticated deduplication system that identifies and resolves duplicate records using NBA-specific business rules and fuzzy matching algorithms.

Acceptance Criteria:
- [ ] Implement exact duplicate detection by primary keys
- [ ] Add fuzzy duplicate detection with configurable similarity thresholds
- [ ] Create conflict resolution rules for player data merging
- [ ] Implement slowly changing dimension (SCD Type 2) support
- [ ] Add deduplication metadata tracking for audit purposes
- [ ] Create comprehensive test suite with known duplicate scenarios

Technical Requirements:
- Support for different deduplication strategies per entity type
- Configurable similarity thresholds and matching algorithms
- Performance optimized for large datasets (>1M records)
- Detailed reporting on deduplication actions taken

Definition of Done:
- Deduplication accuracy >95% on test dataset with known duplicates
- Performance benchmarks met for production data volumes
- All business rules documented and tested
- Audit trail captures all deduplication decisions
```

#### 4. Implement Bronze-to-Silver ETL Core Pipeline
```
Title: feat(etl): build core Bronze-to-Silver transformation pipeline

Description:
Create the main ETL pipeline that orchestrates data extraction from Bronze layer, applies transformations, and loads clean data to Silver layer with comprehensive error handling.

Acceptance Criteria:
- [ ] Implement incremental processing with change detection
- [ ] Add support for full refresh and date-range processing modes
- [ ] Create atomic transaction support for data consistency
- [ ] Implement partition-aware processing for performance
- [ ] Add comprehensive pipeline metrics and monitoring
- [ ] Create data quality scoring and validation checkpoints

Technical Requirements:
- Support for parallel processing of independent data partitions
- Idempotent operations that can be safely retried
- Memory-efficient processing for large datasets
- Integration with existing AWS S3 Bronze and Silver buckets

Definition of Done:
- Pipeline successfully processes full historical NBA dataset
- Incremental processing correctly identifies and processes only new data
- All data quality checks pass with >95% success rate
- Performance requirements met (complete daily processing in <2 hours)
```

### Phase 3: Error Handling and Quality Assurance

#### 5. Create Dead Letter Queue and Error Recovery System
```
Title: feat(etl): implement comprehensive error handling and dead letter queue system

Description:
Build a robust error handling framework that classifies errors, routes failed records to appropriate dead letter queues, and provides automatic recovery mechanisms.

Acceptance Criteria:
- [ ] Implement error classification by severity and category
- [ ] Create partitioned dead letter queues in S3
- [ ] Add automatic recovery strategies for common error types
- [ ] Implement manual review workflow for complex errors
- [ ] Create error analytics and reporting dashboard
- [ ] Add alerting for critical error conditions

Technical Requirements:
- Error classification supports custom business rules
- DLQ partitioning enables efficient error analysis
- Recovery strategies are configurable and extensible
- Integration with monitoring and alerting systems

Definition of Done:
- Error handling covers all identified failure scenarios
- Automatic recovery successfully fixes >80% of recoverable errors
- Manual review workflow provides clear error analysis
- Alerting triggers appropriately for different error severities
```

#### 6. Implement Data Quality Monitoring and Metrics Framework
```
Title: feat(etl): build comprehensive data quality monitoring system

Description:
Create a data quality monitoring framework that tracks pipeline health, data completeness, accuracy, and consistency across all Silver layer datasets.

Acceptance Criteria:
- [ ] Implement data quality scoring algorithms
- [ ] Create quality trend analysis and reporting
- [ ] Add automated quality threshold alerting
- [ ] Build quality metrics dashboard
- [ ] Implement data freshness monitoring
- [ ] Create data lineage tracking and visualization

Technical Requirements:
- Quality metrics calculated in real-time during processing
- Historical quality trends stored for analysis
- Configurable quality thresholds per dataset
- Integration with existing monitoring infrastructure

Definition of Done:
- Quality monitoring covers all critical data quality dimensions
- Alerting triggers before quality issues impact downstream systems
- Dashboard provides clear visibility into pipeline health
- Quality metrics demonstrate continuous improvement over time
```

### Phase 4: Automation and Operations

#### 7. Build GitHub Actions Orchestration Workflows
```
Title: feat(etl): implement GitHub Actions workflows for ETL pipeline automation

Description:
Create comprehensive GitHub Actions workflows that automate the Bronze-to-Silver ETL pipeline with proper error handling, retry logic, and notification systems.

Acceptance Criteria:
- [ ] Implement scheduled daily ETL workflow execution
- [ ] Add support for manual workflow triggers with parameters
- [ ] Create workflow for DLQ processing and recovery
- [ ] Implement failure notification and escalation
- [ ] Add workflow monitoring and health checks
- [ ] Create deployment workflow for ETL code updates

Technical Requirements:
- Workflows integrate with AWS using OIDC authentication
- Proper artifact management and cleanup
- Configurable retry logic for transient failures
- Integration with existing CI/CD patterns

Definition of Done:
- Daily ETL runs automatically without manual intervention
- Failure notifications provide actionable information
- Manual triggers allow for ad-hoc processing scenarios
- Deployment workflow enables safe ETL code updates
```

#### 8. Create ETL Pipeline Monitoring and Observability
```
Title: feat(etl): implement comprehensive ETL pipeline observability

Description:
Build monitoring, logging, and observability infrastructure that provides full visibility into ETL pipeline performance, health, and data quality trends.

Acceptance Criteria:
- [ ] Implement structured logging throughout ETL pipeline
- [ ] Create performance metrics collection and analysis
- [ ] Add pipeline execution dashboards
- [ ] Implement cost monitoring and optimization alerts
- [ ] Create data lineage visualization
- [ ] Add capacity planning and scaling recommendations

Technical Requirements:
- Logging follows established JSON logging standards (ADR-015)
- Metrics integrate with AWS CloudWatch
- Dashboards provide both technical and business views
- Cost monitoring tracks S3 storage and compute usage

Definition of Done:
- Monitoring provides complete visibility into pipeline health
- Performance trends enable proactive optimization
- Cost monitoring prevents budget overruns
- Data lineage supports impact analysis and debugging
```

---

*Each feature request above can be copied directly into a new GitHub issue to begin implementation of the Bronze-to-Silver ETL pipeline.*