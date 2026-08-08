Каждый сервис должен иметь конфигурационный файл config.py

# Service URL (не секреты — допустимы дефолты в коде)
    API_GATEWAY_SERVICE_URL: str = "http://localhost:8000"
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    CORE_SERVICE_URL: str = "http://localhost:8002"
    SCHEDULER_SERVICE_URL: str = "http://localhost:8003"
    TG_BOT_SERVICE_URL: str = "http://localhost:8004"
    VK_BOT_SERVICE_URL: str = "http://localhost:8005"
    WP_BOT_SERVICE_URL: str = "http://localhost:8006"
    URL_BOT_SERVICE_URL: str = "http://localhost:8007"

# CORS (только api-gateway; внутренние сервисы без CORS middleware)
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8100"  # список через запятую в env
    # Новый домен UI → добавить origin в CORS_ORIGINS (compose/K8s), без правок кода.

# Secrets — НЕ хранить в коде и НЕ коммитить
# Локально: cp .env.example .env и заполнить значения.
# Docker Compose: подставляет ${DATABASE_URL}, ${JWT_SECRET_KEY}, ${SECRET_KEY}, ${S3_SECRET_KEY} из .env.
# K8s: k8s/base/secret.yaml (из secret.yaml.example), не коммитить.
#
# В config.py дефолты пустые:
    DATABASE_URL: str = ""
    JWT_SECRET_KEY: str = ""   # gateway, core — openssl rand -hex 32 (без символа $)
    SECRET_KEY: str = ""       # auth — должен совпадать с JWT_SECRET_KEY
# Docker Compose интерполирует $VAR в .env: не кладите bcrypt ($2b$12$...) как JWT.
# Ротация после утечки в git:
#   1) сменить пароль PostgreSQL
#   2) openssl rand -hex 32 → новый JWT / SECRET_KEY
#   3) обновить .env и K8s Secret (старые токены станут невалидны)
