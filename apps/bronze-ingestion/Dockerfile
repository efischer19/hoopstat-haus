# Minimal Lambda-first Dockerfile for bronze-ingestion
# - Builder stage installs runtime dependencies into /opt/venv using Poetry
# - Final stage uses AWS Lambda Python base image and sets the handler
#
# Build context must be the repo root so Poetry can resolve local path deps in libs/
#   docker build -f apps/bronze-ingestion/Dockerfile -t bronze-ingestion:dev .

# ---------------------------------------------------
# Builder: install runtime deps into a virtualenv
# ---------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1

# Only what's needed to install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install poetry

WORKDIR /src

# Copy dependency manifests first for better caching
COPY apps/bronze-ingestion/pyproject.toml apps/bronze-ingestion/poetry.lock ./apps/bronze-ingestion/
# Copy shared libraries because pyproject.toml references them via local path deps
COPY libs/ ./libs/

# Create virtual environment and install only runtime deps
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN cd apps/bronze-ingestion && poetry install --only=main --no-root

# Now copy the application source
COPY apps/bronze-ingestion/app ./apps/bronze-ingestion/app

# ---------------------------------------------------
# Final: AWS Lambda Python base image
# ---------------------------------------------------
FROM public.ecr.aws/lambda/python:3.12

# Bring in the virtualenv with all installed dependencies
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/opt/venv/lib/python3.12/site-packages:$PYTHONPATH"

# Ensure `python` command exists for CI health checks (Lambda base guarantees python3)
RUN ln -sf $(which python3) /usr/local/bin/python || true

# Copy application code into Lambda task root so `app` is importable
WORKDIR ${LAMBDA_TASK_ROOT}
COPY --from=builder /src/apps/bronze-ingestion/app ./app

# If Poetry installed local path dependencies in editable mode, the egg-links
# reference /src/libs. Copy libs to that absolute path so imports resolve.
COPY --from=builder /src/libs /src/libs

# Set the Lambda handler (module.function)
CMD ["app.lambda_handler.lambda_handler"]

# For local CLI runs, you can override entrypoint/cmd, e.g.:
#   docker run --rm -it --entrypoint python <image> -m app.main --help