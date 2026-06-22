FROM python:3.12-slim

WORKDIR /app

# 1. Установка Chromium, драйвера и обязательных зависимостей
# Используем одну команду RUN для минимизации слоев
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    # Зависимости для работы Chromium в headless-режиме:
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

# 2. Настройка переменных окружения (отдельные инструкции)
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
# Важно для Selenium 4+:
ENV PATH=/usr/bin:$PATH

COPY url-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY url-bot/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]