# Hoopstat Haus 🏀

[![Status: WIP](https://img.shields.io/badge/status-work_in_progress-yellow.svg)](https://github.com/efischer19/hoopstat-haus)

A GenAI-powered data lakehouse for NBA/WNBA stats. Your go-to for advanced hoops data!

## Project status

Pre-release hobby project. The pipeline code exists and is tested, but no public data is being published today. Last checked 2026-09-28. Last active development was early April 2026; since then the only changes have been automated dependency updates.

| Area | Status |
| :--- | :----- |
| Bronze ingestion (NBA API to S3) | Works when run manually on a local machine with Docker. It no longer runs in AWS because the NBA API blocks AWS IPs, and the scheduled workflow is disabled. |
| Silver processing, Gold analytics, DB compiler | Code and unit tests exist. Silver was last run manually in January 2026. Gold has no scheduled run. |
| Daily "Build Database" job | Runs green every day but does nothing: it finds no Gold index in S3, so it skips compiling and uploading. No database has been published. |
| Public data (`data.hoopstat.haus`, JSON artifacts, DuckDB/SQLite files) | Not available. The domain does not resolve. |
| Frontend ([`hoopstat.haus`](https://hoopstat.haus)) | The page is up but loads no stats: its data URL is still a placeholder. The pipeline health page returns no data. |
| MCP local proxy | Code and tests exist. Not published to PyPI. |
| WNBA data, S3 Tables, semantic search / GenAI features | Planned in ADRs and docs. No code yet. |

---

## 🚀 Quick Start: Access Basketball Analytics

> [!WARNING]
> None of the endpoints below are live yet. See [Project status](#project-status). This section describes the intended access pattern.

### 🗄️ Static SQL Databases (NEW)

Query the entire Gold analytics dataset with SQL — no API keys, no auth required. Two formats available:

| Format | URL | Best For |
|--------|-----|----------|
| **DuckDB** | `https://data.hoopstat.haus/db/nba_current_season.duckdb` | Remote queries, analytics, AI agents |
| **SQLite** | `https://data.hoopstat.haus/db/nba_current_season.sqlite` | Mobile apps, web backends, zero-dep scripts |

**DuckDB — query remotely (no download needed):**
```python
import duckdb
result = duckdb.sql("""
    SELECT player_name, points_per_game
    FROM 'https://data.hoopstat.haus/db/nba_current_season.duckdb'.player_season_summary
    ORDER BY points_per_game DESC LIMIT 10
""")
print(result)
```

**SQLite — download and query with zero dependencies:**
```bash
curl -o nba.sqlite https://data.hoopstat.haus/db/nba_current_season.sqlite
sqlite3 nba.sqlite "SELECT player_name, points_per_game FROM player_season_summary ORDER BY points_per_game DESC LIMIT 10;"
```

👉 **[Full Database Guide](docs-src/DATABASE_GUIDE.md)** — schema docs, 12+ example queries, format comparison, Python/Node.js examples, and troubleshooting.

### 📦 Stateless JSON Artifacts

Per ADR-027, initial public access is also provided via small, precomputed JSON artifacts served directly from S3. No auth required.

#### What’s available
- player_daily: per-player daily metrics
- team_daily: per-team daily metrics
- top_lists: curated top metrics (e.g., top_ts, top_per, top_efg, top_net)
- index/latest.json: pointer to the most recent available dates

All artifacts are versioned (v1) and capped at ~100 KB for fast, low-cost access.

### 📊 Data Availability
- Coverage: 2023-24 NBA season onwards
- Updates: Daily, 2–4 hours after games complete
- Format: JSON artifacts + DuckDB / SQLite databases under gold/served/
- Access: Public CloudFront with CORS — no auth required

Note: MCP (Model Context Protocol) integration will use a **local proxy adapter** pattern -- all MCP compute runs on the AI client's machine, not in our cloud. See [ADR-033](meta/adr/ADR-033-local_proxy_mcp_architecture.md) for architecture details.

## About The Project

Hoopstat Haus is an open-source project aimed at creating a comprehensive data lakehouse for basketball analytics. It ingests and processes NBA/WNBA statistics to provide deep insights for predictive modeling and powerful semantic search.

The core mission is to leverage modern data infrastructure and Generative AI to make advanced basketball analysis accessible and powerful.

## Tech Stack

This project is being built with a focus on robust, modern backend infrastructure:

* **Language:** Python
* **Core Functionality:** Data Ingestion, Processing, and Predictive Analytics
* **Deployment:** Fully automated via GitHub Actions

## Current Status

See [Project status](#project-status) above.

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
- Documentation is intended to publish to https://efischer19.github.io/hoopstat-haus/ (currently returns 404; build locally as above)

---
