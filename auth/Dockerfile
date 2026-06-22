FROM python:3.12-slim
WORKDIR .
RUN apt-get update \
    && apt-get install -y curl jq
COPY auth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY auth/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
