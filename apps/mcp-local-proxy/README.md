# Hoopstat MCP Local Proxy

A lightweight MCP (Model Context Protocol) proxy adapter that runs locally and
provides AI agents with access to Hoopstat Haus NBA statistics data.

## Overview

This adapter translates MCP JSON-RPC queries from AI agents into standard HTTP
GET requests targeting static JSON artifacts served via CloudFront. All compute
runs locally -- the cloud serves only static data.

## Installation

```bash
# Via uvx (recommended)
uvx hoopstat-mcp

# Via pip
pip install hoopstat-mcp-proxy
```

## Configuration

Set the `HOOPSTAT_BASE_URL` environment variable to override the default
CloudFront endpoint:

```bash
export HOOPSTAT_BASE_URL="https://data.hoopstat.haus"
```

## Usage

The adapter communicates via stdio and is designed to be invoked by MCP-capable
AI agents (e.g., Claude Desktop, Cursor, VS Code).

### Claude Desktop Configuration

Add to your Claude Desktop MCP config:

```json
{
  "mcpServers": {
    "hoopstat": {
      "command": "uvx",
      "args": ["hoopstat-mcp"]
    }
  }
}
```

## Available Tools

### `get_index`

Fetches the latest data index listing all available datasets, dates, and
resource URIs.

### `get_artifact`

Fetches a specific JSON artifact by resource URI. Examples:

- `player_daily/2024-11-15/2544` -- LeBron James' stats for a given date
- `team_daily/2024-11-15/1610612747` -- Lakers' team stats
- `top_lists/2024-11-15/points` -- Top scorers list

## Development

```bash
cd apps/mcp-local-proxy
poetry install
poetry run pytest
poetry run ruff format .
poetry run ruff check .
```
