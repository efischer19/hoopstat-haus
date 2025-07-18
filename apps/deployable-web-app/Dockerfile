# Multi-stage Dockerfile for Deployable Web Application
# This Dockerfile can handle shared library dependencies when built from repo root

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

# Install Poetry
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org poetry

# Configure Poetry
ENV POETRY_VENV_IN_PROJECT=0 \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set work directory
WORKDIR /app

# =============================================================================
# Dependencies stage: Install production dependencies
# =============================================================================
FROM base AS dependencies

# Copy project files and any shared libraries
COPY apps/deployable-web-app/pyproject.toml apps/deployable-web-app/poetry.lock* ./
COPY libs/ ./libs/

# Install only production dependencies
RUN poetry install --only=main --no-root && rm -rf $POETRY_CACHE_DIR

# =============================================================================
# Production stage: Minimal production image
# =============================================================================
FROM python:3.12-slim AS production

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy Python environment from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY apps/deployable-web-app/app/ ./app/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import app.main; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "app.main"]

# Expose port (if this becomes a web service)
# EXPOSE 8000