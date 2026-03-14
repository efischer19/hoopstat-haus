# Hoopstat MCP Setup Guide

This guide shows how to connect your AI client to the **Hoopstat Haus MCP
server** for live NBA statistics data. The server runs locally on your machine
and fetches pre-computed JSON artifacts from the public Hoopstat Haus data
endpoint -- **no API keys, no AWS credentials, no configuration required.**

## Quick Start

Install the package from PyPI and run the CLI command:

```bash
pip install hoopstat-mcp-proxy
hoopstat-mcp --mcp
```

The PyPI package is called `hoopstat-mcp-proxy`; installing it provides the
`hoopstat-mcp` command. When invoked with the `--mcp` flag, the server
communicates over stdio and is ready for any MCP-capable AI client. Without
the flag, `hoopstat-mcp` starts an interactive CLI for querying data directly
from your terminal.

---

## Client Configuration

### Claude Desktop

Add the following to your Claude Desktop MCP configuration file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "hoopstat": {
      "command": "hoopstat-mcp",
      "args": ["--mcp"]
    }
  }
}
```

### Cursor

Add the following to your Cursor MCP configuration file at
`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "hoopstat": {
      "command": "hoopstat-mcp",
      "args": ["--mcp"]
    }
  }
}
```

### VS Code (Copilot)

Add the following to your VS Code `settings.json` or workspace
`.vscode/mcp.json`:

```json
{
  "mcp": {
    "servers": {
      "hoopstat": {
        "command": "hoopstat-mcp",
        "args": ["--mcp"]
      }
    }
  }
}
```

### Generic MCP Client

Any MCP client that supports stdio transport can use the server. The command is:

```
hoopstat-mcp --mcp
```

No environment variables or authentication tokens are needed.

---

## Available Tools

Once connected, the server exposes two tools:

| Tool | Description |
|------|-------------|
| `get_index` | Fetch the latest data index listing all available datasets, dates, and resource URIs. |
| `get_artifact` | Fetch a specific JSON artifact by resource URI (e.g. `player_daily/2024-11-15/2544`). |

**Recommended workflow:** Call `get_index` first to discover available dates and
resource URIs, then call `get_artifact` with a specific URI.

---

## Developer Testing

To run the server locally for development and testing:

```bash
cd apps/mcp-local-proxy
poetry install
poetry run hoopstat-mcp --mcp
```

The server starts on stdio transport. You can pipe JSON-RPC messages to it
or use an MCP inspector tool to interact with it.

You can also use the CLI to query data directly:

```bash
poetry run hoopstat-mcp get-index
poetry run hoopstat-mcp get-artifact player_daily/2024-11-15/2544
```

### Using the MCP Inspector

The MCP SDK includes an inspector for interactive testing:

```bash
cd apps/mcp-local-proxy
poetry install
poetry run mcp dev app/server.py
```

### Running Tests

```bash
cd apps/mcp-local-proxy
poetry install
poetry run pytest
```

### Overriding the Data Endpoint

Set the `HOOPSTAT_BASE_URL` environment variable to point the proxy at a
different data source (e.g. a local test server):

```bash
HOOPSTAT_BASE_URL="http://localhost:8000" poetry run hoopstat-mcp --mcp
```

---

## Zero-Config Design

The Hoopstat MCP server is designed for **zero configuration**:

- **No API keys** -- data is served from a public CloudFront endpoint.
- **No AWS credentials** -- the server makes plain HTTP GET requests.
- **No database** -- all data is pre-computed static JSON.
- **No environment variables required** -- sensible defaults are built in.

The only thing you need is Python 3.12+ (or `uvx`) installed on your machine.
