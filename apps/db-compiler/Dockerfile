## Standalone Dockerfile for the db-compiler CLI tool
# Build context can be the app directory:
#   docker build -f apps/db-compiler/Dockerfile -t db-compiler:dev apps/db-compiler

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

# Copy application source and schema files
COPY app ./app
COPY schema ./schema

ENTRYPOINT ["python", "-m", "app.main"]
