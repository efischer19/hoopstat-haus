# Math Utility Tool

A simple command-line utility that demonstrates the non-deployable application pattern in the Hoopstat Haus monorepo.

## Purpose

This utility tool showcases:
- **Non-deployable application**: No Dockerfile required
- **Shared library usage**: Uses `example-math-utils` for calculations
- **CI/CD testing**: Validated through standard testing (format, lint, test) without Docker builds

## Usage

```bash
# Run the utility
cd apps/math-utility-tool
poetry run calculate

# Development commands
poetry run test    # Run tests
poetry run lint    # Check code quality
poetry run format  # Format code
```

## CI/CD Behavior

This application demonstrates the "utility tool" pattern in our CI pipeline:
- ✅ Format, lint, and test validation
- 🚫 No Docker build required (no Dockerfile)
- 🛠️ Marked as utility/tool in CI output

This is ideal for:
- Command-line utilities
- Data processing scripts
- Development tools
- Analysis utilities

## Dependencies

- `example-math-utils`: Shared math library with hot reloading support