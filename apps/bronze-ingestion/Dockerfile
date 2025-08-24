## Lambda-first Dockerfile that installs Poetry deps (including local libs) into the Lambda runtime
# Build context must be the repo root so Poetry can resolve local path deps in libs/
#   docker build -f apps/bronze-ingestion/Dockerfile -t bronze-ingestion:dev .

FROM public.ecr.aws/lambda/python:3.12

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Install Poetry via pip (no OS packages needed)
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

# Copy application source into Lambda task root
WORKDIR ${LAMBDA_TASK_ROOT}
COPY apps/bronze-ingestion/app ./app

# Lambda handler
CMD ["app.lambda_handler.lambda_handler"]