"""Сервис для управления профилями пользователей."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection


def _instagram_session_is_non_empty(raw: Any) -> bool:
    """True если в БД есть нетривиальная сессия instagrapi (JSONB dict)."""
    if raw is None:
        return False
    if isinstance(raw, dict):
        return len(raw) > 0
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            return isinstance(data, dict) and len(data) > 0
        except (json.JSONDecodeError, TypeError):
            return False
    return False


class ProfileService:
    """Сервис для CRUD операций с профилями всех платформ."""
    
    # ==================== Telegram ====================
    
    async def get_tg_profile(self, user_id: int) -> Optional[Dict]:
        """Получает профиль Telegram пользователя."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM tg_profiles WHERE user_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_tg_profile(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)
    
    async def save_tg_profile(self, user_id: int, data: Dict) -> Dict:
        """Сохраняет или обновляет профиль Telegram."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                process_services = data.get("process_services")
                if process_services is not None:
                    process_services_json = json.dumps(process_services) if isinstance(process_services, list) else None
                else:
                    process_services_json = None
                
                alert_rules = data.get("alert_rules", [])
                alert_rules_json = json.dumps(alert_rules) if isinstance(alert_rules, list) else "[]"

                await cur.execute(
                    """
                    INSERT INTO tg_profiles (
                        user_id, publish_enabled, collect_enabled, schedule_type,
                        time_intervals, api_id, api_hash, telegram_username, auth_phone_number,
                        chats_to_read, save_conditions, channel_to_post, alert_enabled, alert_rules,
                        process_enabled, processing_description, remove_emojis, remove_images,
                        clean_html, process_services, status_review_after_process,
                        add_static_html, static_html_content
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        publish_enabled = EXCLUDED.publish_enabled,
                        collect_enabled = EXCLUDED.collect_enabled,
                        schedule_type = EXCLUDED.schedule_type,
                        time_intervals = EXCLUDED.time_intervals,
                        api_id = EXCLUDED.api_id,
                        api_hash = EXCLUDED.api_hash,
                        telegram_username = EXCLUDED.telegram_username,
                        auth_phone_number = EXCLUDED.auth_phone_number,
                        chats_to_read = EXCLUDED.chats_to_read,
                        save_conditions = EXCLUDED.save_conditions,
                        channel_to_post = EXCLUDED.channel_to_post,
                        alert_enabled = EXCLUDED.alert_enabled,
                        alert_rules = EXCLUDED.alert_rules,
                        process_enabled = EXCLUDED.process_enabled,
                        processing_description = EXCLUDED.processing_description,
                        remove_emojis = EXCLUDED.remove_emojis,
                        remove_images = EXCLUDED.remove_images,
                        clean_html = EXCLUDED.clean_html,
                        process_services = EXCLUDED.process_services,
                        status_review_after_process = EXCLUDED.status_review_after_process,
                        add_static_html = EXCLUDED.add_static_html,
                        static_html_content = EXCLUDED.static_html_content,
                        auth_state = 'authorized',
                        auth_phone_code_hash = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING *
                    """,
                    (
                        user_id,
                        data.get("publish_enabled", False),
                        data.get("collect_enabled", False),
                        data.get("schedule_type", "immediate"),
                        json.dumps(data.get("time_intervals", [])),
                        data.get("api_id"),
                        data.get("api_hash"),
                        data.get("telegram_username"),
                        data.get("auth_phone_number"),
                        json.dumps(data.get("chats_to_read", [])),
                        json.dumps(data.get("save_conditions", [])),
                        data.get("channel_to_post"),
                        data.get("alert_enabled", False),
                        alert_rules_json,
                        data.get("process_enabled", False),
                        data.get("processing_description"),
                        data.get("remove_emojis", False),
                        data.get("remove_images", False),
                        data.get("clean_html", False),
                        process_services_json,
                        data.get("status_review_after_process", False),
                        data.get("add_static_html", False),
                        data.get("static_html_content"),
                    )
                )
                row = await cur.fetchone()
                return self._row_to_tg_profile(row, cur.description)
        finally:
            await release_db_connection(conn)
    
    def _row_to_tg_profile(self, row, description) -> Dict:
        """Преобразует строку БД в словарь профиля Telegram."""
        columns = [col.name for col in description]
        profile = dict(zip(columns, row))
        # Парсим JSON поля
        if isinstance(profile.get("time_intervals"), str):
            profile["time_intervals"] = json.loads(profile["time_intervals"])
        if isinstance(profile.get("chats_to_read"), str):
            profile["chats_to_read"] = json.loads(profile["chats_to_read"])
        if isinstance(profile.get("save_conditions"), str):
            profile["save_conditions"] = json.loads(profile["save_conditions"])
        if isinstance(profile.get("alert_rules"), str):
            try:
                profile["alert_rules"] = json.loads(profile["alert_rules"])
            except (json.JSONDecodeError, TypeError):
                profile["alert_rules"] = []
        elif not isinstance(profile.get("alert_rules"), list):
            profile["alert_rules"] = []
        # Парсим process_services
        ps = profile.get("process_services")
        if ps is not None and isinstance(ps, str):
            try:
                profile["process_services"] = json.loads(ps)
            except (json.JSONDecodeError, TypeError):
                profile["process_services"] = []
        elif not isinstance(profile.get("process_services"), list):
            profile["process_services"] = []
        # Устанавливаем значения по умолчанию для новых полей
        profile.setdefault("remove_emojis", False)
        profile.setdefault("remove_images", False)
        profile.setdefault("clean_html", False)
        profile.setdefault("alert_enabled", False)
        profile.setdefault("alert_rules", [])
        profile.setdefault("status_review_after_process", False)
        profile.setdefault("add_static_html", False)
        return profile
    
    # ==================== Threads ====================
    
    async def get_threads_profile(self, user_id: int) -> Optional[Dict]:
        """Получает профиль Threads пользователя."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM threads_profiles WHERE user_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_threads_profile(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)
    
    async def save_threads_profile(self, user_id: int, data: Dict) -> Dict:
        """Сохраняет или обновляет профиль Threads (без записи токенов)."""
        if "instagram_handle" not in data:
            existing = await self.get_threads_profile(user_id)
            if existing is not None:
                data = {**data, "instagram_handle": existing.get("instagram_handle")}
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                process_services = data.get("process_services")
                process_services_json = json.dumps(process_services) if isinstance(process_services, list) else None
                await cur.execute(
                    """
                    INSERT INTO threads_profiles (
                        user_id, instagram_handle, publish_enabled, collect_enabled, schedule_type,
                        time_intervals, process_enabled, processing_description,
                        remove_emojis, remove_images, clean_html, process_services,
                        status_review_after_process, add_static_html, static_html_content
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        instagram_handle = EXCLUDED.instagram_handle,
                        publish_enabled = EXCLUDED.publish_enabled,
                        collect_enabled = EXCLUDED.collect_enabled,
                        schedule_type = EXCLUDED.schedule_type,
                        time_intervals = EXCLUDED.time_intervals,
                        process_enabled = EXCLUDED.process_enabled,
                        processing_description = EXCLUDED.processing_description,
                        remove_emojis = EXCLUDED.remove_emojis,
                        remove_images = EXCLUDED.remove_images,
                        clean_html = EXCLUDED.clean_html,
                        process_services = EXCLUDED.process_services,
                        status_review_after_process = EXCLUDED.status_review_after_process,
                        add_static_html = EXCLUDED.add_static_html,
                        static_html_content = EXCLUDED.static_html_content,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING *
                    """,
                    (
                        user_id,
                        (data.get("instagram_handle") or "").strip() or None,
                        data.get("publish_enabled", False),
                        data.get("collect_enabled", False),
                        data.get("schedule_type", "immediate"),
                        json.dumps(data.get("time_intervals", [])),
                        data.get("process_enabled", False),
                        data.get("processing_description"),
                        data.get("remove_emojis", False),
                        data.get("remove_images", False),
                        data.get("clean_html", False),
                        process_services_json,
                        data.get("status_review_after_process", False),
                        data.get("add_static_html", False),
                        data.get("static_html_content"),
                    )
                )
                row = await cur.fetchone()
                return self._row_to_threads_profile(row, cur.description)
        finally:
            await release_db_connection(conn)
    
    async def save_threads_oauth_tokens(
        self,
        user_id: int,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[Any] = None,
        threads_user_id: Optional[str] = None,
    ) -> None:
        """Сохраняет OAuth токены Threads после callback (обновляет существующий профиль или создает минимальный)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO threads_profiles (user_id, access_token, refresh_token, token_expires_at, threads_user_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        access_token = EXCLUDED.access_token,
                        refresh_token = EXCLUDED.refresh_token,
                        token_expires_at = EXCLUDED.token_expires_at,
                        threads_user_id = EXCLUDED.threads_user_id,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (user_id, access_token, refresh_token, token_expires_at, threads_user_id),
                )
        finally:
            await release_db_connection(conn)
    
    def _row_to_threads_profile(self, row, description) -> Dict:
        """Преобразует строку БД в словарь профиля Threads (токены не отдаем)."""
        columns = [col.name for col in description]
        profile = dict(zip(columns, row))
        if isinstance(profile.get("time_intervals"), str):
            try:
                profile["time_intervals"] = json.loads(profile["time_intervals"])
            except (json.JSONDecodeError, TypeError):
                profile["time_intervals"] = []
        ps = profile.get("process_services")
        if ps is not None and isinstance(ps, str):
            try:
                profile["process_services"] = json.loads(ps)
            except (json.JSONDecodeError, TypeError):
                profile["process_services"] = []
        elif not isinstance(profile.get("process_services"), list):
            profile["process_services"] = []
        profile["threads_connected"] = bool(profile.get("access_token"))
        profile.setdefault("instagram_handle", None)
        if "access_token" in profile:
            del profile["access_token"]
        if "refresh_token" in profile:
            del profile["refresh_token"]
        return profile
    
    async def get_all_threads_profiles(self) -> List[Dict]:
        """Получает все профили Threads (для админки, без токенов)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM threads_profiles")
                rows = await cur.fetchall()
                return [self._row_to_threads_profile(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)
    
    async def get_threads_profile_with_token(self, user_id: int) -> Optional[Dict]:
        """Получает профиль Threads с access_token для th-bot (внутренний вызов)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM threads_profiles WHERE user_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                if not row:
                    return None
                columns = [col.name for col in cur.description]
                profile = dict(zip(columns, row))
                if isinstance(profile.get("time_intervals"), str):
                    try:
                        profile["time_intervals"] = json.loads(profile["time_intervals"])
                    except (json.JSONDecodeError, TypeError):
                        profile["time_intervals"] = []
                ps = profile.get("process_services")
                if ps is not None and isinstance(ps, str):
                    try:
                        profile["process_services"] = json.loads(ps)
                    except (json.JSONDecodeError, TypeError):
                        profile["process_services"] = []
                return profile
        finally:
            await release_db_connection(conn)
    
    # ==================== Twitter ====================
    
    async def get_tw_profile(self, user_id: int) -> Optional[Dict]:
        """Получает профиль Twitter пользователя."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM tw_profiles WHERE user_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_tw_profile(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)
    
    async def save_tw_profile(self, user_id: int, data: Dict) -> Dict:
        """Сохраняет или обновляет профиль Twitter."""
        pwd = data.get("twitter_password")
        if pwd in (None, "", "***"):
            pwd = None
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                if pwd is None:
                    await cur.execute(
                        """
                        INSERT INTO tw_profiles (
                            user_id, publish_enabled, collect_enabled, schedule_type,
                            time_intervals, use_proxy, proxy_user, proxy_pass,
                            proxy_host, proxy_port, twitter_username,
                            take_screenshot_collect, screenshot_xpath
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            publish_enabled = EXCLUDED.publish_enabled,
                            collect_enabled = EXCLUDED.collect_enabled,
                            schedule_type = EXCLUDED.schedule_type,
                            time_intervals = EXCLUDED.time_intervals,
                            use_proxy = EXCLUDED.use_proxy,
                            proxy_user = EXCLUDED.proxy_user,
                            proxy_pass = EXCLUDED.proxy_pass,
                            proxy_host = EXCLUDED.proxy_host,
                            proxy_port = EXCLUDED.proxy_port,
                            twitter_username = EXCLUDED.twitter_username,
                            take_screenshot_collect = EXCLUDED.take_screenshot_collect,
                            screenshot_xpath = EXCLUDED.screenshot_xpath,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING *
                        """,
                        (
                            user_id,
                            data.get("publish_enabled", False),
                            data.get("collect_enabled", False),
                            data.get("schedule_type", "immediate"),
                            json.dumps(data.get("time_intervals", [])),
                            data.get("use_proxy", False),
                            data.get("proxy_user"),
                            data.get("proxy_pass"),
                            data.get("proxy_host"),
                            data.get("proxy_port"),
                            data.get("twitter_username"),
                            data.get("take_screenshot_collect", False),
                            data.get("screenshot_xpath"),
                        ),
                    )
                else:
                    await cur.execute(
                        """
                        INSERT INTO tw_profiles (
                            user_id, publish_enabled, collect_enabled, schedule_type,
                            time_intervals, use_proxy, proxy_user, proxy_pass,
                            proxy_host, proxy_port, twitter_username, twitter_password,
                            take_screenshot_collect, screenshot_xpath
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            publish_enabled = EXCLUDED.publish_enabled,
                            collect_enabled = EXCLUDED.collect_enabled,
                            schedule_type = EXCLUDED.schedule_type,
                            time_intervals = EXCLUDED.time_intervals,
                            use_proxy = EXCLUDED.use_proxy,
                            proxy_user = EXCLUDED.proxy_user,
                            proxy_pass = EXCLUDED.proxy_pass,
                            proxy_host = EXCLUDED.proxy_host,
                            proxy_port = EXCLUDED.proxy_port,
                            twitter_username = EXCLUDED.twitter_username,
                            twitter_password = EXCLUDED.twitter_password,
                            take_screenshot_collect = EXCLUDED.take_screenshot_collect,
                            screenshot_xpath = EXCLUDED.screenshot_xpath,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING *
                        """,
                        (
                            user_id,
                            data.get("publish_enabled", False),
                            data.get("collect_enabled", False),
                            data.get("schedule_type", "immediate"),
                            json.dumps(data.get("time_intervals", [])),
                            data.get("use_proxy", False),
                            data.get("proxy_user"),
                            data.get("proxy_pass"),
                            data.get("proxy_host"),
                            data.get("proxy_port"),
                            data.get("twitter_username"),
                            pwd,
                            data.get("take_screenshot_collect", False),
                            data.get("screenshot_xpath"),
                        ),
                    )
                row = await cur.fetchone()
                return self._row_to_tw_profile(row, cur.description)
        finally:
            await release_db_connection(conn)

    async def set_tw_oauth_pkce(self, user_id: int, verifier: str, expires_at: datetime) -> None:
        """Сохраняет PKCE code_verifier до callback OAuth."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO tw_profiles (user_id, oauth_pkce_verifier, oauth_pkce_expires_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        oauth_pkce_verifier = EXCLUDED.oauth_pkce_verifier,
                        oauth_pkce_expires_at = EXCLUDED.oauth_pkce_expires_at,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (user_id, verifier, expires_at),
                )
        finally:
            await release_db_connection(conn)

    async def get_tw_oauth_pkce(self, user_id: int) -> Optional[str]:
        """Возвращает PKCE verifier если не истёк, иначе None."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT oauth_pkce_verifier, oauth_pkce_expires_at
                    FROM tw_profiles WHERE user_id = %s
                    """,
                    (user_id,),
                )
                row = await cur.fetchone()
                if not row or not row[0]:
                    return None
                exp = row[1]
                if exp and exp < datetime.utcnow():
                    return None
                return str(row[0])
        finally:
            await release_db_connection(conn)

    async def clear_tw_oauth_pkce(self, user_id: int) -> None:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE tw_profiles SET oauth_pkce_verifier = NULL, oauth_pkce_expires_at = NULL,
                    updated_at = CURRENT_TIMESTAMP WHERE user_id = %s
                    """,
                    (user_id,),
                )
        finally:
            await release_db_connection(conn)

    async def save_tw_oauth_tokens(
        self,
        user_id: int,
        access_token: str,
        refresh_token: Optional[str],
        expires_at: Optional[datetime],
        twitter_rest_id: Optional[str],
    ) -> None:
        """Сохраняет токены OAuth 2.0 X после callback."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO tw_profiles (
                        user_id, twitter_oauth_access_token, twitter_oauth_refresh_token,
                        twitter_oauth_expires_at, twitter_rest_id
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        twitter_oauth_access_token = EXCLUDED.twitter_oauth_access_token,
                        twitter_oauth_refresh_token = EXCLUDED.twitter_oauth_refresh_token,
                        twitter_oauth_expires_at = EXCLUDED.twitter_oauth_expires_at,
                        twitter_rest_id = EXCLUDED.twitter_rest_id,
                        oauth_pkce_verifier = NULL,
                        oauth_pkce_expires_at = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (user_id, access_token, refresh_token, expires_at, twitter_rest_id),
                )
        finally:
            await release_db_connection(conn)

    async def get_tw_oauth_tokens_raw(
        self, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Сырые OAuth-токены X для серверных вызовов API (не отдавать клиенту)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT twitter_oauth_access_token, twitter_oauth_refresh_token,
                           twitter_oauth_expires_at, twitter_rest_id
                    FROM tw_profiles WHERE user_id = %s
                    """,
                    (user_id,),
                )
                row = await cur.fetchone()
                if not row:
                    return None
                return {
                    "twitter_oauth_access_token": row[0],
                    "twitter_oauth_refresh_token": row[1],
                    "twitter_oauth_expires_at": row[2],
                    "twitter_rest_id": row[3],
                }
        finally:
            await release_db_connection(conn)

    async def persist_tw_oauth_tokens_refreshed(
        self,
        user_id: int,
        access_token: str,
        refresh_token: Optional[str],
        expires_at: Optional[datetime],
    ) -> None:
        """Обновляет токены после refresh (refresh_token опционально ротируется)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE tw_profiles SET
                        twitter_oauth_access_token = %s,
                        twitter_oauth_refresh_token = COALESCE(%s, twitter_oauth_refresh_token),
                        twitter_oauth_expires_at = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                    """,
                    (access_token, refresh_token, expires_at, user_id),
                )
        finally:
            await release_db_connection(conn)

    def _row_to_tw_profile(self, row, description) -> Dict:
        """Преобразует строку БД в словарь профиля Twitter."""
        columns = [col.name for col in description]
        profile = dict(zip(columns, row))
        if isinstance(profile.get("time_intervals"), str):
            profile["time_intervals"] = json.loads(profile["time_intervals"])
        raw_at = profile.get("twitter_oauth_access_token")
        raw_rt = profile.get("twitter_oauth_refresh_token")
        profile["twitter_connected"] = bool(raw_at or raw_rt)
        if raw_at:
            profile["twitter_oauth_access_token"] = "***"
        if raw_rt:
            profile["twitter_oauth_refresh_token"] = "***"
        if profile.get("twitter_password"):
            profile["twitter_password"] = "***"
        return profile
    
    # ==================== WordPress ====================
    
    async def get_wp_profile(self, user_id: int) -> Optional[Dict]:
        """Получает профиль WordPress пользователя."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM wp_profiles WHERE user_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_wp_profile(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)
    
    async def save_wp_profile(self, user_id: int, data: Dict) -> Dict:
        """Сохраняет или обновляет профиль WordPress."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO wp_profiles (
                        user_id, publish_enabled, collect_enabled, schedule_type,
                        time_intervals, site_url, username, app_password
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        publish_enabled = EXCLUDED.publish_enabled,
                        collect_enabled = EXCLUDED.collect_enabled,
                        schedule_type = EXCLUDED.schedule_type,
                        time_intervals = EXCLUDED.time_intervals,
                        site_url = EXCLUDED.site_url,
                        username = EXCLUDED.username,
                        app_password = EXCLUDED.app_password,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING *
                    """,
                    (
                        user_id,
                        data.get("publish_enabled", False),
                        data.get("collect_enabled", False),
                        data.get("schedule_type", "immediate"),
                        json.dumps(data.get("time_intervals", [])),
                        data.get("site_url"),
                        data.get("username"),
                        data.get("app_password"),
                    )
                )
                row = await cur.fetchone()
                return self._row_to_wp_profile(row, cur.description)
        finally:
            await release_db_connection(conn)
    
    def _row_to_wp_profile(self, row, description) -> Dict:
        """Преобразует строку БД в словарь профиля WordPress."""
        columns = [col.name for col in description]
        profile = dict(zip(columns, row))
        if isinstance(profile.get("time_intervals"), str):
            profile["time_intervals"] = json.loads(profile["time_intervals"])
        return profile

    def _row_to_wp_publish_profile(self, row, description) -> Dict:
        """Преобразует строку БД в словарь профиля публикации WordPress.
        time_intervals в БД хранится как строка "HH:MM" (JSON string) или legacy массив.
        """
        columns = [col.name for col in description]
        profile = dict(zip(columns, row))
        ti = profile.get("time_intervals")
        if ti is not None and isinstance(ti, str) and ti.strip().startswith("["):
            try:
                arr = json.loads(ti)
                profile["time_intervals"] = arr[0]["start"] if arr and isinstance(arr[0], dict) and arr[0].get("start") else ""
            except (json.JSONDecodeError, (KeyError, IndexError, TypeError)):
                profile["time_intervals"] = ""
        elif ti is not None and isinstance(ti, list) and len(ti) > 0 and isinstance(ti[0], dict):
            profile["time_intervals"] = ti[0].get("start", "") or ""
        elif ti is None or ti == "":
            profile["time_intervals"] = ""
        # иначе ti уже строка "HH:MM" — оставляем как есть
        profile.setdefault("publish_all_ready", True)
        profile.setdefault("process_before_publish", False)
        ps = profile.get("process_services")
        if ps is not None and isinstance(ps, str):
            try:
                profile["process_services"] = json.loads(ps)
            except (json.JSONDecodeError, TypeError):
                profile["process_services"] = []
        elif not isinstance(profile.get("process_services"), list):
            profile["process_services"] = []
        profile.setdefault("remove_emojis", False)
        profile.setdefault("remove_images", False)
        profile.setdefault("clean_html", False)
        profile.setdefault("status_review_after_process", False)
        profile.setdefault("add_static_html", False)
        return profile

    async def get_wp_publish_profile(self, user_id: int) -> Optional[Dict]:
        """Получает профиль публикации WordPress пользователя."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM wp_publish_profile WHERE user_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_wp_publish_profile(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

    async def save_wp_publish_profile(self, user_id: int, data: Dict) -> Dict:
        """Сохраняет или обновляет профиль публикации WordPress."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                ps = data.get("process_services")
                ps_val = json.dumps(ps) if isinstance(ps, list) and ps else None
                static_html = data.get("static_html_content")
                if static_html and len(str(static_html)) > 1000:
                    static_html = str(static_html)[:1000]
                await cur.execute(
                    """
                    INSERT INTO wp_publish_profile (
                        user_id, publish_enabled, schedule_type,
                        time_intervals, site_url, username, app_password,
                        publish_all_ready, publish_limit, publish_interval_minutes,
                        process_before_publish, process_description,
                        remove_emojis, remove_images, clean_html, process_services,
                        status_review_after_process, add_static_html, static_html_content
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        publish_enabled = EXCLUDED.publish_enabled,
                        schedule_type = EXCLUDED.schedule_type,
                        time_intervals = EXCLUDED.time_intervals,
                        site_url = EXCLUDED.site_url,
                        username = EXCLUDED.username,
                        app_password = EXCLUDED.app_password,
                        publish_all_ready = EXCLUDED.publish_all_ready,
                        publish_limit = EXCLUDED.publish_limit,
                        publish_interval_minutes = EXCLUDED.publish_interval_minutes,
                        process_before_publish = EXCLUDED.process_before_publish,
                        process_description = EXCLUDED.process_description,
                        remove_emojis = EXCLUDED.remove_emojis,
                        remove_images = EXCLUDED.remove_images,
                        clean_html = EXCLUDED.clean_html,
                        process_services = EXCLUDED.process_services,
                        status_review_after_process = EXCLUDED.status_review_after_process,
                        add_static_html = EXCLUDED.add_static_html,
                        static_html_content = EXCLUDED.static_html_content,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING *
                    """,
                    (
                        user_id,
                        data.get("publish_enabled", False),
                        data.get("schedule_type", "on_new_messages"),
                        json.dumps(data.get("time_intervals")) if data.get("time_intervals") else None,
                        data.get("site_url"),
                        data.get("username"),
                        data.get("app_password"),
                        data.get("publish_all_ready", True),
                        data.get("publish_limit"),
                        data.get("publish_interval_minutes"),
                        data.get("process_before_publish", False),
                        data.get("process_description"),
                        data.get("remove_emojis", False),
                        data.get("remove_images", False),
                        data.get("clean_html", False),
                        ps_val,
                        data.get("status_review_after_process", False),
                        data.get("add_static_html", False),
                        static_html if data.get("add_static_html") else None,
                    )
                )
                row = await cur.fetchone()
                return self._row_to_wp_publish_profile(row, cur.description)
        finally:
            await release_db_connection(conn)

    async def get_wp_collect_profile(self, user_id: int) -> Optional[Dict]:
        """Получает профиль сбора WordPress: collect_enabled из wp_collect_profile, сайты из wp_collect_sites."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM wp_collect_profile WHERE user_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                if row is None:
                    return None
                columns = [c.name for c in cur.description]
                profile = dict(zip(columns, row))
                profile["collect_sites"] = []
                profile.setdefault("collect_all_available", True)
                profile.setdefault("collect_limit", 1)
                await cur.execute(
                    "SELECT site_url, schedule_type, time_intervals FROM wp_collect_sites WHERE user_id = %s ORDER BY id",
                    (user_id,)
                )
                sites_rows = await cur.fetchall()
                sites_desc = cur.description
                for srow in sites_rows:
                    site = dict(zip([c.name for c in sites_desc], srow))
                    profile["collect_sites"].append({
                        "site_url": site.get("site_url"),
                        "schedule_type": site.get("schedule_type") or "on_new_messages",
                        "time_intervals": site.get("time_intervals") or "",
                    })
                return profile
        finally:
            await release_db_connection(conn)

    async def save_wp_collect_profile(self, user_id: int, data: Dict) -> Dict:
        """Сохраняет профиль сбора: collect_enabled в wp_collect_profile, сайты в wp_collect_sites (столбцы site_url, schedule_type, time_intervals)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                collect_limit_val = data.get("collect_limit")
                if collect_limit_val is not None:
                    collect_limit_val = max(1, min(25, int(collect_limit_val)))
                await cur.execute(
                    """
                    INSERT INTO wp_collect_profile (user_id, collect_enabled, collect_all_available, collect_limit)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        collect_enabled = EXCLUDED.collect_enabled,
                        collect_all_available = EXCLUDED.collect_all_available,
                        collect_limit = EXCLUDED.collect_limit,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (user_id, data.get("collect_enabled", False), data.get("collect_all_available", True), collect_limit_val or 1)
                )
                await cur.execute("DELETE FROM wp_collect_sites WHERE user_id = %s", (user_id,))
                for site in data.get("collect_sites", []):
                    site_url = site.get("site_url") or ""
                    schedule_type = site.get("schedule_type") or "on_new_messages"
                    time_intervals = site.get("time_intervals") if isinstance(site.get("time_intervals"), str) else ""
                    await cur.execute(
                        """
                        INSERT INTO wp_collect_sites (user_id, site_url, schedule_type, time_intervals)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (user_id, site_url, schedule_type, time_intervals or None)
                    )
                return await self.get_wp_collect_profile(user_id) or {}
        finally:
            await release_db_connection(conn)

    # ==================== VKontakte ====================
    
    async def get_vk_profile(self, user_id: int) -> Optional[Dict]:
        """Получает профиль VKontakte пользователя."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM vk_profiles WHERE user_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_vk_profile(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)
    
    async def save_vk_profile(self, user_id: int, data: Dict) -> Dict:
        """Сохраняет или обновляет профиль VKontakte."""
        access_token = data.get("access_token")
        # При обновлении не перезаписываем токен маской "***"
        if access_token in (None, "", "***"):
            access_token = None
        user_access_token = data.get("user_access_token")
        if user_access_token in (None, "", "***"):
            user_access_token = None
        vk_app_secret = data.get("vk_app_secret")
        if vk_app_secret in (None, "", "***"):
            vk_app_secret = None
        groups_to_read = data.get("groups_to_read", [])
        if not isinstance(groups_to_read, list):
            groups_to_read = []
        users_to_read = data.get("users_to_read", [])
        if not isinstance(users_to_read, list):
            users_to_read = []
        group_to_post = data.get("group_to_post")
        post_to_own_wall = data.get("post_to_own_wall", False)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO vk_profiles (
                        user_id, publish_enabled, collect_enabled, schedule_type,
                        time_intervals, owner_id, friends_only, from_group,
                        message, attachments, signed, mark_as_ads,
                        access_token, user_access_token, groups_to_read, group_to_post,
                        post_to_own_wall, users_to_read,
                        vk_app_id, vk_app_secret, vk_frontend_url, vk_public_gateway_url
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        publish_enabled = EXCLUDED.publish_enabled,
                        collect_enabled = EXCLUDED.collect_enabled,
                        schedule_type = EXCLUDED.schedule_type,
                        time_intervals = EXCLUDED.time_intervals,
                        owner_id = EXCLUDED.owner_id,
                        friends_only = EXCLUDED.friends_only,
                        from_group = EXCLUDED.from_group,
                        message = EXCLUDED.message,
                        attachments = EXCLUDED.attachments,
                        signed = EXCLUDED.signed,
                        mark_as_ads = EXCLUDED.mark_as_ads,
                        access_token = COALESCE(NULLIF(EXCLUDED.access_token, ''), vk_profiles.access_token),
                        user_access_token = COALESCE(NULLIF(EXCLUDED.user_access_token, ''), vk_profiles.user_access_token),
                        groups_to_read = COALESCE(EXCLUDED.groups_to_read, vk_profiles.groups_to_read),
                        group_to_post = COALESCE(EXCLUDED.group_to_post, vk_profiles.group_to_post),
                        post_to_own_wall = COALESCE(EXCLUDED.post_to_own_wall, vk_profiles.post_to_own_wall),
                        users_to_read = COALESCE(EXCLUDED.users_to_read, vk_profiles.users_to_read),
                        vk_app_id = COALESCE(NULLIF(EXCLUDED.vk_app_id, ''), vk_profiles.vk_app_id),
                        vk_app_secret = COALESCE(NULLIF(EXCLUDED.vk_app_secret, ''), vk_profiles.vk_app_secret),
                        vk_frontend_url = COALESCE(NULLIF(EXCLUDED.vk_frontend_url, ''), vk_profiles.vk_frontend_url),
                        vk_public_gateway_url = COALESCE(
                            NULLIF(EXCLUDED.vk_public_gateway_url, ''), vk_profiles.vk_public_gateway_url
                        ),
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING *
                    """,
                    (
                        user_id,
                        data.get("publish_enabled", False),
                        data.get("collect_enabled", False),
                        data.get("schedule_type", "immediate"),
                        json.dumps(data.get("time_intervals", [])),
                        data.get("owner_id"),
                        data.get("friends_only", False),
                        data.get("from_group", False),
                        data.get("message"),
                        data.get("attachments"),
                        data.get("signed", False),
                        data.get("mark_as_ads", False),
                        access_token,
                        user_access_token,
                        json.dumps(groups_to_read),
                        group_to_post,
                        post_to_own_wall,
                        json.dumps(users_to_read),
                        data.get("vk_app_id") or None,
                        vk_app_secret,
                        data.get("vk_frontend_url") or None,
                        data.get("vk_public_gateway_url") or None,
                    )
                )
                row = await cur.fetchone()
                return self._row_to_vk_profile(row, cur.description)
        finally:
            await release_db_connection(conn)

    async def get_vk_profile_tokens_raw(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Внутренний доступ к токенам VK без маскирования (только серверные вызовы VK API)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT access_token, user_access_token, vk_user_id, group_to_post, groups_to_read
                    FROM vk_profiles WHERE user_id = %s
                    """,
                    (user_id,),
                )
                row = await cur.fetchone()
                if not row:
                    return None
                access_token, user_access_token, vk_user_id, group_to_post, groups_to_read = row
                gr = groups_to_read
                if isinstance(gr, str):
                    try:
                        gr = json.loads(gr)
                    except (json.JSONDecodeError, TypeError):
                        gr = []
                if not isinstance(gr, list):
                    gr = []
                return {
                    "access_token": access_token,
                    "user_access_token": user_access_token,
                    "vk_user_id": vk_user_id,
                    "group_to_post": group_to_post,
                    "groups_to_read": gr,
                }
        finally:
            await release_db_connection(conn)

    async def get_vk_oauth_config_raw(self, user_id: int) -> Optional[Dict[str, Any]]:
        """OAuth-приложение VK из профиля (секрет без маскирования)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT vk_app_id, vk_app_secret, vk_frontend_url, vk_public_gateway_url
                    FROM vk_profiles WHERE user_id = %s
                    """,
                    (user_id,),
                )
                row = await cur.fetchone()
                if not row:
                    return None
                return {
                    "vk_app_id": row[0],
                    "vk_app_secret": row[1],
                    "vk_frontend_url": row[2],
                    "vk_public_gateway_url": row[3],
                }
        finally:
            await release_db_connection(conn)

    async def save_vk_oauth_tokens(
        self,
        user_id: int,
        user_access_token: str,
        vk_user_id: Optional[int] = None,
    ) -> None:
        """Сохраняет пользовательский OAuth-токен VK после callback (создаёт минимальный профиль при необходимости)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO vk_profiles (user_id, user_access_token, vk_user_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        user_access_token = EXCLUDED.user_access_token,
                        vk_user_id = EXCLUDED.vk_user_id,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (user_id, user_access_token, vk_user_id),
                )
        finally:
            await release_db_connection(conn)
    
    def _row_to_vk_profile(self, row, description) -> Dict:
        """Преобразует строку БД в словарь профиля VKontakte. Токен маскируется в ответах."""
        columns = [col.name for col in description]
        profile = dict(zip(columns, row))
        if isinstance(profile.get("time_intervals"), str):
            profile["time_intervals"] = json.loads(profile["time_intervals"])
        if isinstance(profile.get("groups_to_read"), str):
            try:
                profile["groups_to_read"] = json.loads(profile["groups_to_read"])
            except (json.JSONDecodeError, TypeError):
                profile["groups_to_read"] = []
        if isinstance(profile.get("users_to_read"), str):
            try:
                profile["users_to_read"] = json.loads(profile["users_to_read"])
            except (json.JSONDecodeError, TypeError):
                profile["users_to_read"] = []
        has_user_oauth = bool(profile.get("user_access_token"))
        profile["vk_connected"] = has_user_oauth
        if "vk_user_id" not in profile:
            profile["vk_user_id"] = None
        if profile.get("access_token"):
            profile["access_token"] = "***"
        if profile.get("user_access_token"):
            profile["user_access_token"] = "***"
        if profile.get("vk_app_secret"):
            profile["vk_app_secret"] = "***"
        return profile
    
    # ==================== cURL ====================
    
    async def get_curl_settings(self, user_id: int) -> Optional[Dict]:
        """Получает настройки cURL пользователя."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM curl_settings WHERE user_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_curl_settings(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)
    
    async def save_curl_settings(self, user_id: int, data: Dict) -> Dict:
        """Сохраняет или обновляет настройки cURL (urls + обработка)."""
        urls = data.get("urls") or []
        urls_json = json.dumps(urls)
        first = urls[0] if urls else {}
        tsn = first.get("target_social_networks") or {}
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO curl_settings (
                        user_id, collect_enabled, schedule_type, time_intervals,
                        url, xpath, take_screenshot, to_tg, to_tw, to_vk, to_wp,
                        urls, process_before_publish, process_description,
                        remove_emojis, remove_images, clean_html, process_services,
                        status_review_after_process, add_static_html, static_html_content,
                        screenshot_only
                    ) VALUES (
                        %s, %s, 'standard', '[]',
                        %s, %s, %s, %s, %s, %s, %s,
                        %s::jsonb, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s,
                        %s
                    )
                    ON CONFLICT (user_id) DO UPDATE SET
                        collect_enabled = EXCLUDED.collect_enabled,
                        url = EXCLUDED.url,
                        xpath = EXCLUDED.xpath,
                        take_screenshot = EXCLUDED.take_screenshot,
                        to_tg = EXCLUDED.to_tg,
                        to_tw = EXCLUDED.to_tw,
                        to_vk = EXCLUDED.to_vk,
                        to_wp = EXCLUDED.to_wp,
                        urls = EXCLUDED.urls,
                        process_before_publish = EXCLUDED.process_before_publish,
                        process_description = EXCLUDED.process_description,
                        remove_emojis = EXCLUDED.remove_emojis,
                        remove_images = EXCLUDED.remove_images,
                        clean_html = EXCLUDED.clean_html,
                        process_services = EXCLUDED.process_services,
                        status_review_after_process = EXCLUDED.status_review_after_process,
                        add_static_html = EXCLUDED.add_static_html,
                        static_html_content = EXCLUDED.static_html_content,
                        screenshot_only = EXCLUDED.screenshot_only,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING *
                    """,
                    (
                        user_id,
                        data.get("collect_enabled", False),
                        first.get("url"),
                        first.get("xpath"),
                        first.get("take_screenshot", False),
                        tsn.get("tg", False),
                        tsn.get("tw", False),
                        tsn.get("vk", False),
                        tsn.get("wp", False),
                        urls_json,
                        data.get("process_before_publish", False),
                        data.get("process_description"),
                        data.get("remove_emojis", False),
                        data.get("remove_images", False),
                        data.get("clean_html", False),
                        json.dumps(data.get("process_services") or []),
                        data.get("status_review_after_process", False),
                        data.get("add_static_html", False),
                        (data.get("static_html_content") or "")[:1000],
                        data.get("screenshot_only", False),
                    )
                )
                row = await cur.fetchone()
                return self._row_to_curl_settings(row, cur.description)
        finally:
            await release_db_connection(conn)
    
    def _row_to_curl_settings(self, row, description) -> Dict:
        """Преобразует строку БД в словарь настроек cURL (urls + обработка)."""
        columns = [col.name for col in description]
        settings = dict(zip(columns, row))
        urls_raw = settings.get("urls")
        if urls_raw is not None:
            if isinstance(urls_raw, str):
                urls_raw = json.loads(urls_raw) if urls_raw else []
            settings["urls"] = urls_raw
        else:
            url = settings.get("url")
            xpath = settings.get("xpath")
            if url is not None or xpath is not None:
                settings["urls"] = [{
                    "url": url or "",
                    "xpath": xpath or "",
                    "take_screenshot": settings.get("take_screenshot", False),
                    "target_social_networks": {
                        "tg": settings.get("to_tg", False),
                        "tw": settings.get("to_tw", False),
                        "vk": settings.get("to_vk", False),
                        "wp": settings.get("to_wp", False),
                    },
                    "schedule_time": "09:00",
                }]
            else:
                settings["urls"] = []
        # Normalize urls: ensure schedule_time, run_once, drop legacy time_interval
        for item in settings.get("urls") or []:
            if "time_interval" in item:
                item["schedule_time"] = (item["time_interval"] or {}).get("start") or "09:00"
                del item["time_interval"]
            item.setdefault("schedule_time", "09:00")
            item.setdefault("run_once", False)
        for key in ("time_intervals", "schedule_type", "url", "xpath", "take_screenshot", "to_tg", "to_tw", "to_vk", "to_wp"):
            settings.pop(key, None)
        if isinstance(settings.get("process_services"), str):
            settings["process_services"] = json.loads(settings["process_services"]) if settings["process_services"] else []
        # Гарантируем булево значение для screenshot_only
        settings["screenshot_only"] = bool(settings.get("screenshot_only", False))
        return settings

    async def record_curl_one_time_done_batch(self, items: List[Dict[str, Any]]) -> None:
        """Записывает выполненные одноразовые URL в curl_one_time_done (ON CONFLICT DO NOTHING)."""
        if not items:
            return
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                for it in items:
                    user_id = it.get("user_id")
                    url = (it.get("url") or "").strip()
                    xpath = (it.get("xpath") or "").strip()
                    if user_id is None:
                        continue
                    await cur.execute(
                        """
                        INSERT INTO curl_one_time_done (user_id, url, xpath)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id, url, xpath) DO NOTHING
                        """,
                        (user_id, url, xpath),
                    )
        finally:
            await release_db_connection(conn)
    
    # ==================== cPost ====================
    
    async def get_cpost_profile(self, user_id: int) -> Optional[Dict]:
        """Получает профиль ручных постов пользователя."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM cpost_profiles WHERE user_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_cpost_profile(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)
    
    async def save_cpost_profile(self, user_id: int, data: Dict) -> Dict:
        """Сохраняет или обновляет профиль ручных постов."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO cpost_profiles (user_id, default_platforms)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        default_platforms = EXCLUDED.default_platforms,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING *
                    """,
                    (
                        user_id,
                        json.dumps(
                            data.get(
                                "default_platforms",
                                {
                                    "tg": False,
                                    "tw": False,
                                    "wp": False,
                                    "vk": False,
                                    "threads": False,
                                    "dzen": False,
                                    "instagram": False,
                                },
                            )
                        ),
                    )
                )
                row = await cur.fetchone()
                return self._row_to_cpost_profile(row, cur.description)
        finally:
            await release_db_connection(conn)
    
    def _row_to_cpost_profile(self, row, description) -> Dict:
        """Преобразует строку БД в словарь профиля ручных постов."""
        columns = [col.name for col in description]
        profile = dict(zip(columns, row))
        if isinstance(profile.get("default_platforms"), str):
            profile["default_platforms"] = json.loads(profile["default_platforms"])
        return profile
    
    # ==================== Методы получения всех профилей ====================
    
    async def get_all_tg_profiles(self) -> list[Dict]:
        """Получает все профили Telegram."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM tg_profiles")
                rows = await cur.fetchall()
                return [self._row_to_tg_profile(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)
    
    async def get_all_tw_profiles(self) -> list[Dict]:
        """Получает все профили Twitter."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM tw_profiles")
                rows = await cur.fetchall()
                return [self._row_to_tw_profile(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)
    
    async def get_all_wp_profiles(self) -> list[Dict]:
        """Получает все профили WordPress (объединение wp_publish_profile и wp_collect_profile по user_id)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM wp_publish_profile")
                pub_rows = await cur.fetchall()
                pub_desc = cur.description
                await cur.execute("SELECT * FROM wp_collect_profile")
                coll_rows = await cur.fetchall()
                coll_desc = cur.description
            # Собираем по user_id
            by_user: Dict[int, Dict] = {}
            for row in pub_rows:
                rec = self._row_to_wp_publish_profile(row, pub_desc)
                uid = rec["user_id"]
                ti = rec.get("time_intervals")
                if isinstance(ti, list):
                    ti_val = ti
                elif isinstance(ti, str) and ti:
                    ti_val = ti  # "HH:MM" — строка для wp publish
                else:
                    ti_val = []
                by_user[uid] = {
                    "user_id": uid,
                    "publish_enabled": rec.get("publish_enabled", False),
                    "collect_enabled": False,
                    "schedule_type": rec.get("schedule_type") or "immediate",
                    "time_intervals": ti_val,
                }
            for row in coll_rows:
                rec = dict(zip([c.name for c in coll_desc], row))
                uid = rec["user_id"]
                if uid not in by_user:
                    by_user[uid] = {
                        "user_id": uid,
                        "publish_enabled": False,
                        "collect_enabled": False,
                        "schedule_type": "immediate",
                        "time_intervals": [],
                    }
                by_user[uid]["collect_enabled"] = rec.get("collect_enabled", False)
            return list(by_user.values())
        finally:
            await release_db_connection(conn)
    
    async def get_all_vk_profiles(self) -> list[Dict]:
        """Получает все профили VKontakte."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM vk_profiles")
                rows = await cur.fetchall()
                return [self._row_to_vk_profile(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)

    # ==================== Dzen ====================

    async def get_dzen_profile(self, user_id: int) -> Optional[Dict]:
        """Получает профиль Дзен пользователя."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM dzen_profiles WHERE user_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_dzen_profile(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

    async def save_dzen_profile(self, user_id: int, data: Dict) -> Dict:
        """Сохраняет или обновляет профиль Дзен."""
        channels_to_read = data.get("channels_to_read", [])
        if not isinstance(channels_to_read, list):
            channels_to_read = []
        yandex_password = data.get("yandex_password")
        if yandex_password in (None, "", "***"):
            yandex_password = None
        collect_source = (data.get("collect_source") or "rss").strip().lower()
        if collect_source not in ("rss", "selenium", "both"):
            collect_source = "rss"
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO dzen_profiles (
                        user_id, publish_enabled, collect_enabled, schedule_type,
                        time_intervals, rss_feed_url, channel_name, channels_to_read, rss_token,
                        yandex_login, yandex_password, dzen_studio_url, collect_source
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        publish_enabled = EXCLUDED.publish_enabled,
                        collect_enabled = EXCLUDED.collect_enabled,
                        schedule_type = EXCLUDED.schedule_type,
                        time_intervals = EXCLUDED.time_intervals,
                        rss_feed_url = EXCLUDED.rss_feed_url,
                        channel_name = EXCLUDED.channel_name,
                        channels_to_read = EXCLUDED.channels_to_read,
                        rss_token = EXCLUDED.rss_token,
                        yandex_login = EXCLUDED.yandex_login,
                        yandex_password = COALESCE(NULLIF(EXCLUDED.yandex_password, ''), dzen_profiles.yandex_password),
                        dzen_studio_url = EXCLUDED.dzen_studio_url,
                        collect_source = EXCLUDED.collect_source,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING *
                    """,
                    (
                        user_id,
                        data.get("publish_enabled", False),
                        data.get("collect_enabled", False),
                        data.get("schedule_type", "immediate"),
                        json.dumps(data.get("time_intervals", [])),
                        data.get("rss_feed_url"),
                        data.get("channel_name"),
                        json.dumps(channels_to_read),
                        data.get("rss_token"),
                        data.get("yandex_login"),
                        yandex_password,
                        data.get("dzen_studio_url"),
                        collect_source,
                    )
                )
                row = await cur.fetchone()
                return self._row_to_dzen_profile(row, cur.description)
        finally:
            await release_db_connection(conn)

    async def set_dzen_last_auth_error(self, user_id: int, message: Optional[str]) -> None:
        """Сохраняет текст последней ошибки авторизации/сценария Дзен (dzen-bot)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE dzen_profiles SET last_auth_error = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                    """,
                    (message, user_id),
                )
        finally:
            await release_db_connection(conn)

    def _row_to_dzen_profile(self, row, description) -> Dict:
        """Преобразует строку БД в словарь профиля Дзен."""
        columns = [col.name for col in description]
        profile = dict(zip(columns, row))
        if isinstance(profile.get("time_intervals"), str):
            try:
                profile["time_intervals"] = json.loads(profile["time_intervals"])
            except (json.JSONDecodeError, TypeError):
                profile["time_intervals"] = []
        if isinstance(profile.get("channels_to_read"), str):
            try:
                profile["channels_to_read"] = json.loads(profile["channels_to_read"])
            except (json.JSONDecodeError, TypeError):
                profile["channels_to_read"] = []
        if profile.get("yandex_password"):
            profile["yandex_password"] = "***"
        if profile.get("collect_source") in (None, ""):
            profile["collect_source"] = "rss"
        return profile

    async def get_all_dzen_profiles(self) -> list[Dict]:
        """Получает все профили Дзен."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM dzen_profiles")
                rows = await cur.fetchall()
                return [self._row_to_dzen_profile(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)

    # ==================== Instagram ====================

    async def get_instagram_profile(self, user_id: int) -> Optional[Dict]:
        """Получает профиль Instagram пользователя."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM instagram_profiles WHERE user_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_instagram_profile(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

    async def save_instagram_profile(self, user_id: int, data: Dict) -> Dict:
        """Сохраняет или обновляет профиль Instagram."""
        password = data.get("password")
        if password in (None, "", "***"):
            password = None
        usernames_to_read = data.get("usernames_to_read", [])
        if not isinstance(usernames_to_read, list):
            usernames_to_read = []
        process_services = data.get("process_services")
        process_services_json = json.dumps(process_services) if isinstance(process_services, list) else None
        vcode = data.get("instagram_verification_code")
        if vcode in (None, "", "***"):
            vcode = None
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO instagram_profiles (
                        user_id, publish_enabled, collect_enabled, schedule_type,
                        time_intervals, username, password, usernames_to_read,
                        process_enabled, processing_description, remove_emojis,
                        remove_images, clean_html, process_services,
                        status_review_after_process, add_static_html, static_html_content,
                        instagram_verification_code
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        publish_enabled = EXCLUDED.publish_enabled,
                        collect_enabled = EXCLUDED.collect_enabled,
                        schedule_type = EXCLUDED.schedule_type,
                        time_intervals = EXCLUDED.time_intervals,
                        username = EXCLUDED.username,
                        password = COALESCE(NULLIF(EXCLUDED.password, ''), instagram_profiles.password),
                        usernames_to_read = COALESCE(EXCLUDED.usernames_to_read, instagram_profiles.usernames_to_read),
                        process_enabled = EXCLUDED.process_enabled,
                        processing_description = EXCLUDED.processing_description,
                        remove_emojis = EXCLUDED.remove_emojis,
                        remove_images = EXCLUDED.remove_images,
                        clean_html = EXCLUDED.clean_html,
                        process_services = EXCLUDED.process_services,
                        status_review_after_process = EXCLUDED.status_review_after_process,
                        add_static_html = EXCLUDED.add_static_html,
                        static_html_content = EXCLUDED.static_html_content,
                        instagram_verification_code = COALESCE(
                            NULLIF(EXCLUDED.instagram_verification_code, ''),
                            instagram_profiles.instagram_verification_code
                        ),
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING *
                    """,
                    (
                        user_id,
                        data.get("publish_enabled", False),
                        data.get("collect_enabled", False),
                        data.get("schedule_type", "immediate"),
                        json.dumps(data.get("time_intervals", [])),
                        data.get("username"),
                        password,
                        json.dumps(usernames_to_read),
                        data.get("process_enabled", False),
                        data.get("processing_description"),
                        data.get("remove_emojis", False),
                        data.get("remove_images", False),
                        data.get("clean_html", False),
                        process_services_json,
                        data.get("status_review_after_process", False),
                        data.get("add_static_html", False),
                        data.get("static_html_content"),
                        vcode,
                    )
                )
                row = await cur.fetchone()
                return self._row_to_instagram_profile(row, cur.description)
        finally:
            await release_db_connection(conn)

    def _row_to_instagram_profile(self, row, description) -> Dict:
        """Преобразует строку БД в словарь профиля Instagram. Пароль не возвращается."""
        columns = [col.name for col in description]
        profile = dict(zip(columns, row))
        if isinstance(profile.get("time_intervals"), str):
            try:
                profile["time_intervals"] = json.loads(profile["time_intervals"])
            except (json.JSONDecodeError, TypeError):
                profile["time_intervals"] = []
        if isinstance(profile.get("usernames_to_read"), str):
            try:
                profile["usernames_to_read"] = json.loads(profile["usernames_to_read"])
            except (json.JSONDecodeError, TypeError):
                profile["usernames_to_read"] = []
        if profile.get("password"):
            profile["password"] = "***"
        raw_session = profile.get("instagrapi_session")
        profile["has_instagram_session"] = _instagram_session_is_non_empty(raw_session)
        vc = profile.get("instagram_verification_code")
        profile["instagram_verification_pending"] = bool(vc)
        profile.pop("instagrapi_session", None)
        profile.pop("instagram_verification_code", None)
        profile["instagram_verification_code"] = None
        return profile

    async def get_all_instagram_profiles(self) -> list[Dict]:
        """Получает все профили Instagram."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM instagram_profiles")
                rows = await cur.fetchall()
                return [self._row_to_instagram_profile(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)


profile_service = ProfileService()
