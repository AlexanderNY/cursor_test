from datetime import datetime, timedelta
from typing import Optional
from database import get_db_connection
from utils.jwt_utils import decode_token
from utils.exceptions import TokenExpiredError, TokenInvalidError


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
    """Добавление токена в черный список."""
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


async def is_token_blacklisted(token: str) -> bool:
    """Проверка наличия токена в черном списке."""
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

