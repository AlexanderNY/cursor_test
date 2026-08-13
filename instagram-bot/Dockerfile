FROM python:3.12-slim

WORKDIR /app

# Chromium + chromedriver для Selenium fallback (как url-bot); retries for flaky mirrors
RUN printf 'Acquire::Retries "5";\nAcquire::http::Timeout "30";\nAcquire::https::Timeout "30";\n' \
      > /etc/apt/apt.conf.d/80-retries \
 && apt-get update && apt-get install -y --no-install-recommends \
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

# Контекст сборки — корень репозитория (см. docker-compose: context: .)
COPY instagram-bot/requirements.txt ./requirements.txt
ENV PIP_DEFAULT_TIMEOUT=300
RUN pip install --no-cache-dir -r requirements.txt

COPY shared_storage /app/shared_storage
COPY shared /app/shared
COPY instagram-bot/ .

EXPOSE 8011

CMD ["python", "main.py"]
