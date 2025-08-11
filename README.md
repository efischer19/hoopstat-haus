# Hoopstat Haus 🏀

[![Status: WIP](https://img.shields.io/badge/status-work_in_progress-yellow.svg)](https://github.com/efischer19/hoopstat-haus)

A GenAI-powered data lakehouse for NBA/WNBA stats. Your go-to for advanced hoops data!

---

> **Note:** This project is currently under active development and is not yet functional. The infrastructure and core components are being built. Please check back for updates!

## About The Project

Hoopstat Haus is an open-source project aimed at creating a comprehensive data lakehouse for basketball analytics. It ingests and processes NBA/WNBA statistics to provide deep insights for predictive modeling and powerful semantic search.

The core mission is to leverage modern data infrastructure and Generative AI to make advanced basketball analysis accessible and powerful.

## Tech Stack

This project is being built with a focus on robust, modern backend infrastructure:

* **Language:** Python
* **Core Functionality:** Data Ingestion, Processing, and Predictive Analytics
* **Deployment:** Fully automated via GitHub Actions

## Current Status

The repository has been seeded with foundational documents and architectural principles. The next phase of development will focus on building the core data ingestion pipelines.

The project is **not operational** at this time.

## Repository Structure

```
apps/           # Individual applications
libs/           # Shared Python libraries  
infrastructure/ # Terraform AWS infrastructure (includes ECR)
docs-src/       # Documentation source (MkDocs with Material theme)
scripts/        # Utility scripts (ECR helper, etc.)
meta/           # Project metadata and ADRs
templates/      # Project templates
```

Key infrastructure components:
- **AWS ECR**: Container registry with automated CI/CD integration
- **GitHub Actions**: Automated testing, building, and deployment
- **Terraform**: Infrastructure as code for AWS resources

## Contributing

While the core infrastructure is being established, contributions are welcome in the form of ideas, feature requests, and bug reports. Please see our **[Contributing Guidelines](.github/CONTRIBUTING.md)** for more details on how you can help shape the future of Hoopstat Haus.

### Quality Assurance for Contributors

To maintain code quality and reduce review cycles, please run local quality checks before submitting pull requests:

```bash
# For Python projects (apps and libs)
./scripts/local-ci-check.sh apps/your-app
./scripts/local-ci-check.sh libs/your-lib
```

**Optional**: Set up pre-commit hooks to automatically run quality checks:
```bash
pip install pre-commit
pre-commit install
```

This ensures your code passes the same checks that CI runs, catching formatting and linting issues early.

### Documentation

This project uses [MkDocs with Material theme](https://squidfunk.github.io/mkdocs-material/) for documentation. All documentation is authored in `docs-src/` and automatically published to GitHub Pages.

**Local Documentation Development:**
```bash
# Install documentation dependencies
pip install -r docs-requirements.txt

# Build documentation (includes API docs generation)
./scripts/build-docs.sh

# Serve documentation locally
mkdocs serve
```

The documentation site will be available at `http://localhost:8000` for local preview.

**Documentation Structure:**
- Library API documentation is automatically generated from docstrings
- Development guides and ADRs are manually authored in `docs-src/`
- Documentation is published to: https://efischer19.github.io/hoopstat-haus/

---
