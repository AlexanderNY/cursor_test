FROM python:3.12-slim

WORKDIR /app

COPY tg-game/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY tg-game/ .

EXPOSE 8015

CMD ["python", "main.py"]
