FROM python:3.12-slim
WORKDIR /app
RUN apt-get update \
    && apt-get install -y curl jq
COPY selectcb/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY selectcb/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8008"]
