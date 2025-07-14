# Apps Directory

This directory contains all applications in the Hoopstat Haus project, following the monorepo structure defined in ADR-008.

## Creating New Applications

To create a new Python application:

1. Copy the template:
   ```bash
   cp -r templates/python-app-template apps/your-new-app
   cd apps/your-new-app
   ```

2. Update the project configuration in `pyproject.toml`
3. Install dependencies: `poetry install`
4. Start developing!

## Current Applications

This directory will contain applications such as:
- Web dashboard for viewing basketball statistics
- Data pipeline for processing game data
- APIs for accessing statistical data
- Utility applications for data management

Each application follows the standard Python development patterns established in the project ADRs.