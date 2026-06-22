# Анализ архитектуры и план рефакторинга

## 📋 Что реализовано в текущем коде

### 1. **Telegram функциональность**
- ✅ Сбор сообщений из Telegram каналов через Telethon
- ✅ Фильтрация сообщений по ключевым словам/фразам
- ✅ Сохранение сообщений в БД (таблица `MESSAGES`)
- ✅ Обработка сообщений (замена эмодзи, удаление фраз)
- ✅ Публикация обработанных сообщений в канал

**Функции:**
- `handler()` - обработчик новых сообщений из Telegram
- `WritetoDB_tg()` - запись сообщений в БД
- `DBprocessing_tg()` - обработка сообщений (замена символов)
- `DBposting_tg()` - публикация сообщений в канал
- `CheckDB_tg()` - проверка количества сообщений по статусу

### 2. **Twitter функциональность**
- ✅ Скрапинг Twitter/X через Selenium WebDriver
- ✅ Авторизация на Twitter
- ✅ Парсинг твитов (текст, изображения, метрики)
- ✅ Сохранение в БД (таблица `TWITTER`)
- ✅ Перевод текста с английского на русский
- ✅ Публикация твитов в Telegram канал

**Функции:**
- `getTwitterMessages()` - сбор твитов через Selenium
- `WritetoDB_tw()` - запись твитов в БД
- `DBprocessing_tw()` - обработка (перевод, очистка HTML)
- `DBposting_tw()` - публикация в Telegram
- `CheckDB_tw()` - проверка количества твитов

### 3. **Scraping функциональность**
- ✅ Сбор heatmaps с SmartLab
- ✅ Создание скриншотов элементов страницы
- ⚠️ Сбор постов с доменов (не завершено)
- ✅ Настройка Selenium с прокси поддержкой

**Функции:**
- `getHeatmap()` - сбор и публикация heatmaps
- `getDomainsPosts()` - сбор постов с доменов (заглушка)
- `get_chromedriver()` - настройка Chrome WebDriver
- `click_coords()` - клик по координатам (для доменов)

### 4. **Обработка данных**
- ✅ Замена эмодзи и символов в сообщениях
- ✅ Очистка HTML тегов
- ✅ Перевод текста (Google Translator)
- ✅ Форматирование дат

**Функции:**
- `replaceMessage()` - замена символов/эмодзи
- `clearHTML()` - очистка HTML
- `translate()` - перевод текста
- `date_format()` - форматирование дат

### 5. **База данных**
- ✅ PostgreSQL подключение
- ✅ Таблицы: `MESSAGES`, `TWITTER`, `POSTS`
- ✅ Статусы сообщений (0 - необработано, 1 - обработано, 8 - опубликовано)

### 6. **Основной цикл (Scheduler)**
- ✅ Управление таймерами для разных задач
- ✅ Проверка флагов включения/выключения функций
- ✅ Управление временными интервалами между операциями

## 🏗️ Предлагаемая архитектура микросервисов

### **Сервис 1: Telegram Service**
**Ответственность:**
- Сбор сообщений из Telegram каналов
- Публикация сообщений в Telegram каналы
- Управление Telegram клиентом

**API Endpoints:**
```
POST   /api/v1/telegram/messages/gather     - Запуск сбора сообщений
POST   /api/v1/telegram/messages/process    - Обработка сообщений
POST   /api/v1/telegram/messages/post       - Публикация сообщений
GET    /api/v1/telegram/messages/stats      - Статистика сообщений
GET    /api/v1/telegram/channels             - Список отслеживаемых каналов
POST   /api/v1/telegram/channels             - Добавить канал для отслеживания
```

**Зависимости:**
- Database Service (для сохранения сообщений)
- Message Processing Service (для обработки)

### **Сервис 2: Twitter Service**
**Ответственность:**
- Скрапинг Twitter/X через Selenium
- Парсинг твитов
- Сохранение твитов в БД

**API Endpoints:**
```
POST   /api/v1/twitter/gather                - Запуск сбора твитов
POST   /api/v1/twitter/process                - Обработка твитов
POST   /api/v1/twitter/post                   - Публикация твитов
GET    /api/v1/twitter/stats                  - Статистика твитов
GET    /api/v1/twitter/tweets                 - Список твитов
```

**Зависимости:**
- Database Service
- Scraping Service (для Selenium)
- Message Processing Service (для перевода)

### **Сервис 3: Scraping Service**
**Ответственность:**
- Управление Selenium WebDriver
- Сбор данных с веб-страниц
- Создание скриншотов
- Сбор heatmaps

