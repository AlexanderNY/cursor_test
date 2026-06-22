import csv
import io
from typing import Dict, List, Optional
from database import get_db_connection
from services.password_service import hash_password, verify_password
from services.token_service import (
    save_refresh_token,
    save_email_verification_token,
    get_email_verification_token,
    delete_email_verification_token,
    save_password_reset_token,
    get_password_reset_token,
    delete_password_reset_token,
    revoke_all_refresh_tokens,
)
from utils.jwt_utils import (
    create_access_token,
    create_refresh_token,
    create_email_verification_token,
    create_password_reset_token
)
from utils.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    EmailAlreadyVerifiedError,
    TokenNotFoundError
)
from services.admin_audit_service import log_admin_audit


async def register_user(username: str, email: str, password: str) -> Dict:
    """Регистрация нового пользователя."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            # Проверка существования пользователя
            await cur.execute(
                "SELECT id FROM users WHERE username = %s OR email = %s",
                (username, email)
            )
            existing_user = await cur.fetchone()
            
            if existing_user:
                raise UserAlreadyExistsError("User with this username or email already exists")
            
            # Хеширование пароля
            password_hash = hash_password(password)
            
            # Создание пользователя (роль по умолчанию 'guest', тариф по умолчанию 'free')
            await cur.execute(
                """
                INSERT INTO users (username, email, password_hash, role, tariff)
                VALUES (%s, %s, %s, 'guest', 'free')
                RETURNING id, username, email, role, tariff, is_email_verified, created_at
                """,
                (username, email, password_hash)
            )
            user_row = await cur.fetchone()

            if not user_row:
                raise RuntimeError("Failed to create user")

            user_id = user_row[0]
            user_role = user_row[3]
            
            # Создание токенов
            access_token = create_access_token(user_id, user_role, is_blocked=False)
            refresh_token = create_refresh_token(user_id, user_role)
            
            # Сохранение refresh токена
            await save_refresh_token(user_id, refresh_token)
            
            # Создание токена для верификации email
            email_verification_token = create_email_verification_token(user_id)
            await save_email_verification_token(user_id, email_verification_token)
            
            return {
                "user_id": user_id,
                "username": user_row[1],
                "email": user_row[2],
                "role": user_role,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "email_verification_token": email_verification_token
            }


async def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Аутентификация пользователя по логину и паролю."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, username, email, password_hash, role, is_email_verified, is_blocked
                FROM users WHERE username = %s
                """,
                (username,)
            )
            user_row = await cur.fetchone()
            
            if not user_row:
                return None
            
            user_id, db_username, db_email, password_hash, user_role, is_email_verified, is_blocked = user_row
            
            if is_blocked:
                return None
            
            # Проверка пароля
            if not verify_password(password, password_hash):
                return None
            
            # Создание токенов
            access_token = create_access_token(user_id, user_role, is_blocked=False)
            refresh_token = create_refresh_token(user_id, user_role)
            
            # Сохранение refresh токена
            await save_refresh_token(user_id, refresh_token)
            
            return {
                "user_id": user_id,
                "username": db_username,
                "email": db_email,
                "role": user_role,
                "is_email_verified": is_email_verified,
                "access_token": access_token,
                "refresh_token": refresh_token
            }


async def verify_email_token(token: str) -> bool:
    """Верификация email по токену."""
    user_id = await get_email_verification_token(token)
    
    if not user_id:
        raise TokenNotFoundError("Invalid or expired email verification token")
    
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            # Проверка, не верифицирован ли уже email
            await cur.execute(
                "SELECT is_email_verified FROM users WHERE id = %s",
                (user_id,)
            )
            user_row = await cur.fetchone()
            
            if not user_row:
                raise UserNotFoundError("User not found")
            
            if user_row[0]:
                raise EmailAlreadyVerifiedError("Email is already verified")
            
            # Обновление статуса верификации
            await cur.execute(
                "UPDATE users SET is_email_verified = TRUE WHERE id = %s",
                (user_id,)
            )
            
            # Удаление токена
            await delete_email_verification_token(token)
            
            return True


async def reset_password(token: str, new_password: str) -> bool:
    """Сброс пароля по токену."""
    user_id = await get_password_reset_token(token)
    
    if not user_id:
        raise TokenNotFoundError("Invalid or expired password reset token")
    
    # Хеширование нового пароля
    password_hash = hash_password(new_password)
    
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            # Обновление пароля
            await cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (password_hash, user_id)
            )
            
            # Удаление токена
            await delete_password_reset_token(token)
            
            # Отзыв всех refresh токенов пользователя (безопасность)
            await revoke_all_refresh_tokens(user_id)
            
            return True


