# Multi-stage Dockerfile for Bronze Layer Ingestion Application
# This Dockerfile demonstrates best practices for containerizing Python applications
# in the Hoopstat Haus project.
#
# IMPORTANT: When building apps with shared library dependencies from libs/,
# this Dockerfile expects to be built from the repository root context:
#   docker build -f apps/bronze-ingestion/Dockerfile -t bronze-ingestion:latest .
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
COPY apps/bronze-ingestion/ .

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

# Copy the application and library files [cite: 108, 109]
COPY apps/bronze-ingestion/ .
COPY libs/ ../libs/

# Create a virtual environment 
RUN python -m venv /opt/venv

# Activate the virtual environment and install dependencies into it
RUN . /opt/venv/bin/activate && \
    poetry install --only=main --no-root && \
    rm -rf $POETRY_CACHE_DIR

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

# Copy the virtual environment from dependencies stage
COPY --from=dependencies /opt/venv /opt/venv

# Copy shared libraries (maintaining editable install compatibility)
COPY --from=dependencies /libs /libs

# Copy application code
COPY --from=dependencies /app/app ./app

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

# =============================================================================
# Lambda stage: AWS Lambda Runtime Interface Emulator compatible
# =============================================================================
FROM public.ecr.aws/lambda/python:3.12 AS lambda

# Set environment variables for Lambda
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy the virtual environment from dependencies stage
COPY --from=dependencies /opt/venv /opt/venv

# Copy shared libraries - copy all hoopstat packages to a flat structure for simple imports
COPY --from=dependencies /libs /tmp/libs
RUN mkdir -p /libs && \
    for lib_dir in /tmp/libs/hoopstat-*; do \
        if [ -d "$lib_dir" ]; then \
            lib_name=$(basename "$lib_dir" | sed 's/-/_/g'); \
            if [ -d "$lib_dir/$lib_name" ]; then \
                cp -r "$lib_dir/$lib_name" "/libs/"; \
            fi; \
        fi; \
    done && \
    rm -rf /tmp/libs

# Ensure Lambda runtime can find installed packages and all shared libraries
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/opt/venv/lib/python3.12/site-packages:/libs"

# Copy application code to Lambda function directory
COPY --from=dependencies /app/app ${LAMBDA_TASK_ROOT}/app

# Set the Lambda handler
CMD ["app.lambda_handler.lambda_handler"]