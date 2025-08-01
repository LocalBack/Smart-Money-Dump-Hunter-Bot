FROM python:3.12-alpine
WORKDIR /app
COPY pyproject.toml poetry.lock README.md /app/
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-interaction --no-root
COPY src /app/src
CMD ["python", "-m", "smartmoney_bot.collector"]
