## Standalone Dockerfile for the local MCP proxy adapter
# Build context can be the app directory:
#   docker build -f apps/mcp-local-proxy/Dockerfile -t mcp-local-proxy:dev apps/mcp-local-proxy

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN pip install --upgrade pip && pip install poetry

WORKDIR /src

# Copy dependency manifests first for better caching
COPY pyproject.toml poetry.lock* README.md ./

# Install only runtime dependencies
RUN poetry install --only=main --no-root --no-ansi && \
    poetry cache clear pypi --all || true

# Copy application source
COPY app ./app

ENTRYPOINT ["python", "-m", "app.main"]
