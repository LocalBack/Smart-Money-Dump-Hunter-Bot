FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential gcc \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock README.md /app/

RUN pip install --no-cache-dir poetry \
  && poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-root

COPY src /app/src

ENV PYTHONPATH=/app/src

CMD ["sh", "-c", "python -m $SERVICE"]
