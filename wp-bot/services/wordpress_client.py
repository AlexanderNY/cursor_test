"""Клиент для работы с WordPress REST API."""

import httpx
from typing import Optional, Dict, Any


class WordPressClient:
    """Клиент для работы с WordPress REST API."""
    
    def __init__(self, site_url: str, username: str, app_password: str):
        """
        Инициализация клиента.
        
        Args:
            site_url: URL сайта WordPress
            username: Имя пользователя
            app_password: Application Password
        """
        self.site_url = site_url.rstrip('/')
        self.username = username
        self.app_password = app_password
        self.base_url = f"{self.site_url}/wp-json/wp/v2"
    
    async def create_post(
        self,
        title: str,
        content: str,
        status: str = "publish",
        categories: Optional[list[int]] = None,
        tags: Optional[list[int]] = None,
        excerpt: Optional[str] = None,
        slug: Optional[str] = None,
        featured_media: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Создает пост в WordPress.
        
        Args:
            title: Заголовок поста (обязательно)
            content: Содержимое поста (обязательно)
            status: Статус (draft, publish, pending, private)
            categories: Список ID категорий
            tags: Список ID тегов
            excerpt: Краткое описание
            slug: URL slug
            featured_media: ID медиа-файла
            meta: Дополнительные мета-поля
            
        Returns:
            Данные созданного поста
            
        Raises:
            ValueError: При отсутствии обязательных полей
            httpx.HTTPStatusError: При ошибке HTTP запроса
            httpx.RequestError: При ошибке сетевого запроса
        """
        if not title or not content:
            raise ValueError("Title and content are required")
        
        post_data = {
            "title": title,
            "content": content,
            "status": status,
        }
        
        # Добавляем опциональные поля только если они указаны
        if excerpt:
            post_data["excerpt"] = excerpt
        if slug:
            post_data["slug"] = slug
        if categories:
            post_data["categories"] = categories
        if tags:
            post_data["tags"] = tags
        if featured_media:
            post_data["featured_media"] = featured_media
        if meta:
            post_data["meta"] = meta
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/posts",
                    json=post_data,
                    headers={"Content-Type": "application/json"},
                    auth=(self.username, self.app_password),
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            if e.response.status_code == 401:
                error_detail = "Authentication failed. Check username and application password."
            elif e.response.status_code == 403:
                error_detail = "Permission denied. User may not have permission to create posts."
            elif e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get("message", "Invalid request data")
                except:
                    error_detail = "Invalid request data"
            
            raise Exception(f"WordPress API error ({e.response.status_code}): {error_detail}")
        except httpx.RequestError as e:
            raise Exception(f"Request to WordPress failed: {str(e)}")
    
    async def get_posts(
        self,
        per_page: int = 10,
        page: int = 1,
        status: Optional[str] = None,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получает список постов из WordPress.
        
        Args:
            per_page: Количество постов на странице
            page: Номер страницы
            status: Статус постов (publish, draft, etc.)
            after: Дата после которой получать посты (ISO 8601)
            
        Returns:
            Словарь с данными постов и пагинацией
        """
        params = {
            "per_page": per_page,
            "page": page,
        }
        
        if status:
            params["status"] = status
        if after:
            params["after"] = after
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/posts",
                    params=params,
                    auth=(self.username, self.app_password),
                )
                response.raise_for_status()
                
                # Получаем заголовки пагинации
                total_posts = int(response.headers.get("X-WP-Total", 0))
                total_pages = int(response.headers.get("X-WP-TotalPages", 0))
                
                return {
                    "posts": response.json(),
                    "total": total_posts,
                    "total_pages": total_pages,
                    "page": page,
                    "per_page": per_page
                }
        except httpx.HTTPStatusError as e:
            raise Exception(f"WordPress API error ({e.response.status_code}): Failed to get posts")
        except httpx.RequestError as e:
            raise Exception(f"Request to WordPress failed: {str(e)}")
    
    async def get_categories(self) -> list[Dict[str, Any]]:
        """Получает список категорий."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/categories",
                    auth=(self.username, self.app_password),
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"WordPress API error ({e.response.status_code}): Failed to get categories")
        except httpx.RequestError as e:
            raise Exception(f"Request to WordPress failed: {str(e)}")
    
    async def get_tags(self) -> list[Dict[str, Any]]:
        """Получает список тегов."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/tags",
                    auth=(self.username, self.app_password),
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"WordPress API error ({e.response.status_code}): Failed to get tags")
        except httpx.RequestError as e:
            raise Exception(f"Request to WordPress failed: {str(e)}")
    
    async def upload_media(
        self,
        file_path: str,
        title: Optional[str] = None,
        alt_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Загружает медиа-файл в WordPress.
        
        Args:
            file_path: Путь к файлу
            title: Заголовок медиа-файла
            alt_text: Альтернативный текст
            
        Returns:
            Данные загруженного медиа-файла
        """
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                data = {}
                if title:
                    data["title"] = title
                if alt_text:
                    data["alt_text"] = alt_text
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.base_url}/media",
                        files=files,
                        data=data,
                        auth=(self.username, self.app_password),
                    )
                    response.raise_for_status()
                    return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"WordPress API error ({e.response.status_code}): Failed to upload media")
        except httpx.RequestError as e:
            raise Exception(f"Request to WordPress failed: {str(e)}")
        except FileNotFoundError:
            raise Exception(f"File not found: {file_path}")