**API Endpoints:**
```
POST   /api/v1/scraping/heatmap               - Сбор heatmap
POST   /api/v1/scraping/domain                 - Сбор данных с домена
POST   /api/v1/scraping/screenshot             - Создание скриншота
GET    /api/v1/scraping/drivers/status        - Статус WebDriver
```

**Зависимости:**
- Storage Service (для сохранения изображений)

### **Сервис 4: Message Processing Service**
**Ответственность:**
- Обработка текста (замена символов, очистка HTML)
- Перевод текста
- Форматирование данных

**API Endpoints:**
```
POST   /api/v1/processing/replace              - Замена символов
POST   /api/v1/processing/translate             - Перевод текста
POST   /api/v1/processing/clean-html            - Очистка HTML
POST   /api/v1/processing/format-date           - Форматирование даты
```

**Зависимости:**
- Нет (stateless сервис)

### **Сервис 5: Database Service**
**Ответственность:**
- Абстракция работы с PostgreSQL
- CRUD операции для сообщений, твитов, постов
- Управление транзакциями

**API Endpoints:**
```
POST   /api/v1/db/messages                     - Создать сообщение
GET    /api/v1/db/messages                      - Получить сообщения
PUT    /api/v1/db/messages/{id}                 - Обновить сообщение
GET    /api/v1/db/messages/stats                - Статистика сообщений

POST   /api/v1/db/twitter                       - Создать твит
GET    /api/v1/db/twitter                      - Получить твиты
PUT    /api/v1/db/twitter/{id}                 - Обновить твит
GET    /api/v1/db/twitter/stats                 - Статистика твитов

POST   /api/v1/db/posts                         - Создать пост
GET    /api/v1/db/posts                         - Получить посты
```

**Зависимости:**
- PostgreSQL

### **Сервис 6: Scheduler Service**
**Ответственность:**
- Управление расписанием задач
- Запуск периодических операций
- Управление таймерами

**API Endpoints:**
```
POST   /api/v1/scheduler/tasks                  - Создать задачу
GET    /api/v1/scheduler/tasks                  - Список задач
PUT    /api/v1/scheduler/tasks/{id}             - Обновить задачу
DELETE /api/v1/scheduler/tasks/{id}             - Удалить задачу
POST   /api/v1/scheduler/tasks/{id}/run         - Запустить задачу вручную
GET    /api/v1/scheduler/tasks/{id}/status       - Статус задачи
```

**Зависимости:**
- Все остальные сервисы (для запуска задач)

### **Сервис 7: Storage Service**
**Ответственность:**
- Хранение файлов (изображения, скриншоты)
- Управление путями к файлам
- Очистка старых файлов

**API Endpoints:**
```
POST   /api/v1/storage/upload                   - Загрузить файл
GET    /api/v1/storage/{file_id}                 - Получить файл
DELETE /api/v1/storage/{file_id}                 - Удалить файл
GET    /api/v1/storage/stats                     - Статистика хранилища
```

## 🔌 План интеграции с API Gateway

### **Этап 1: Базовая инфраструктура**

#### 1.1 Настройка API Gateway (FastAPI)
```python
# Структура проекта
api-gateway/
├── main.py                 # Точка входа API Gateway
├── routers/
│   ├── telegram.py         # Роуты для Telegram Service
│   ├── twitter.py          # Роуты для Twitter Service
│   ├── scraping.py         # Роуты для Scraping Service
│   ├── processing.py       # Роуты для Processing Service
│   ├── database.py         # Роуты для Database Service
│   └── scheduler.py        # Роуты для Scheduler Service
├── services/
│   ├── telegram_client.py  # HTTP клиент для Telegram Service
│   ├── twitter_client.py   # HTTP клиент для Twitter Service
│   └── ...                 # Клиенты для других сервисов
├── middleware/
│   ├── auth.py             # Аутентификация
│   ├── logging.py          # Логирование
│   └── rate_limit.py       # Rate limiting
└── schemas/
    └── ...                 # Pydantic схемы
```

#### 1.2 Конфигурация сервисов
```python
# config.py
SERVICES = {
    "telegram": "http://telegram-service:8001",
    "twitter": "http://twitter-service:8002",
    "scraping": "http://scraping-service:8003",
    "processing": "http://processing-service:8004",
    "database": "http://database-service:8005",
    "scheduler": "http://scheduler-service:8006",
    "storage": "http://storage-service:8007"
}
```

### **Этап 2: Реализация API Gateway**

