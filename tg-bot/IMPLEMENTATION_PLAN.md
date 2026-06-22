# Детальный план реализации микросервисной архитектуры

## 🎯 Цели рефакторинга

1. **Разделение ответственности** - каждый сервис отвечает за свою область
2. **Масштабируемость** - возможность масштабировать сервисы независимо
3. **Поддерживаемость** - легче тестировать и поддерживать код
4. **Гибкость** - возможность добавлять новые источники данных без изменения существующих сервисов

## 📁 Предлагаемая структура проекта

```
project-root/
├── api-gateway/                    # API Gateway сервис
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── telegram.py
│   │   │   ├── twitter.py
│   │   │   ├── scraping.py
│   │   │   └── scheduler.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── telegram_client.py
│   │   │   ├── twitter_client.py
│   │   │   └── scraping_client.py
│   │   ├── middleware/
│   │   │   ├── auth.py
│   │   │   └── logging.py
│   │   └── schemas/
│   │       ├── telegram.py
│   │       └── twitter.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── services/
│   ├── telegram-service/           # Telegram сервис
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routers/
│   │   │   │   └── messages.py
│   │   │   ├── services/
│   │   │   │   ├── telegram_client.py
│   │   │   │   └── message_processor.py
│   │   │   └── schemas/
│   │   │       └── message.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── twitter-service/            # Twitter сервис
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routers/
│   │   │   │   └── tweets.py
│   │   │   ├── services/
│   │   │   │   ├── scraper.py
│   │   │   │   └── parser.py
│   │   │   └── schemas/
│   │   │       └── tweet.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── scraping-service/           # Scraping сервис
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routers/
│   │   │   │   └── scraping.py
│   │   │   ├── services/
│   │   │   │   ├── webdriver_manager.py
│   │   │   │   └── scraper.py
│   │   │   └── schemas/
│   │   │       └── scraping.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── processing-service/         # Message Processing сервис
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routers/
│   │   │   │   └── processing.py
│   │   │   ├── services/
│   │   │   │   ├── text_processor.py
│   │   │   │   └── translator.py
│   │   │   └── schemas/
│   │   │       └── processing.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── database-service/            # Database сервис
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routers/
│   │   │   │   ├── messages.py
│   │   │   │   ├── tweets.py
│   │   │   │   └── posts.py
│   │   │   ├── services/
│   │   │   │   └── database.py
│   │   │   ├── models/
│   │   │   │   ├── message.py
│   │   │   │   ├── tweet.py
│   │   │   │   └── post.py
│   │   │   └── schemas/
│   │   │       └── database.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── scheduler-service/           # Scheduler сервис
│       ├── app/
│       │   ├── main.py
│       │   ├── config.py
│       │   ├── routers/
│       │   │   └── tasks.py
│       │   ├── services/
│       │   │   └── scheduler.py
│       │   └── schemas/
│       │       └── task.py
│       ├── requirements.txt
│       └── Dockerfile
│
├── shared/                          # Общие модули
│   ├── schemas/                     # Общие Pydantic схемы
│   └── utils/                       # Общие утилиты
│
├── docker-compose.yml               # Docker Compose конфигурация
├── .env.example                     # Пример переменных окружения
└── README.md                        # Документация проекта
```

## 🔧 Примеры реализации

### 1. API Gateway - Основной файл

```python
# api-gateway/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import telegram, twitter, scraping, scheduler
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import LoggingMiddleware

app = FastAPI(
    title="Content Aggregator API Gateway",
    description="API Gateway для управления микросервисами агрегатора контента",
    version="1.0.0"
)

# Middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(telegram.router, prefix="/api/v1/telegram", tags=["telegram"])
app.include_router(twitter.router, prefix="/api/v1/twitter", tags=["twitter"])
app.include_router(scraping.router, prefix="/api/v1/scraping", tags=["scraping"])
app.include_router(scheduler.router, prefix="/api/v1/scheduler", tags=["scheduler"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 2. API Gateway - HTTP клиент для Telegram Service

```python
# api-gateway/app/services/telegram_client.py
import httpx
from typing import Optional
from app.config import SERVICES

class TelegramServiceClient:
    def __init__(self):
        self.base_url = SERVICES["telegram"]
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
    
    async def gather_messages(self) -> dict:
        """Запуск сбора сообщений из Telegram"""
        response = await self.client.post("/messages/gather")
        response.raise_for_status()
        return response.json()
    
    async def process_messages(self) -> dict:
        """Обработка сообщений"""
        response = await self.client.post("/messages/process")
        response.raise_for_status()
        return response.json()
    
    async def post_messages(self) -> dict:
        """Публикация сообщений"""
        response = await self.client.post("/messages/post")
        response.raise_for_status()
        return response.json()
    
    async def get_stats(self) -> dict:
        """Получить статистику"""
        response = await self.client.get("/messages/stats")
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        await self.client.aclose()
```

### 3. Telegram Service - Основной файл

```python
# services/telegram-service/app/main.py
from fastapi import FastAPI
from app.routers import messages
from app.services.telegram_client import TelegramClient
from app.config import settings

