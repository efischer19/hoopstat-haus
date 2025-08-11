# Hoopstat S3 Library

A Python library for S3 storage and Parquet data processing for NBA data with proper partitioning.

## Features

- **Parquet Conversion**: Convert raw JSON responses to optimized Parquet format
- **S3 Upload**: Upload data to S3 with proper date-based partitioning
- **Error Handling**: Comprehensive error logging and retry logic
- **Data Optimization**: Efficient compression and storage formats

## Architecture

This library follows the architectural decisions:
- **ADR-014**: Stores data in Apache Parquet format for optimal analytics performance

## Usage

```python
from hoopstat_s3 import ParquetConverter, S3Uploader
from datetime import date

# Initialize components
converter = ParquetConverter(compression="snappy")
uploader = S3Uploader(
    bucket_name="your-bucket",
    region_name="us-east-1"
)

# Convert JSON data to Parquet
game_data = {"games": [...]}  # Your NBA API response
parquet_data = converter.convert_games(game_data)

# Upload to S3 with date partitioning
uploader.upload_games(parquet_data, date(2024, 1, 15))

# Upload player data
player_data = {"players": [...]}
parquet_data = converter.convert_players(player_data)
uploader.upload_players(parquet_data, date(2024, 1, 15))
```

## S3 Partitioning Strategy

Data is stored using the following partitioning scheme:

```
s3://bucket/nba-api/{data_type}/year={year}/month={month}/day={day}/hour={hour}/
```

This enables efficient querying and cost-effective storage management.

## Installation

This library is designed to be used as a shared dependency within the hoopstat-haus monorepo.

## Development

```bash
poetry install
poetry run pytest
poetry run ruff check .
poetry run ruff format .
```

## Supported Data Types

- Games
- Players  
- Teams
- Statistics
- Generic JSON data

All data is automatically optimized for analytics workloads using Apache Parquet format with Snappy compression.