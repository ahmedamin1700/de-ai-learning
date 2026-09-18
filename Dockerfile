FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

RUN mkdir -p logs data

CMD ["python", "scripts/cli.py", "--help"]