app = FastAPI(title="Telegram Service")

# Инициализация Telegram клиента
telegram_client = TelegramClient(
    name=settings.TELEGRAM_NAME,
    api_id=settings.TELEGRAM_API_ID,
    api_hash=settings.TELEGRAM_API_HASH
)

app.include_router(messages.router, prefix="/messages", tags=["messages"])

@app.on_event("startup")
async def startup():
    await telegram_client.start()

@app.on_event("shutdown")
async def shutdown():
    await telegram_client.disconnect()
```

### 4. Telegram Service - Роутер

```python
# services/telegram-service/app/routers/messages.py
from fastapi import APIRouter, HTTPException, Depends
from app.services.telegram_client import TelegramClient
from app.services.database_client import DatabaseClient
from app.schemas.message import MessageCreate, MessageResponse

router = APIRouter()

@router.post("/gather")
async def gather_messages(
    telegram_client: TelegramClient = Depends(),
    db_client: DatabaseClient = Depends()
):
    """Сбор сообщений из Telegram каналов"""
    try:
        # Логика сбора сообщений
        messages = await telegram_client.gather_messages()
        
        # Сохранение в БД через Database Service
        for msg in messages:
            await db_client.create_message(MessageCreate(**msg))
        
        return {"status": "success", "count": len(messages)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process")
async def process_messages(
    db_client: DatabaseClient = Depends(),
    processing_client: ProcessingClient = Depends()
):
    """Обработка сообщений"""
    # Получить необработанные сообщения
    messages = await db_client.get_unprocessed_messages()
    
    processed_count = 0
    for msg in messages:
        # Обработка через Processing Service
        processed_text = await processing_client.replace_symbols(msg.text)
        
        # Обновление в БД
        await db_client.update_message(msg.id, {"text": processed_text, "status": 1})
        processed_count += 1
    
    return {"status": "success", "processed": processed_count}

@router.post("/post")
async def post_messages(
    telegram_client: TelegramClient = Depends(),
    db_client: DatabaseClient = Depends()
):
    """Публикация обработанных сообщений"""
    # Получить готовые к публикации сообщения
    messages = await db_client.get_ready_to_post_messages()
    
    posted_count = 0
    for msg in messages:
        # Публикация в Telegram
        await telegram_client.send_message(
            channel_id=settings.CHANNEL_TO_POST,
            text=msg.text,
            file=msg.image if msg.image else None
        )
        
        # Обновление статуса
        await db_client.update_message(msg.id, {"status": 8})
        posted_count += 1
    
    return {"status": "success", "posted": posted_count}

@router.get("/stats")
async def get_stats(db_client: DatabaseClient = Depends()):
    """Статистика сообщений"""
    stats = await db_client.get_message_stats()
    return stats
```

### 5. Database Service - Модели

```python
# services/database-service/app/models/message.py
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(String, nullable=False)
    sender_name = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    status = Column(Integer, default=0)  # 0 - необработано, 1 - обработано, 8 - опубликовано
    type = Column(Integer, default=0)
    image = Column(String, nullable=True)
    timer = Column(DateTime, default=datetime.utcnow)
```

### 6. Database Service - Сервис

```python
# services/database-service/app/services/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models.message import Message
from app.schemas.database import MessageCreate, MessageUpdate
from typing import List, Optional

class DatabaseService:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url)
        self.SessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def create_message(self, message: MessageCreate) -> Message:
        async with self.SessionLocal() as session:
            db_message = Message(**message.dict())
            session.add(db_message)
            await session.commit()
            await session.refresh(db_message)
            return db_message
    
    async def get_unprocessed_messages(self) -> List[Message]:
        async with self.SessionLocal() as session:
            result = await session.execute(
                select(Message).where(Message.status == 0, Message.type == 2)
            )
            return result.scalars().all()
    
    async def get_ready_to_post_messages(self) -> List[Message]:
        async with self.SessionLocal() as session:
            result = await session.execute(
                select(Message).where(Message.status == 1, Message.type == 2)
            )
            return result.scalars().all()
    
    async def update_message(self, message_id: int, update_data: MessageUpdate):
        async with self.SessionLocal() as session:
            result = await session.execute(
                select(Message).where(Message.id == message_id)
            )
            message = result.scalar_one_or_none()
            if message:
                for key, value in update_data.dict(exclude_unset=True).items():
                    setattr(message, key, value)
                await session.commit()
    
    async def get_message_stats(self) -> dict:
        async with self.SessionLocal() as session:
            total = await session.scalar(select(func.count(Message.id)))
            unprocessed = await session.scalar(
                select(func.count(Message.id)).where(Message.status == 0)
            )
            processed = await session.scalar(
                select(func.count(Message.id)).where(Message.status == 1)
            )
            posted = await session.scalar(
                select(func.count(Message.id)).where(Message.status == 8)
            )
            return {
                "total": total,
                "unprocessed": unprocessed,
                "processed": processed,
                "posted": posted
            }
