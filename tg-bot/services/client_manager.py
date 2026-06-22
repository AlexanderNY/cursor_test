"""Управление Telegram клиентами для разных пользователей."""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional
from telethon import TelegramClient
from telethon.errors import (
    PhoneNumberInvalidError,
    FloodWaitError
)
from database import get_db_connection, release_db_connection
from config import settings
from .notification_service import notification_service


logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    """Логирует действие бота при LOG_BOT_ACTIONS."""
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


class TelegramClientManager:
    """Управление множественными TelegramClient для разных пользователей."""
    
    def __init__(self):
        """Инициализация менеджера клиентов."""
        self._clients: Dict[int, TelegramClient] = {}
        self._profiles: Dict[int, Dict] = {}
        self._pending_clients: Dict[int, TelegramClient] = {}  # Клиенты ожидающие авторизации
    
    async def load_profiles(self) -> List[Dict]:
        """Загружает профили из БД (collect_enabled или publish_enabled).

        Returns:
            Список профилей для сбора и/или публикации
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT * FROM tg_profiles
                    WHERE (collect_enabled = TRUE OR publish_enabled = TRUE OR alert_enabled = TRUE)
                      AND api_id IS NOT NULL
                      AND api_hash IS NOT NULL
                    """
                )
                rows = await cur.fetchall()
                
                if not rows:
                    _log_action("No profiles with collect_enabled or publish_enabled found")
                    return []
                
                # Преобразуем строки в словари
                columns = [col.name for col in cur.description]
                profiles = []
                for row in rows:
                    profile = dict(zip(columns, row))
                    # Парсим JSONB поля
                    if isinstance(profile.get('chats_to_read'), str):
                        try:
                            profile['chats_to_read'] = json.loads(profile['chats_to_read'])
                        except (json.JSONDecodeError, TypeError):
                            profile['chats_to_read'] = []
                    if isinstance(profile.get('save_conditions'), str):
                        try:
                            profile['save_conditions'] = json.loads(profile['save_conditions'])
                        except (json.JSONDecodeError, TypeError):
                            profile['save_conditions'] = []
                    if isinstance(profile.get('alert_rules'), str):
                        try:
                            profile['alert_rules'] = json.loads(profile['alert_rules'])
                        except (json.JSONDecodeError, TypeError):
                            profile['alert_rules'] = []
                    elif not isinstance(profile.get('alert_rules'), list):
                        profile['alert_rules'] = []
                    profile.setdefault('alert_enabled', False)
                    profiles.append(profile)
                
                _log_action("Loaded %d profiles for collect/publish", len(profiles))
                return profiles
        finally:
            await release_db_connection(conn)
    
    async def _update_auth_state(
        self,
        user_id: int,
        auth_state: str,
        phone_code_hash: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> None:
        """Обновляет состояние авторизации в БД.
        
        Args:
            user_id: ID пользователя
            auth_state: Новое состояние авторизации
            phone_code_hash: Хеш кода (опционально)
            phone_number: Номер телефона (опционально)
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                updates = ["auth_state = %s", "updated_at = CURRENT_TIMESTAMP"]
                params = [auth_state]
                
                if phone_code_hash is not None:
                    updates.append("auth_phone_code_hash = %s")
                    h = phone_code_hash
                    params.append(
                        h.decode("utf-8", errors="replace") if isinstance(h, bytes) else str(h)
                    )
                
                if phone_number is not None:
                    updates.append("auth_phone_number = %s")
                    p = phone_number
                    params.append(
                        p.decode("utf-8", errors="replace") if isinstance(p, bytes) else str(p)
                    )
                
                params.append(user_id)
                
                await cur.execute(
                    f"""
                    UPDATE tg_profiles
                    SET {', '.join(updates)}
                    WHERE user_id = %s
                    """,
                    params
                )
        finally:
            await release_db_connection(conn)
    
    async def _request_authorization_code(
        self,
        client: TelegramClient,
        phone_number: str,
        user_id: int
    ) -> Optional[str]:
        """Запрашивает код авторизации у Telegram.

        Args:
            client: TelegramClient для запроса кода
            phone_number: Номер телефона в международном формате
            user_id: ID пользователя

        Returns:
            phone_code_hash или None в случае ошибки
        """
        if not phone_number or not isinstance(phone_number, (str, bytes)):
            logger.error(f"Invalid phone_number for user {user_id}: {phone_number!r}")
            await self._update_auth_state(user_id, auth_state='failed')
            return None
        phone_number = str(phone_number).strip()
        if not phone_number:
            logger.error(f"Empty phone_number for user {user_id}")
            await self._update_auth_state(user_id, auth_state='failed')
            return None

        try:
            # Telethon требует str для phone
            phone_str = phone_number if isinstance(phone_number, str) else str(phone_number)
            result = await client.send_code_request(phone_str)
            phone_code_hash = result.phone_code_hash
            if not isinstance(phone_code_hash, (str, bytes)):
                phone_code_hash = str(phone_code_hash) if phone_code_hash is not None else None
            elif isinstance(phone_code_hash, bytes):
                phone_code_hash = phone_code_hash.decode("utf-8", errors="replace")

            # Сохраняем в БД
            await self._update_auth_state(
                user_id,
                auth_state='pending_code',
                phone_code_hash=phone_code_hash,
                phone_number=phone_str
            )
            
            # Отправляем уведомление пользователю
            await notification_service.send_authorization_notification(
                user_id,
                phone_str
            )
            
            logger.info(f"Authorization code requested for user {user_id}")
            return phone_code_hash
        
        except PhoneNumberInvalidError:
            logger.error(f"Invalid phone number for user {user_id}")
            await notification_service.send_error_notification(
                user_id,
                "Неверный номер телефона. Проверьте номер и попробуйте снова."
            )
            await self._update_auth_state(user_id, auth_state='failed')
            return None
        
        except FloodWaitError as e:
            logger.warning(f"FloodWait error for user {user_id}: {e.seconds} seconds")
            await notification_service.send_error_notification(
                user_id,
                f"Слишком много запросов. Попробуйте через {e.seconds} секунд."
            )
            return None
        
        except Exception as e:
            err_msg = str(e) if e else repr(e)
            logger.error(
                "Error requesting authorization code for user %s: %s",
                user_id, err_msg, exc_info=True
            )
            # Сообщение для пользователя — без технических деталей, если они нечитаемы
            user_msg = (
                err_msg
                if err_msg and len(err_msg) < 200 and "bytes or str" not in err_msg
                else "Ошибка при запросе кода. Проверьте номер телефона (формат +79001234567) и API credentials."
            )
            await notification_service.send_error_notification(user_id, user_msg)
            return None

    @staticmethod
    def _is_valid_phone_number(phone: str) -> bool:
        """Проверяет, что строка похожа на номер телефона (не username)."""
        if not phone or len(phone) < 10:
            return False
        clean = phone.lstrip('+')
        return clean.isdigit()

    async def _create_client_with_retry(self, profile: Dict) -> Optional[TelegramClient]:
        """Создает клиент с повторными попытками при FloodWait."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return await self.create_client(profile)
            except FloodWaitError as e:
                wait_sec = min(e.seconds, 60) * (2 ** attempt)
                logger.warning(
                    "FloodWait for user %s: waiting %s sec (attempt %d/%d)",
                    profile.get("user_id"), wait_sec, attempt + 1, max_retries
                )
                await asyncio.sleep(wait_sec)
        return None

    async def create_client(self, profile: Dict) -> Optional[TelegramClient]:
        """Создает TelegramClient для профиля.
        
        Args:
            profile: Словарь с данными профиля из БД
            
        Returns:
            TelegramClient или None в случае ошибки или необходимости авторизации
        """
        user_id = profile['user_id']
        api_id = profile.get('api_id')
        api_hash = profile.get('api_hash')
        auth_state = profile.get('auth_state', 'authorized')

        try:
            api_id = int(api_id) if api_id is not None else None
        except (ValueError, TypeError):
            api_id = None
        if api_hash is not None:
            api_hash = (
                api_hash.decode("utf-8", errors="replace")
                if isinstance(api_hash, bytes)
                else str(api_hash)
            ).strip()
        else:
            api_hash = None

        if not api_id or not api_hash:
            logger.warning(f"Profile {user_id} missing api_id or api_hash")
            return None

        try:
            # Создаем директорию для сессий если её нет
            os.makedirs('sessions', exist_ok=True)

            # Создаем клиент с уникальным именем сессии для каждого пользователя
            session_name = f'sessions/tg_session_{user_id}'
            client = TelegramClient(
                session_name,
                api_id,
                api_hash,
                system_version="4.16.30-vxASPA"
            )
            
            # Подключаемся к Telegram
            try:
                await client.connect()
            except FloodWaitError:
                raise
            except Exception as e:
                logger.error(f"Error connecting client for user {user_id}: {e}")
                return None
            
            # Проверяем авторизацию
            try:
                if not await client.is_user_authorized():
                    # Клиент не авторизован — запрашиваем код независимо
                    # от текущего auth_state (код мог протухнуть после
                    # перезапуска контейнера)
                    if auth_state == 'pending_password':
                        # 2FA ожидает пароль — код уже был принят,
                        # просто ждём пароль от пользователя
                        self._pending_clients[user_id] = client
                        return None

                    raw_phone = profile.get('auth_phone_number')
                    phone_number = None
                    if raw_phone is not None:
                        if isinstance(raw_phone, bytes):
                            phone_number = raw_phone.decode("utf-8", errors="replace").strip().lstrip("@")
                        else:
                            phone_number = str(raw_phone).strip().lstrip("@")
                        if not phone_number:
                            phone_number = None

                    if phone_number and self._is_valid_phone_number(phone_number):
                        phone_code_hash = await self._request_authorization_code(
                            client, phone_number, user_id
                        )
                        if phone_code_hash:
                            # Сохраняем клиент для последующей авторизации
                            self._pending_clients[user_id] = client
                            return None
                        else:
                            # send_code_request не удался
                            self._pending_clients[user_id] = client
                            return None
                    else:
                        logger.warning(
                            f"No valid phone number for user {user_id}. "
                            "Set auth_phone_number in tg_profiles (e.g. +79001234567)"
                        )
                        await self._update_auth_state(user_id, auth_state='failed')
                        await client.disconnect()
                        return None
                
                # Клиент авторизован
                _log_action("Created and connected client for user %s", user_id)
                return client
            
            except FloodWaitError:
                try:
                    await client.disconnect()
                except Exception:
                    pass
                raise
            except Exception as e:
                logger.error(f"Error checking authorization for user {user_id}: {e}")
                try:
                    await client.disconnect()
                except Exception:
                    pass
                return None
            
        except FloodWaitError:
            raise
        except Exception as e:
            logger.error(f"Error creating client for user {user_id}: {e}", exc_info=True)
            return None
    
    def get_pending_client(self, user_id: int) -> Optional[TelegramClient]:
        """Получает клиент ожидающий авторизации.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            TelegramClient или None
        """
        return self._pending_clients.get(user_id)
    
    def move_client_to_active(self, user_id: int) -> None:
        """Перемещает клиент из pending в active после успешной авторизации.
        
        Args:
            user_id: ID пользователя
        """
        if user_id in self._pending_clients:
            client = self._pending_clients.pop(user_id)
            self._clients[user_id] = client
            _log_action("Moved client for user %s to active", user_id)
    
    async def start_all_clients(self) -> None:
        """Запускает все клиенты для профилей с collect_enabled/publish_enabled.
        
        Профили с collect_enabled имеют приоритет. Клиенты создаются батчами
        с задержкой между батчами. Ограничение MAX_CONCURRENT_CLIENTS.
        """
        profiles = await self.load_profiles()
        if not profiles:
            return

        # Приоритизация: collect_enabled, alert_enabled, publish_enabled
        def _priority(p: Dict) -> int:
            c = 1 if p.get("collect_enabled") else 0
            a = 1 if p.get("alert_enabled") else 0
            p_en = 1 if p.get("publish_enabled") else 0
            return c * 4 + a * 2 + p_en

        profiles = sorted(profiles, key=_priority, reverse=True)

        batch_size = settings.CLIENT_BATCH_SIZE
        batch_delay = settings.CLIENT_BATCH_DELAY_SEC
        max_clients = settings.MAX_CONCURRENT_CLIENTS

        total = len(self._clients) + len(self._pending_clients)
        for i in range(0, len(profiles), batch_size):
            batch = profiles[i : i + batch_size]
            for profile in batch:
                if max_clients > 0 and total >= max_clients:
                    _log_action(
                        "Reached MAX_CONCURRENT_CLIENTS=%d, skipping remaining profiles",
                        max_clients,
                    )
                    return

                user_id = profile["user_id"]
                if user_id in self._clients or user_id in self._pending_clients:
                    _log_action("Client for user %s already exists, skipping", user_id)
                    continue

                client = await self._create_client_with_retry(profile)
                if client:
                    self._clients[user_id] = client
                    self._profiles[user_id] = profile
                    total += 1
                    _log_action("Started client for user %s", user_id)
                else:
                    self._profiles[user_id] = profile
                    total += 1
                    _log_action("Client for user %s pending authorization", user_id)

            if i + batch_size < len(profiles) and batch_delay > 0:
                await asyncio.sleep(batch_delay)

        _log_action(
            "Clients: %d active, %d pending",
            len(self._clients),
            len(self._pending_clients),
        )

    async def stop_all_clients(self) -> None:
        """Останавливает все клиенты."""
        for user_id, client in list(self._clients.items()):
            try:
                await client.disconnect()
                _log_action("Stopped client for user %s", user_id)
            except Exception as e:
                logger.error(f"Error stopping client for user {user_id}: {e}")
        
        for user_id, client in list(self._pending_clients.items()):
            try:
                await client.disconnect()
                _log_action("Stopped pending client for user %s", user_id)
            except Exception as e:
                logger.error(f"Error stopping pending client for user {user_id}: {e}")
        
        self._clients.clear()
        self._pending_clients.clear()
        self._profiles.clear()
    
    async def reload_clients(self) -> None:
        """Перезагружает клиенты при изменении профилей."""
        logger.info("Reloading clients...")
        await self.stop_all_clients()
        await self.start_all_clients()
    
    def get_client(self, user_id: int) -> Optional[TelegramClient]:
        """Получает клиент для пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            TelegramClient или None
        """
        return self._clients.get(user_id)
    
    def get_profile(self, user_id: int) -> Optional[Dict]:
        """Получает профиль пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Профиль или None
        """
        return self._profiles.get(user_id)
    
    def get_all_clients(self) -> Dict[int, TelegramClient]:
        """Возвращает все активные клиенты.
        
        Returns:
            Словарь {user_id: TelegramClient}
        """
        return self._clients.copy()
