FROM python:3.12-slim
WORKDIR /app
COPY processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY processor/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