async def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Получение пользователя по ID."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, username, email, role, tariff, is_email_verified, created_at, is_blocked,
                       billing_provider, billing_customer_id, billing_subscription_id,
                       subscription_status, subscription_current_period_end
                FROM users WHERE id = %s
                """,
                (user_id,)
            )
            user_row = await cur.fetchone()

            if not user_row:
                return None

            return {
                "id": user_row[0],
                "username": user_row[1],
                "email": user_row[2],
                "role": user_row[3],
                "tariff": user_row[4],
                "is_email_verified": user_row[5],
                "created_at": user_row[6],
                "is_blocked": user_row[7],
                "billing_provider": user_row[8],
                "billing_customer_id": user_row[9],
                "billing_subscription_id": user_row[10],
                "subscription_status": user_row[11],
                "subscription_current_period_end": user_row[12],
            }


async def update_user_profile(user_id: int, username: Optional[str] = None, email: Optional[str] = None) -> Dict:
    """Обновление профиля пользователя."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            # Проверка существования пользователя
            await cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not await cur.fetchone():
                raise UserNotFoundError("User not found")
            
            # Проверка уникальности username и email
            if username:
                await cur.execute(
                    "SELECT id FROM users WHERE username = %s AND id != %s",
                    (username, user_id)
                )
                if await cur.fetchone():
                    raise UserAlreadyExistsError("Username already taken")
            
            if email:
                await cur.execute(
                    "SELECT id FROM users WHERE email = %s AND id != %s",
                    (email, user_id)
                )
                if await cur.fetchone():
                    raise UserAlreadyExistsError("Email already taken")
            
            # Обновление полей
            updates = []
            params = []
            
            if username:
                updates.append("username = %s")
                params.append(username)
            
            if email:
                updates.append("email = %s")
                updates.append("is_email_verified = FALSE")
                params.append(email)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(user_id)

                query = f"""
                UPDATE users SET {', '.join(updates)} WHERE id = %s
                RETURNING id, username, email, role, tariff, is_email_verified, created_at, is_blocked,
                          billing_provider, billing_customer_id, billing_subscription_id,
                          subscription_status, subscription_current_period_end
                """
                await cur.execute(query, params)
                user_row = await cur.fetchone()

                if user_row:
                    return {
                        "id": user_row[0],
                        "username": user_row[1],
                        "email": user_row[2],
                        "role": user_row[3],
                        "tariff": user_row[4],
                        "is_email_verified": user_row[5],
                        "created_at": user_row[6],
                        "is_blocked": user_row[7],
                        "billing_provider": user_row[8],
                        "billing_customer_id": user_row[9],
                        "billing_subscription_id": user_row[10],
                        "subscription_status": user_row[11],
                        "subscription_current_period_end": user_row[12],
                    }
            
            # Если ничего не обновлялось, возвращаем текущего пользователя
            return await get_user_by_id(user_id)


