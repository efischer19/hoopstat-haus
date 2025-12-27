## Lambda-first Dockerfile that installs Poetry deps (including local libs) into the Lambda runtime
# Build context must be the repo root so Poetry can resolve local path deps in libs/
#   docker build -f apps/gold-analytics/Dockerfile -t gold-analytics:dev .

FROM public.ecr.aws/lambda/python:3.12

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Install Poetry and the export plugin
RUN pip install --upgrade pip && \
    pip install poetry poetry-plugin-export

# Use a build-friendly workspace so Poetry can resolve path deps
WORKDIR /src

# Copy dependency manifests first for better caching
COPY apps/gold-analytics/pyproject.toml apps/gold-analytics/poetry.lock* ./apps/gold-analytics/
# Copy local libraries referenced as path deps
COPY libs/ ./libs/

# Export dependencies to requirements.txt, excluding local libs which we install explicitly
# This ensures we have full control over how local path dependencies are installed
RUN cd apps/gold-analytics && \
    poetry export --without-hashes --format=requirements.txt | grep -v "hoopstat-" > requirements.txt && \
    pip install -r requirements.txt --target ${LAMBDA_TASK_ROOT}

# Install local libraries explicitly into the Lambda task root
RUN pip install \
    ./libs/hoopstat-observability \
    ./libs/hoopstat-data \
    ./libs/hoopstat-config \
    ./libs/hoopstat-s3 \
    --target ${LAMBDA_TASK_ROOT}

# Copy application source into Lambda task root
WORKDIR ${LAMBDA_TASK_ROOT}
COPY apps/gold-analytics/app ./app

# Lambda handler
CMD ["app.lambda_handler.lambda_handler"]