```

### 7. Docker Compose конфигурация

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16.6
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api-gateway:
    build: ./api-gateway
    ports:
      - "8000:8000"
    environment:
      - TELEGRAM_SERVICE_URL=http://telegram-service:8001
      - TWITTER_SERVICE_URL=http://twitter-service:8002
      - DATABASE_SERVICE_URL=http://database-service:8005
    depends_on:
      - telegram-service
      - twitter-service
      - database-service

  telegram-service:
    build: ./services/telegram-service
    ports:
      - "8001:8001"
    environment:
      - DATABASE_SERVICE_URL=http://database-service:8005
      - PROCESSING_SERVICE_URL=http://processing-service:8004
    depends_on:
      - database-service
      - processing-service

  twitter-service:
    build: ./services/twitter-service
    ports:
      - "8002:8002"
    environment:
      - DATABASE_SERVICE_URL=http://database-service:8005
      - SCRAPING_SERVICE_URL=http://scraping-service:8003
      - PROCESSING_SERVICE_URL=http://processing-service:8004
    depends_on:
      - database-service
      - scraping-service
      - processing-service

  scraping-service:
    build: ./services/scraping-service
    ports:
      - "8003:8003"
    environment:
      - STORAGE_SERVICE_URL=http://storage-service:8007
    depends_on:
      - storage-service

  processing-service:
    build: ./services/processing-service
    ports:
      - "8004:8004"

  database-service:
    build: ./services/database-service
    ports:
      - "8005:8005"
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
    depends_on:
      - postgres

  scheduler-service:
    build: ./services/scheduler-service
    ports:
      - "8006:8006"
    environment:
      - API_GATEWAY_URL=http://api-gateway:8000
    depends_on:
      - api-gateway

  storage-service:
    build: ./services/storage-service
    ports:
      - "8007:8007"
    volumes:
      - storage_data:/storage

volumes:
  postgres_data:
  storage_data:
```

## 📋 Чеклист миграции

### Этап 1: Подготовка
- [ ] Создать структуру проекта
- [ ] Настроить Docker и Docker Compose
- [ ] Настроить переменные окружения
- [ ] Создать базовые Pydantic схемы

### Этап 2: Database Service
- [ ] Создать модели SQLAlchemy
- [ ] Реализовать CRUD операции
- [ ] Создать API endpoints
- [ ] Написать тесты

### Этап 3: Processing Service
- [ ] Выделить функции обработки текста
- [ ] Создать stateless API
- [ ] Реализовать endpoints
- [ ] Написать тесты

### Этап 4: Telegram Service
- [ ] Выделить Telegram функциональность
- [ ] Интегрировать с Database Service
- [ ] Интегрировать с Processing Service
- [ ] Реализовать endpoints
- [ ] Написать тесты

### Этап 5: Twitter Service
- [ ] Выделить Twitter функциональность
- [ ] Интегрировать с Scraping Service
- [ ] Интегрировать с Database Service
- [ ] Реализовать endpoints
- [ ] Написать тесты

### Этап 6: Scraping Service
- [ ] Выделить Selenium функциональность
- [ ] Создать пул WebDriver
- [ ] Реализовать endpoints
- [ ] Написать тесты

### Этап 7: API Gateway
- [ ] Создать основное приложение
- [ ] Реализовать HTTP клиенты
- [ ] Создать роутеры
- [ ] Настроить middleware
- [ ] Написать тесты

### Этап 8: Scheduler Service
- [ ] Реализовать планировщик задач
- [ ] Интегрировать с другими сервисами
- [ ] Реализовать endpoints
- [ ] Написать тесты

### Этап 9: Интеграция
- [ ] Настроить Docker Compose
- [ ] Протестировать интеграцию
- [ ] Настроить мониторинг
- [ ] Настроить логирование

### Этап 10: Документация
- [ ] Написать README для каждого сервиса
- [ ] Обновить общую документацию
- [ ] Создать примеры использования API


