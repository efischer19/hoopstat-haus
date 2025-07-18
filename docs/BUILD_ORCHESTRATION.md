# Build and Test Orchestration

This document describes the enhanced CI/CD pipeline that validates shared library compatibility and handles deployment requirements appropriately.

## Overview

The CI pipeline has been enhanced to support the monorepo structure with shared libraries (`/libs`) and applications (`/apps`). It provides comprehensive testing while ensuring that deployment requirements are only enforced where appropriate.

## Pipeline Structure

### 1. Change Detection (`detect-changes`)
- Detects changes in both `/apps` and `/libs` directories
- Creates dynamic build matrices for changed components
- Outputs separate matrices for applications and libraries

### 2. Library Testing (`test-libraries`)
- **Triggers**: When changes detected in `/libs`
- **Tests**: Format, lint, and unit tests for each changed library
- **No Docker requirement**: Libraries are not deployable and don't need containerization
- **Validation**: Ensures shared libraries are ready for consumption by applications

### 3. Application Testing (`test-applications`)
- **Triggers**: When changes detected in `/apps`
- **Tests**: Format, lint, and unit tests for each changed application
- **Conditional Docker builds**: Based on application type
  - **Deployable apps**: Must have Dockerfile, Docker build required
  - **Utility tools**: No Dockerfile required, skips Docker build
- **Smart detection**: Automatically determines build context for apps with shared library dependencies

### 4. Integration Testing (`test-integration`)
- **Triggers**: When both apps and libraries have changes
- **Purpose**: Validates that applications work correctly with updated shared libraries
- **Process**: Re-runs application tests with updated library dependencies

## Application Types

### Deployable Applications
- **Characteristics**: Intended for production deployment
- **Requirements**: Must have a `Dockerfile`
- **CI Behavior**: 
  - Standard testing (format, lint, test)
  - Docker build validation
  - Build context automatically adjusted for shared library dependencies

### Utility Applications  
- **Characteristics**: Tools, scripts, or non-deployable utilities
- **Requirements**: No `Dockerfile` needed
- **CI Behavior**:
  - Standard testing (format, lint, test)
  - Docker build skipped
  - Marked as utility in CI output

## Shared Library Dependencies

When applications depend on shared libraries:

1. **Detection**: CI automatically detects local library dependencies in `pyproject.toml`
2. **Build Context**: Docker builds are executed from repository root to include library code
3. **Integration Testing**: Ensures apps work with updated library versions

### Example Dependency Declaration
```toml
[tool.poetry.dependencies]
python = "^3.12"
my-shared-lib = {path = "../../libs/my-shared-lib", develop = true}
```

## CI/CD Workflow Benefits

### Clear Failure Attribution
- **Library failures**: Isolated to library testing jobs
- **Application failures**: Separated by app type (deployable vs utility)
- **Integration failures**: Clearly identify app-library compatibility issues

### Efficient Resource Usage
- **Selective testing**: Only test changed components
- **Conditional Docker**: Only build containers when needed
- **Parallel execution**: Libraries and applications test in parallel

### Deployment Readiness
- **Deployable apps**: Validated with Docker builds
- **Utility tools**: Tested for functionality without deployment overhead
- **Shared libraries**: Validated independently and through integration

## Error Scenarios

### Missing Dockerfile for Deployable App
```
❌ Deployable application my-app is missing required Dockerfile
```

### Utility App (Expected Behavior)
```
🛠️ Application my-tool is a utility/tool (no Dockerfile required)
✅ Utility/tool application validated successfully
```

### Library Failure
```
❌ Library test-utils failed format check
📦 Library is NOT ready for use by applications
```

### Integration Failure
```
❌ Integration testing failed for my-app
🔗 Application does NOT work correctly with updated shared libraries
```

## Future Enhancements

- **Deployment markers**: Optional `pyproject.toml` metadata to explicitly mark deployable vs utility apps
- **Library versioning**: Automatic version bumping and compatibility checking
- **Dependency analysis**: Automatically test downstream applications when libraries change
- **Security scanning**: Container vulnerability assessment for deployable applications