FROM python:3.12-slim
WORKDIR /app
RUN apt-get update \
    && apt-get install -y curl jq
COPY api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api-gateway/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
