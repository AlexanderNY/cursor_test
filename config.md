Каждый сервис должен иметь конфигурационный файл config.py
# Service URL
    API_GATEWAY_SERVICE_URL: str = "http://localhost:8000"
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    CORE_SERVICE_URL: str = "http://localhost:8002"
    SCHEDULER_SERVICE_URL: str = "http://localhost:8003"
    TG_BOT_SERVICE_URL: str = "http://localhost:8004"
    VK_BOT_SERVICE_URL: str = "http://localhost:8005"
    WP_BOT_SERVICE_URL: str = "http://localhost:8006"
    URL_BOT_SERVICE_URL: str = "http://localhost:8007"
# CORS    
    CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","http://localhost:8001", "http://localhost:8002"]
# JWT Settings
    JWT_SECRET_KEY: str ="$2b$12$xyiAcpacCfrFN3wl3ayJT."
    ALGORITHM: str = "HS256"
# Database
    DATABASE_URL: str = 'dbname=db_bot user=postgres password=1qaz!QAZ host=127.0.0.1' #postgresql://localhost:5432/postgres'

