FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Build context = repo root (see nine-to-eighteen/docker-compose.yml).
COPY nine-to-eighteen/resume/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY shared /app/shared
COPY nine-to-eighteen/resume/ .

ENV PYTHONPATH=/app
EXPOSE 8021
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8021", "--timeout-keep-alive", "75"]
