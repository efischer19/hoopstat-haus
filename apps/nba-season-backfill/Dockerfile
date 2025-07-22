# Multi-stage Dockerfile for NBA Season Backfill Application
# This Dockerfile follows the project pattern for containerizing Python applications
# with proper dependency management and security practices.
#
# IMPORTANT: When building apps with shared library dependencies from libs/,
# this Dockerfile expects to be built from the repository root context:
#   docker build -f apps/nba-season-backfill/Dockerfile -t nba-backfill:latest .
#
# The CI automatically detects shared dependencies and uses repo root context.

# =============================================================================
# Base stage: Common base for all subsequent stages
# =============================================================================
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry with --trusted-host for environments with SSL issues
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org poetry

# Configure Poetry: Don't create virtual environment (we're in a container)
ENV POETRY_VENV_IN_PROJECT=0 \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set work directory to match app structure when building from repo root
WORKDIR /app

# =============================================================================
# Development stage: For local development with dev dependencies
# =============================================================================
FROM base AS development

# Copy the entire app directory to maintain relative path structure
COPY apps/nba-season-backfill/ .

# Copy libs directory to maintain relative path dependencies
COPY libs/ ../libs/

# Install dependencies including dev dependencies (Poetry handles path deps automatically)
RUN poetry install && rm -rf $POETRY_CACHE_DIR

# Default command for development
CMD ["poetry", "run", "python", "-m", "app.main"]

# =============================================================================
# Dependencies stage: Install only production dependencies
# =============================================================================
FROM base AS dependencies

# Copy the entire app directory to maintain relative path structure
COPY apps/nba-season-backfill/ .

# Copy libs directory to maintain relative path dependencies
COPY libs/ ../libs/

# Install only production dependencies (Poetry handles path deps automatically)
RUN poetry install --only=main && rm -rf $POETRY_CACHE_DIR

# =============================================================================
# Production stage: Minimal production image
# =============================================================================
FROM python:3.12-slim AS production

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy Python environment from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy shared libraries (maintaining editable install compatibility)
COPY --from=dependencies /libs /libs

# Copy application code
COPY --from=dependencies /app/app ./app

# Create directories for state management
RUN mkdir -p /app/state /app/data /app/logs

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import app.main; print('OK')" || exit 1

# Default command - CLI interface
ENTRYPOINT ["python", "-m", "app.main"]

# Default arguments (can be overridden)
CMD ["--help"]