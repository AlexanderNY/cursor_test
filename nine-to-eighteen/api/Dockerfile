FROM python:3.12-slim
WORKDIR /app

# Build context = repo root (see nine-to-eighteen/docker-compose.yml).
COPY nine-to-eighteen/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY nine-to-eighteen/api/ .

ENV PYTHONPATH=/app
EXPOSE 8020
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8020"]
