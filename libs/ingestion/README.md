# Hoopstat NBA Ingestion Library

A Python library for ingesting NBA data from the nba-api, converting to Parquet format, and uploading to S3 with proper partitioning and rate limiting.

## Features

- **NBA API Client**: Respectful rate-limited client for fetching NBA data
- **Parquet Conversion**: Convert raw JSON responses to optimized Parquet format
- **S3 Upload**: Upload data to S3 with proper date-based partitioning
- **Error Handling**: Comprehensive error logging and exponential backoff
- **Rate Limiting**: Built-in protection against API abuse

## Architecture

This library follows the architectural decisions:
- **ADR-013**: Uses nba-api as the primary NBA data source
- **ADR-014**: Stores data in Apache Parquet format for optimal analytics performance

## Usage

```python
from hoopstat_nba_ingestion import NBAClient, ParquetConverter, S3Uploader
from datetime import date

# Initialize components
client = NBAClient()
converter = ParquetConverter()
uploader = S3Uploader(bucket="your-bucket")

# Fetch and process data
game_data = client.get_games_for_date(date(2024, 1, 15))
parquet_data = converter.convert_games(game_data)
uploader.upload_games(parquet_data, date(2024, 1, 15))
```

## Installation

This library is designed to be used as a shared dependency within the hoopstat-haus monorepo.

## Development

```bash
poetry install
poetry run pytest
poetry run ruff check .
poetry run black .
```