#### 2.1 Основной файл API Gateway
- FastAPI приложение
- Подключение роутеров
- Middleware для аутентификации
- Health check endpoints
- Документация Swagger/OpenAPI

#### 2.2 HTTP клиенты для сервисов
- Асинхронные HTTP клиенты (httpx)
- Retry логика
- Error handling
- Timeout настройки

#### 2.3 Аутентификация и авторизация
- JWT токены
- API ключи
- Роли и права доступа

### **Этап 3: Рефакторинг существующего кода**

#### 3.1 Telegram Service
- Выделить Telegram функциональность
- Создать FastAPI приложение
- Реализовать endpoints
- Интегрировать с Database Service

#### 3.2 Twitter Service
- Выделить Twitter функциональность
- Создать FastAPI приложение
- Реализовать endpoints
- Интегрировать с Scraping Service и Database Service

#### 3.3 Scraping Service
- Выделить Selenium функциональность
- Создать пул WebDriver инстансов
- Реализовать endpoints для скрапинга
- Интегрировать с Storage Service

#### 3.4 Message Processing Service
- Выделить функции обработки текста
- Создать stateless FastAPI приложение
- Реализовать endpoints

#### 3.5 Database Service
- Создать абстракцию для работы с БД
- Реализовать CRUD операции
- Использовать SQLAlchemy или asyncpg
- Реализовать endpoints

#### 3.6 Scheduler Service
- Выделить логику планировщика
- Использовать Celery или APScheduler
- Реализовать endpoints для управления задачами

### **Этап 4: Интеграция и тестирование**

#### 4.1 Docker Compose
- Настройка всех сервисов в Docker
- Настройка сети между сервисами
- Настройка PostgreSQL
- Настройка Redis (для Celery, если используется)

#### 4.2 Мониторинг
- Логирование (структурированные логи)
- Метрики (Prometheus)
- Health checks
- Tracing (OpenTelemetry)

#### 4.3 Тестирование
- Unit тесты для каждого сервиса
- Integration тесты
- E2E тесты через API Gateway

### **Этап 5: Дополнительные улучшения**

#### 5.1 Очереди сообщений
- RabbitMQ или Redis для асинхронной обработки
- Отдельные очереди для каждого типа задач

#### 5.2 Кэширование
- Redis для кэширования часто запрашиваемых данных
- Кэширование результатов обработки

#### 5.3 Безопасность
- Валидация входных данных
- Rate limiting
- CORS настройки
- Защита от SQL injection

## 📊 Схема взаимодействия сервисов

```
┌─────────────────┐
│   API Gateway    │
│   (FastAPI)      │
└────────┬─────────┘
         │
         ├───► Telegram Service ──► Database Service
         │
         ├───► Twitter Service ──► Scraping Service ──► Storage Service
         │                        └─► Database Service
         │
         ├───► Scraping Service ──► Storage Service
         │
         ├───► Message Processing Service (stateless)
         │
         ├───► Database Service ──► PostgreSQL
         │
         └───► Scheduler Service ──► Все остальные сервисы
```

## 🚀 План реализации (поэтапно)

### **Фаза 1: Подготовка (1-2 недели)**
1. Создать структуру проекта для API Gateway
2. Настроить базовую инфраструктуру (Docker, PostgreSQL)
3. Создать базовые схемы данных (Pydantic models)
4. Настроить CI/CD

### **Фаза 2: Базовые сервисы (2-3 недели)**
1. Database Service - базовые CRUD операции
2. Message Processing Service - обработка текста
3. Storage Service - управление файлами

### **Фаза 3: Основные сервисы (3-4 недели)**
1. Telegram Service - сбор и публикация
2. Twitter Service - скрапинг и обработка
3. Scraping Service - Selenium функциональность

### **Фаза 4: Интеграция (2-3 недели)**
1. API Gateway - объединение всех сервисов
2. Scheduler Service - управление задачами
3. Тестирование интеграции

### **Фаза 5: Оптимизация (1-2 недели)**
1. Добавление очередей сообщений
2. Кэширование
3. Мониторинг и логирование
4. Оптимизация производительности

## 📝 Рекомендации

1. **Использовать async/await** везде для лучшей производительности
2. **Использовать Pydantic** для валидации данных
3. **Использовать SQLAlchemy Core или asyncpg** для работы с БД
4. **Использовать Celery** для фоновых задач (если нужны долгие операции)
5. **Использовать Redis** для кэширования и очередей
6. **Структурированное логирование** (structlog или loguru)
7. **Docker Compose** для локальной разработки
8. **Kubernetes** для продакшена (опционально)


