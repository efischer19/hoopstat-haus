# E2E Testing Updates for Bronze Parquet Support

## Overview
The bronze-ingestion refactor to use Parquet storage requires corresponding updates to the E2E testing framework in `libs/hoopstat-e2e-testing`.

## Required Changes

### 1. Update Pipeline Test Runner
**File**: `libs/hoopstat-e2e-testing/hoopstat_e2e_testing/pipeline_runner.py`

- Modify bronze layer data expectations from JSON to Parquet format
- Update S3 key validation to match new structure: `raw/<entity>/date=YYYY-MM-DD/data.parquet`
- Add Parquet reading capabilities using pyarrow/pandas

### 2. Update S3 Test Utilities  
**File**: `libs/hoopstat-e2e-testing/hoopstat_e2e_testing/s3_utils.py`

- Add methods for reading/validating Parquet files from S3
- Update bronze layer validation functions
- Ensure compatibility with new date-partitioned structure

### 3. Test Data Generation
- Modify mock data generators to support date-scoped data creation
- Update test scenarios to use date-based ingestion rather than season-based

### 4. Integration Test Updates
- Update existing integration tests to expect Parquet outputs in Bronze
- Add new tests for date-scoped ingestion scenarios
- Validate idempotent behavior for date-based writes

## Implementation Approach

1. **Phase 1**: Update utility functions to read Parquet from Bronze layer
2. **Phase 2**: Modify pipeline runner to validate new Bronze structure
3. **Phase 3**: Update or add integration tests for new ingestion pattern
4. **Phase 4**: Ensure bronze → silver → gold pipeline tests still pass

## Dependencies
- Ensure pyarrow is available in the E2E testing environment
- Update any Docker configurations to include Parquet support

This work should be done as a follow-up task after the core bronze-ingestion refactor is merged and validated.