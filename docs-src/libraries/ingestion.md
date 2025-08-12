# ingestion

**Version:** 0.1.0

## Description

A Python library for ingesting NBA data from the nba-api, converting to Parquet format, and uploading to S3 with proper partitioning and rate limiting.

## Installation

Add to your application's `pyproject.toml`:

```toml
[tool.poetry.dependencies]
ingestion = {path = "../libs/ingestion", develop = true}
```
