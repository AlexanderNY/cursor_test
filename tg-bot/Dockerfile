FROM python:3.12-slim

WORKDIR /app

COPY tg-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared_storage /app/shared_storage
COPY tg-bot/ .

RUN mkdir -p sessions

EXPOSE 8004

CMD ["python", "main.py"]
