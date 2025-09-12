## Lambda-first Dockerfile that installs Poetry deps (including local libs) into the Lambda runtime
# Build context must be the repo root so Poetry can resolve local path deps in libs/
#   docker build -f apps/silver-processing/Dockerfile -t silver-processing:dev .

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
COPY apps/silver-processing/pyproject.toml apps/silver-processing/poetry.lock* ./apps/silver-processing/
# Copy local libraries referenced as path deps
COPY libs/ ./libs/

# Install only runtime deps into the base interpreter site-packages
RUN cd apps/silver-processing && poetry install --only=main --no-root --no-ansi && \
    poetry cache clear pypi --all || true

# Copy application source into Lambda task root
WORKDIR ${LAMBDA_TASK_ROOT}
COPY apps/silver-processing/app ./app

# Lambda handler
CMD ["app.handlers.lambda_handler"]