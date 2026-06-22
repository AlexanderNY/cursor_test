FROM python:3.12-slim
WORKDIR /app
COPY core/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared_storage /app/shared_storage
COPY core/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
