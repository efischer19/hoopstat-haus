# Use AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.12

# Copy requirements and install dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only=main

# Copy application code
COPY player_daily_aggregator/ ${LAMBDA_TASK_ROOT}/player_daily_aggregator/

# Set the CMD to your handler
CMD ["player_daily_aggregator.lambda_handler.lambda_handler"]