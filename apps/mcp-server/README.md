# Hoopstat MCP Server

MCP (Model Context Protocol) server for exposing Gold layer basketball data to AI agents.

## Overview

This server implements the Model Context Protocol specifications to provide AI agents with access to basketball statistics stored in the Gold layer as Parquet files on S3. It follows serverless-first architecture principles and supports async processing for large data queries.

## Features

- MCP resource discovery endpoint
- Properly formatted resource manifests for available data  
- MCP protocol versioning and capability negotiation
- Clear resource descriptions and schemas
- Reusable MCP server framework components
- Request/response handling according to MCP specification
- Proper error handling and validation
- Async processing for large data queries

## Architecture

The server is designed as a serverless Python application that can run on AWS Lambda, fronted by Amazon API Gateway. It accesses basketball data from S3 Parquet files in the Gold layer using efficient querying strategies.

## Local Development

### Prerequisites

- Python 3.12+
- Poetry for dependency management

### Setup

```bash
# Install dependencies
poetry install

# Run formatting
poetry run ruff format .

# Run linting
poetry run ruff check .

# Run tests
poetry run pytest
```

### Testing

Run the quality checks that CI uses:

```bash
# From repository root
./scripts/local-ci-check.sh apps/mcp-server
```

## Usage

The MCP server can be run in development mode:

```bash
poetry run mcp-server
```

For development and debugging, use:

```bash
poetry run dev
```

## MCP Protocol Compliance

This server strictly adheres to the Model Context Protocol specifications. It supports:

- Resource discovery and capability negotiation
- JSON schema validation for requests and responses
- Proper error handling according to MCP standards
- Protocol versioning for compatibility

## Dependencies

- **mcp**: Official Model Context Protocol library
- **boto3**: AWS SDK for S3 access
- **pandas/pyarrow**: Data processing and Parquet reading
- **pydantic**: Data validation and serialization
- **hoopstat-config**: Project configuration management
- **hoopstat-data**: Data access utilities
- **hoopstat-observability**: Logging and monitoring

## License

See the main project LICENSE.md file.