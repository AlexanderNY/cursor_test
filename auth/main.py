from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db, close_db
from routers import profile, auth, security, groups, billing


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Обработчики событий жизненного цикла приложения."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="Auth Service",
    description="Микросервис авторизации и аутентификации",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(groups.router)
app.include_router(security.router)
app.include_router(billing.router)


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "service": "Auth Service API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса."""
    return {
        "status": "healthy",
        "service": "auth",
        "server_time": datetime.utcnow().isoformat() + "Z",
    }


