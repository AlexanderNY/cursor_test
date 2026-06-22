FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    libnss3 \
    libglib2.0-0 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxshmfence1 \
    libasound2 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PATH=/usr/bin:$PATH

COPY dzen-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared_storage /app/shared_storage
COPY dzen-bot/ .

EXPOSE 8012

CMD ["python", "main.py"]
