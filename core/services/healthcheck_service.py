"""Сервис для проверки здоровья всех сервисов."""

import httpx
from typing import List, Dict
from config import settings


class HealthcheckService:
    """Сервис для опроса healthcheck всех микросервисов."""
    
    def __init__(self):
        self.services = {
            "auth": settings.AUTH_SERVICE_URL,
            "core": "http://localhost:8002",  # self
            "api-gateway": settings.API_GATEWAY_URL,
            "tg-bot": settings.TG_BOT_SERVICE_URL,
            "vk-bot": settings.VK_BOT_SERVICE_URL,
            "wp-bot": settings.WP_BOT_SERVICE_URL,
            "url-bot": settings.URL_BOT_SERVICE_URL,
            "tw-bot": settings.TW_BOT_SERVICE_URL,
            "scheduler": settings.SCHEDULER_SERVICE_URL,
            "collector": settings.COLLECTOR_SERVICE_URL,
            "processor": settings.PROCESSOR_SERVICE_URL,
        }
    
    async def check_service(self, name: str, url: str) -> Dict:
        """Проверяет здоровье одного сервиса.
        
        Args:
            name: Имя сервиса
            url: URL сервиса
            
        Returns:
            Словарь с результатом проверки
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    data = response.json() if response.content else {}
                    server_time = data.get("server_time") if isinstance(data, dict) else None
                    return {
                        "service_name": name,
                        "status": "ok",
                        "error": None,
                        "server_time": server_time,
                    }
                else:
                    return {
                        "service_name": name,
                        "status": "error",
                        "error": f"HTTP {response.status_code}"
                    }
        except httpx.ConnectError:
            return {
                "service_name": name,
                "status": "error",
                "error": "Connection refused"
            }
        except httpx.TimeoutException:
            return {
                "service_name": name,
                "status": "error",
                "error": "Timeout"
            }
        except Exception as e:
            return {
                "service_name": name,
                "status": "error",
                "error": str(e)
            }
    
    async def check_all_services(self) -> List[Dict]:
        """Проверяет здоровье всех сервисов.
        
        Returns:
            Список результатов проверки всех сервисов
        """
        results = []
        for name, url in self.services.items():
            result = await self.check_service(name, url)
            results.append(result)
        return results


healthcheck_service = HealthcheckService()
