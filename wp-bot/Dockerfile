FROM python:3.12-slim
WORKDIR /app
COPY wp-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY wp-bot/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8006"]
