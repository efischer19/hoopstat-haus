# db-compiler

Compiles Gold-layer JSON artifacts from S3 into DuckDB and SQLite database files.

## Usage

```bash
# Compile both formats from a local directory of Gold JSON artifacts
poetry run compile --local-dir ./test-data/ --output-dir /tmp/db/

# Compile from an S3 bucket (requires AWS credentials)
poetry run compile --s3-bucket hoopstat-haus-gold --output-dir /tmp/db/

# Compile only DuckDB format
poetry run compile --local-dir ./test-data/ --output-dir /tmp/db/ --format duckdb

# Dry run — discover and report artifact counts without writing databases
poetry run compile --local-dir ./test-data/ --dry-run
```

## Output

- `nba_current_season.duckdb` — DuckDB database openable with `duckdb /path/to/file.duckdb`
- `nba_current_season.sqlite` — SQLite database openable with `sqlite3 /path/to/file.sqlite`
