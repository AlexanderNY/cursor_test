from datetime import datetime, timedelta
from typing import Optional
from database import get_db_connection
from utils.jwt_utils import decode_token
from utils.exceptions import TokenExpiredError, TokenInvalidError
from shared.token_blacklist_redis import token_blacklist_redis


async def save_refresh_token(user_id: int, token: str) -> None:
    """Сохранение refresh токена в базе данных."""
    payload = decode_token(token)
    expires_at = datetime.fromtimestamp(payload["exp"])
    
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO refresh_tokens (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (token) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    expires_at = EXCLUDED.expires_at
                """,
                (user_id, token, expires_at)
            )


async def revoke_refresh_token(token: str) -> None:
    """Отзыв refresh токена (удаление из базы данных)."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM refresh_tokens WHERE token = %s",
                (token,)
            )


async def revoke_all_refresh_tokens(user_id: int) -> None:
    """Отзыв всех refresh токенов пользователя."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM refresh_tokens WHERE user_id = %s",
                (user_id,)
            )


async def is_refresh_token_valid(token: str) -> bool:
    """Проверка валидности refresh токена в базе данных."""
    try:
        payload = decode_token(token)
        
        if payload.get("type") != "refresh":
            return False
        
        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id FROM refresh_tokens 
                    WHERE token = %s AND expires_at > %s
                    """,
                    (token, datetime.utcnow())
                )
                row = await cur.fetchone()
                return row is not None
    except (TokenExpiredError, TokenInvalidError):
        return False


async def blacklist_token(token: str) -> None:
    """Добавление токена в черный список (Postgres + Redis hot path)."""
    try:
        payload = decode_token(token)
        expires_at = datetime.fromtimestamp(payload["exp"])
    except (TokenExpiredError, TokenInvalidError):
        # Если токен уже истек или невалиден, все равно добавляем в blacklist
        expires_at = datetime.utcnow() + timedelta(days=1)
    
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO blacklisted_tokens (token, expires_at)
                VALUES (%s, %s)
                ON CONFLICT (token) DO NOTHING
                """,
                (token, expires_at)
            )

    await token_blacklist_redis.add(token, expires_at)
    # Ensure ready flag stays set after first write (warm may have run already).
    await token_blacklist_redis.mark_ready()


async def is_token_blacklisted(token: str) -> bool:
    """Проверка blacklist: Redis (если ready) → Postgres."""
    ready = await token_blacklist_redis.is_ready()
    if ready is True:
        hit = await token_blacklist_redis.contains(token)
        if hit is not None:
            return hit

    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id FROM blacklisted_tokens 
                WHERE token = %s AND expires_at > %s
                """,
                (token, datetime.utcnow())
            )
            row = await cur.fetchone()
            return row is not None


async def warm_token_blacklist_redis() -> int:
    """Load non-expired blacklisted tokens into Redis for gateway hot path."""
    if not token_blacklist_redis.connected:
        return 0
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT token, expires_at
                FROM blacklisted_tokens
                WHERE expires_at > %s
                """,
                (datetime.utcnow(),),
            )
            rows = await cur.fetchall()
    pairs = [(str(r[0]), r[1]) for r in rows if r and r[0]]
    return await token_blacklist_redis.warm(pairs)


async def save_email_verification_token(user_id: int, token: str) -> None:
    """Сохранение токена верификации email в базе данных."""
    payload = decode_token(token)
    expires_at = datetime.fromtimestamp(payload["exp"])
    
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO email_verification_tokens (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, token, expires_at)
            )


async def get_email_verification_token(token: str) -> Optional[int]:
    """Получение user_id по токену верификации email."""
    try:
        payload = decode_token(token)
        
        if payload.get("type") != "email_verification":
            return None
        
        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_id FROM email_verification_tokens 
                    WHERE token = %s AND expires_at > %s
                    """,
                    (token, datetime.utcnow())
                )
                row = await cur.fetchone()
                if row:
                    return row[0]
                return None
    except (TokenExpiredError, TokenInvalidError):
        return None


async def delete_email_verification_token(token: str) -> None:
    """Удаление токена верификации email после использования."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM email_verification_tokens WHERE token = %s",
                (token,)
            )


async def save_password_reset_token(user_id: int, token: str) -> None:
    """Сохранение токена сброса пароля в базе данных."""
    payload = decode_token(token)
    expires_at = datetime.fromtimestamp(payload["exp"])
    
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            # Удаляем старые токены для этого пользователя
            await cur.execute(
                "DELETE FROM password_reset_tokens WHERE user_id = %s",
                (user_id,)
            )
            # Сохраняем новый токен
            await cur.execute(
                """
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, token, expires_at)
            )


async def get_password_reset_token(token: str) -> Optional[int]:
    """Получение user_id по токену сброса пароля."""
    try:
        payload = decode_token(token)
        
        if payload.get("type") != "password_reset":
            return None
        
        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_id FROM password_reset_tokens 
                    WHERE token = %s AND expires_at > %s
                    """,
                    (token, datetime.utcnow())
                )
                row = await cur.fetchone()
                if row:
                    return row[0]
                return None
    except (TokenExpiredError, TokenInvalidError):
        return None


async def delete_password_reset_token(token: str) -> None:
    """Удаление токена сброса пароля после использования."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM password_reset_tokens WHERE token = %s",
                (token,)
            )
