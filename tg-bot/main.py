"""Главный файл для запуска Telegram бота с FastAPI сервером."""

import asyncio
import logging
import signal
import sys
from fastapi import FastAPI
import uvicorn
from database import init_db, close_db
from game_schema import GAME_TABLE_DDL
from tg_profiles_migration import TG_PROFILES_ALERT_MIGRATION
from services.telegram_bot_service import TelegramBotService
from services.client_manager import TelegramClientManager
from routers.auth import router as auth_router, set_client_manager
from routers.channels import router as channels_router, set_client_manager as set_channels_client_manager
from routers.game_admin import router as game_admin_router
from routers.game_rating import router as game_rating_router
from config import settings


# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)

# FastAPI приложение
app = FastAPI(title="Telegram Bot Service", version="1.0.0")

# Подключение роутеров
app.include_router(auth_router, prefix="/tg")
app.include_router(channels_router, prefix="/tg")
app.include_router(game_rating_router, prefix="/tg/game")
app.include_router(game_admin_router, prefix="/tg/game")

# Глобальные переменные
bot_service: TelegramBotService = None
client_manager: TelegramClientManager = None
_reload_task = None
_game_poll_task: asyncio.Task | None = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    return {"status": "ok", "service": "tg-bot", "server_time": datetime.utcnow().isoformat() + "Z"}


@app.post("/tg/reload")
async def reload_profiles():
    """Перезагружает профили и клиенты. Запускается в фоне."""
    global bot_service
    if not bot_service:
        return {"status": "error", "message": "Bot service not initialized"}
    asyncio.create_task(bot_service.reload())
    return {"status": "ok", "message": "Reload started"}


async def run_api_server():
    """Запуск FastAPI сервера."""
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
    server = uvicorn.Server(config)
    await server.serve()


def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown."""
    logger.info(f"Received signal {signum}, shutting down...")
    if bot_service:
        asyncio.create_task(bot_service.stop())
    sys.exit(0)


async def _reload_loop():
    """Фоновая задача периодической перезагрузки профилей."""
    interval = settings.RELOAD_PROFILES_INTERVAL_SEC
    if interval <= 0:
        return
    while True:
        await asyncio.sleep(interval)
        if bot_service and bot_service.is_running():
            try:
                logger.info("Scheduled profile reload...")
                await bot_service.reload()
            except Exception as e:
                logger.error(f"Error in scheduled reload: {e}", exc_info=True)


async def main():
    """Основная функция запуска бота."""
    global bot_service, client_manager, _reload_task, _game_poll_task
    
    try:
        logger.info("Initializing Telegram Bot...")
        
        # Инициализация БД: игровые таблицы + миграции tg_profiles (alerting)
        logger.info("Initializing database...")
        await init_db(TG_PROFILES_ALERT_MIGRATION + GAME_TABLE_DDL)
        logger.info("Database initialized")
        
        # Создание менеджера клиентов
        client_manager = TelegramClientManager()
        set_client_manager(client_manager)
        set_channels_client_manager(client_manager)
        
        # Создание и запуск бота
        bot_service = TelegramBotService()
        bot_service.client_manager = client_manager
        
        # Запуск API сервера в фоне
        logger.info(f"Starting API server on port {settings.API_PORT}...")
        api_task = asyncio.create_task(run_api_server())
        
        # Небольшая задержка для запуска API сервера
        await asyncio.sleep(1)
        
        # Запуск бота
        await bot_service.start()

        game_token = (settings.GAME_BOT_TOKEN or "").strip()
        if game_token:
            from bots.game_bot_runner import run_game_bot_polling

            _game_poll_task = asyncio.create_task(run_game_bot_polling(game_token))
            logger.info("Game bot (aiogram) polling task started.")
        
        # Запуск фоновой задачи перезагрузки профилей
        if settings.RELOAD_PROFILES_INTERVAL_SEC > 0:
            _reload_task = asyncio.create_task(_reload_loop())
        
        logger.info("Telegram Bot is running. Press Ctrl+C to stop.")
        
        # Ожидание завершения (бесконечный цикл)
        try:
            await asyncio.gather(api_task)
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt, shutting down...")
    
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        raise
    
    finally:
        if _game_poll_task:
            _game_poll_task.cancel()
            try:
                await _game_poll_task
            except asyncio.CancelledError:
                pass
            _game_poll_task = None
        # Остановка задачи перезагрузки
        if _reload_task:
            _reload_task.cancel()
            try:
                await _reload_task
            except asyncio.CancelledError:
                pass
        # Остановка бота и закрытие БД
        if bot_service:
            await bot_service.stop()
        if client_manager:
            await client_manager.stop_all_clients()
        await close_db()
        logger.info("Telegram Bot stopped")


if __name__ == '__main__':
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Запуск бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