async def update_user_role_tariff(
    user_id: int,
    role: Optional[str] = None,
    tariff: Optional[str] = None,
    is_blocked: Optional[bool] = None,
    changed_by_user_id: Optional[int] = None
) -> Dict:
    """Обновление роли, тарифа и/или флага блокировки пользователя (только для администраторов)."""
    if role is None and tariff is None and is_blocked is None:
        return await get_user_by_id(user_id)

    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, role, tariff FROM users WHERE id = %s",
                (user_id,)
            )
            row = await cur.fetchone()
            if not row:
                raise UserNotFoundError("User not found")

            role_old = row[1]
            tariff_old = row[2] or "free"

            updates = []
            params = []

            if role is not None:
                updates.append("role = %s")
                params.append(role)
            if tariff is not None:
                updates.append("tariff = %s")
                params.append(tariff)
            if is_blocked is not None:
                updates.append("is_blocked = %s")
                params.append(is_blocked)

            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(user_id)
                query = f"""
                UPDATE users SET {', '.join(updates)} WHERE id = %s
                RETURNING id, username, email, role, tariff, is_email_verified, created_at, is_blocked,
                          billing_provider, billing_customer_id, billing_subscription_id,
                          subscription_status, subscription_current_period_end
                """
                await cur.execute(query, params)
                user_row = await cur.fetchone()
                if user_row:
                    role_new = user_row[3]
                    tariff_new = user_row[4] or "free"
                    if role is not None or tariff is not None:
                        await cur.execute(
                            """
                            INSERT INTO user_role_tariff_history
                            (user_id, changed_by_user_id, role_old, role_new, tariff_old, tariff_new)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (
                                user_id,
                                changed_by_user_id,
                                role_old,
                                role_new,
                                tariff_old,
                                tariff_new,
                            ),
                        )
                    result = {
                        "id": user_row[0],
                        "username": user_row[1],
                        "email": user_row[2],
                        "role": user_row[3],
                        "tariff": user_row[4],
                        "is_email_verified": user_row[5],
                        "created_at": user_row[6],
                        "is_blocked": user_row[7],
                        "billing_provider": user_row[8],
                        "billing_customer_id": user_row[9],
                        "billing_subscription_id": user_row[10],
                        "subscription_status": user_row[11],
                        "subscription_current_period_end": user_row[12],
                    }
                    if is_blocked is True:
                        await revoke_all_refresh_tokens(user_id)
                    if changed_by_user_id is not None:
                        await log_admin_audit(
                            changed_by_user_id,
                            "user_admin_update",
                            target_type="user",
                            target_id=str(user_id),
                            details={
                                "role": role,
                                "tariff": tariff,
                                "is_blocked": is_blocked,
                            },
                        )
                    return result

    return await get_user_by_id(user_id)


async def get_user_role_tariff_history(user_id: int) -> List[Dict]:
    """Получение истории изменений роли и тарифа пользователя."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, user_id, changed_at, changed_by_user_id,
                       role_old, role_new, tariff_old, tariff_new
                FROM user_role_tariff_history
                WHERE user_id = %s
                ORDER BY changed_at DESC
                """,
                (user_id,),
            )
            rows = await cur.fetchall()
    return [
        {
            "id": r[0],
            "user_id": r[1],
            "changed_at": r[2],
            "changed_by_user_id": r[3],
            "role_old": r[4],
            "role_new": r[5],
            "tariff_old": r[6],
            "tariff_new": r[7],
        }
        for r in rows
    ]


async def initiate_password_reset(email: str) -> str:
    """Инициация сброса пароля (создание токена)."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            user_row = await cur.fetchone()
            
            if not user_row:
                # Не раскрываем информацию о существовании пользователя
                # Все равно создаем токен, но он будет невалидным
                return ""
            
            user_id = user_row[0]
            
            # Создание токена сброса пароля
            reset_token = create_password_reset_token(user_id)
            await save_password_reset_token(user_id, reset_token)
            
            return reset_token


async def get_all_users(
    tariff: Optional[str] = None,
    subscription_status: Optional[str] = None,
) -> list[Dict]:
    """Получение списка пользователей с опциональными фильтрами (админ)."""
    conditions: list[str] = []
    params: list = []
    if tariff:
        conditions.append("tariff = %s")
        params.append(tariff)
    if subscription_status:
        if subscription_status == "__null__":
            conditions.append("subscription_status IS NULL")
        else:
            conditions.append("subscription_status = %s")
            params.append(subscription_status)
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"""
                SELECT id, username, email, role, tariff, is_email_verified, created_at, is_blocked,
                       billing_provider, billing_customer_id, billing_subscription_id,
                       subscription_status, subscription_current_period_end
                FROM users
                {where}
                ORDER BY created_at DESC
                """
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()

            return [
                {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "role": row[3],
                    "tariff": row[4],
                    "is_email_verified": row[5],
                    "created_at": row[6],
                    "is_blocked": row[7],
                    "billing_provider": row[8],
                    "billing_customer_id": row[9],
                    "billing_subscription_id": row[10],
                    "subscription_status": row[11],
                    "subscription_current_period_end": row[12],
                }
                for row in rows
            ]


def export_users_csv_rows(users: list[Dict]) -> str:
    """CSV для экспорта списка пользователей (бухгалтерия / отчёты)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "id",
            "username",
            "email",
            "role",
            "tariff",
            "subscription_status",
            "billing_provider",
            "is_email_verified",
            "is_blocked",
            "created_at",
        ]
    )
    for u in users:
        w.writerow(
            [
                u.get("id"),
                u.get("username"),
                u.get("email"),
                u.get("role"),
                u.get("tariff"),
                u.get("subscription_status") or "",
                u.get("billing_provider") or "",
                u.get("is_email_verified"),
                u.get("is_blocked"),
                u.get("created_at"),
            ]
        )
    return buf.getvalue()

