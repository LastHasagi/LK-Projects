FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .

RUN playwright install-deps firefox && python -m camoufox fetch

COPY app ./app
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

CMD ["python", "-m", "app.main"]
