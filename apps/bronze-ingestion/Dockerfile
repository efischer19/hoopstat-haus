## ARMv7 Dockerfile for Raspberry Pi 2 deployment
# Build context must be the repo root so Poetry can resolve local path deps in libs/
#   docker build -f apps/bronze-ingestion/Dockerfile -t bronze-ingestion:dev --platform linux/arm/v7 .

FROM python:3.12-slim

# Add build dependencies for compiling Python packages with C extensions
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential python3-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Install Poetry via pip
RUN pip install --upgrade pip && pip install poetry

# Use a build-friendly workspace so Poetry can resolve path deps
WORKDIR /src

# Copy dependency manifests first for better caching
COPY apps/bronze-ingestion/pyproject.toml apps/bronze-ingestion/poetry.lock* ./apps/bronze-ingestion/
# Copy local libraries referenced as path deps
COPY libs/ ./libs/

# Install only runtime deps into the base interpreter site-packages
RUN cd apps/bronze-ingestion && poetry install --only=main --no-root --no-ansi && \
    poetry cache clear pypi --all || true

# Copy application source
WORKDIR /app
COPY apps/bronze-ingestion/app ./app

# Set entrypoint to run ingestion command
ENTRYPOINT ["python", "-m", "app.main"]
CMD ["ingest"]