# Shared Library Versioning Guide

This document outlines the versioning strategy for shared libraries in the Hoopstat Haus monorepo, as established in [ADR-016](../meta/adr/ADR-016-shared_library_versioning.md).

## Overview

Shared libraries in the `/libs` directory follow [Semantic Versioning (SemVer)](https://semver.org/) to enable clear dependency management and stable deployments.

## Semantic Versioning Format

All shared libraries use the **MAJOR.MINOR.PATCH** format:

- **MAJOR**: Incremented for breaking changes that require code changes in consuming applications
- **MINOR**: Incremented for new features that are backward compatible
- **PATCH**: Incremented for bug fixes that are backward compatible

### Examples

- `1.0.0` → `1.0.1`: Bug fix (safe to update)
- `1.0.1` → `1.1.0`: New backward-compatible feature (safe to update) 
- `1.1.0` → `2.0.0`: Breaking change (requires code changes in apps)

## Version Management Process

### 1. Initial Library Version

New libraries start at version `0.1.0` to indicate pre-release status:

```toml
[tool.poetry]
name = "my-new-library"
version = "0.1.0"
```

### 2. Version Bumping Guidelines

#### For Bug Fixes (PATCH)
```bash
# Fix a bug without changing the API
# 1.0.0 → 1.0.1
poetry version patch
```

#### For New Features (MINOR)
```bash
# Add new functions/classes without breaking existing ones
# 1.0.1 → 1.1.0
poetry version minor
```

#### For Breaking Changes (MAJOR)
```bash
# Change function signatures, remove functions, change behavior
# 1.1.0 → 2.0.0
poetry version major
```

### 3. Pre-release Versions

For development versions before a stable release:

```bash
# Create a pre-release version
# 1.0.0 → 1.1.0-alpha.1
poetry version preminor --next-phase=alpha

# Bump pre-release
# 1.1.0-alpha.1 → 1.1.0-alpha.2
poetry version prerelease
```

## Dependency Management Between Apps and Libraries

### Development Dependencies (Recommended)

For active development, applications should use local path dependencies:

```toml
# In apps/my-app/pyproject.toml
[tool.poetry.dependencies]
python = "^3.12"
# Use local path for development
basketball-stats = {path = "../../libs/basketball-stats", develop = true}
data-utils = {path = "../../libs/data-utils", develop = true}
```

Benefits:
- Immediate access to library changes during development
- No version management overhead for local development
- Supports rapid iteration and testing

### Production Dependencies (Optional)

For production stability, applications can pin to specific versions:

```toml
# In apps/my-app/pyproject.toml
[tool.poetry.dependencies]
python = "^3.12"
# Pin to specific versions for stability
basketball-stats = {path = "../../libs/basketball-stats", version = "^1.2.0"}
data-utils = {path = "../../libs/data-utils", version = "^2.0.0"}
```

### Version Constraint Guidelines

Use caret constraints (`^`) for most dependencies:

```toml
# Allows 1.2.0 ≤ version < 2.0.0
basketball-stats = {path = "../../libs/basketball-stats", version = "^1.2.0"}

# For pre-1.0 libraries, use tilde constraints to avoid breaking changes
experimental-lib = {path = "../../libs/experimental-lib", version = "~0.3.0"}
```

## Breaking Change Management

### 1. Planning Breaking Changes

Before introducing breaking changes:

1. **Document the change**: Update library README with migration guide
2. **Deprecation period**: Mark old functionality as deprecated in a minor release
3. **Communication**: Notify application maintainers of upcoming changes

### 2. Implementing Breaking Changes

1. **Create migration documentation** in the library's README
2. **Bump major version** using `poetry version major`
3. **Update library changelog** with clear migration instructions
4. **Update applications** that consume the library

### 3. Migration Strategy

For gradual migration:

1. **Version pinning**: Pin applications to the last compatible version
2. **Parallel development**: Applications can migrate at their own pace
3. **Testing**: Verify compatibility before updating dependencies

## Library Release Checklist

Before releasing a new library version:

- [ ] Update version in `pyproject.toml` using `poetry version`
- [ ] Update `CHANGELOG.md` (if present) with changes
- [ ] Run tests: `poetry run pytest`
- [ ] Run linting: `poetry run ruff check`
- [ ] Update documentation if needed
- [ ] Commit version bump: `git commit -m "bump: version X.Y.Z"`
- [ ] Tag release: `git tag vX.Y.Z` (optional, for tracking)

## Best Practices

### 1. Version Consistency

- Use `poetry version` command to ensure consistent version bumping
- Keep versions in sync with actual changes (don't skip versions)
- Document breaking changes clearly in commit messages

### 2. Dependency Updates

- Review library changes before updating dependencies in applications
- Test applications thoroughly after updating library dependencies
- Use version ranges (`^1.0.0`) rather than exact pins when possible

### 3. Backward Compatibility

- Maintain backward compatibility within major versions
- Use deprecation warnings before removing functionality
- Provide clear migration paths for breaking changes

### 4. Development Workflow

- Use local path dependencies during active development
- Consider version pinning for critical production applications
- Coordinate library updates across multiple consuming applications

## Common Patterns

### Pattern 1: Feature Development

```bash
# 1. Develop new feature in library
cd libs/my-library
# Work on feature...
poetry run pytest  # Ensure tests pass

# 2. Bump minor version for new feature
poetry version minor  # 1.0.0 → 1.1.0

# 3. Update consuming applications (optional)
cd apps/my-app
# Update dependency version if needed
poetry update my-library
```

### Pattern 2: Bug Fix

```bash
# 1. Fix bug in library
cd libs/my-library
# Fix the bug...
poetry run pytest

# 2. Bump patch version
poetry version patch  # 1.1.0 → 1.1.1

# 3. Applications using ^1.1.0 will automatically get the fix
```

### Pattern 3: Breaking Change

```bash
# 1. Plan and communicate breaking change
# 2. Implement change in library
cd libs/my-library
# Make breaking changes...
poetry run pytest

# 3. Bump major version
poetry version major  # 1.1.1 → 2.0.0

# 4. Update applications one by one
cd apps/my-app
# Update code to work with new API
# Update dependency version
poetry add my-library@^2.0.0
```

## Troubleshooting

### Issue: "Package not found" errors

**Solution**: Ensure the library path is correct and the library has a valid `pyproject.toml`:

```bash
# Verify library structure
ls libs/my-library/pyproject.toml
ls libs/my-library/my_library/__init__.py
```

### Issue: Version conflicts between libraries

**Solution**: Use compatible version ranges and coordinate updates:

```bash
# Check current versions
poetry show | grep my-library

# Update with compatible constraints
poetry add my-library@^1.0.0
```

### Issue: Development changes not reflected

**Solution**: Ensure using development mode for local dependencies:

```toml
my-library = {path = "../../libs/my-library", develop = true}
```

This versioning strategy enables stable dependency management while maintaining the flexibility needed for monorepo development workflows.