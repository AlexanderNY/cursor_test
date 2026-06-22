"""Сервис для отправки уведомлений через core API."""

import logging
import httpx
from config import settings


logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений пользователям."""
    
    def __init__(self):
        """Инициализация сервиса."""
        self.core_url = settings.CORE_SERVICE_URL
    
    async def send_notification(
        self,
        user_id: int,
        message: str,
        notif_type: str = "general"
    ) -> bool:
        """Отправляет уведомление пользователю через core API.
        
        Args:
            user_id: ID пользователя
            message: Текст уведомления
            notif_type: Тип уведомления (general, tg_auth_code, tg_auth_2fa, tg_auth_error)
            
        Returns:
            True если уведомление отправлено успешно, False иначе
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.core_url}/notifications",
                    json={"message": message, "user_id": user_id, "type": notif_type},
                    headers={
                        "X-User-Id": str(user_id),
                        "X-User-Role": "admin"
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"Notification sent to user {user_id}")
                    return True
                else:
                    logger.warning(
                        f"Failed to send notification to user {user_id}: "
                        f"{response.status_code} {response.text}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}", exc_info=True)
            return False
    
    async def send_authorization_notification(
        self,
        user_id: int,
        phone_number: str
    ) -> bool:
        """Отправляет уведомление о необходимости ввести код.
        
        Args:
            user_id: ID пользователя
            phone_number: Номер телефона для авторизации
            
        Returns:
            True если уведомление отправлено успешно
        """
        message = (
            f"Telegram авторизация: код подтверждения отправлен "
            f"на номер {phone_number}. "
            f'<a href="/telegram?auth=1" style="color:#60a5fa;text-decoration:underline">'
            f"Введите код на странице Telegram</a>."
        )
        return await self.send_notification(user_id, message, notif_type="tg_auth_code")
    
    async def send_2fa_notification(self, user_id: int) -> bool:
        """Отправляет уведомление о необходимости ввести 2FA пароль.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если уведомление отправлено успешно
        """
        message = (
            "Telegram авторизация: требуется ввести пароль "
            "двухфакторной аутентификации. "
            '<a href="/telegram?auth=1" style="color:#60a5fa;text-decoration:underline">'
            "Введите пароль на странице Telegram</a>."
        )
        return await self.send_notification(user_id, message, notif_type="tg_auth_2fa")
    
    async def send_error_notification(
        self,
        user_id: int,
        error_message: str
    ) -> bool:
        """Отправляет уведомление об ошибке авторизации.
        
        Args:
            user_id: ID пользователя
            error_message: Текст ошибки
            
        Returns:
            True если уведомление отправлено успешно
        """
        message = f"Telegram авторизация: {error_message}"
        return await self.send_notification(user_id, message, notif_type="tg_auth_error")


notification_service = NotificationService()
