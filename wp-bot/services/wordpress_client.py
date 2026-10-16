"""Клиент для работы с WordPress REST API."""

import logging
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import httpx

from shared import async_fs

logger = logging.getLogger(__name__)


def normalize_app_password(value: Optional[str]) -> str:
    """Application Password is shown in groups; spaces are not part of the secret."""
    return "".join((value or "").split())


class WordPressClient:
    """Клиент для работы с WordPress REST API."""

    def __init__(
        self,
        site_url: str,
        username: Optional[str] = None,
        app_password: Optional[str] = None,
    ):
        """
        Инициализация клиента.

        Args:
            site_url: URL сайта WordPress
            username: Имя пользователя (optional for public reads)
            app_password: Application Password (optional for public reads)
        """
        self.site_url = site_url.rstrip("/")
        self.username = (username or "").strip()
        self.app_password = normalize_app_password(app_password)
        self.base_url = f"{self.site_url}/wp-json/wp/v2"

    @property
    def has_auth(self) -> bool:
        return bool(self.username and self.app_password)

    def _auth(self) -> Optional[Tuple[str, str]]:
        if not self.has_auth:
            return None
        return (self.username, self.app_password)

    def _require_auth(self) -> Tuple[str, str]:
        auth = self._auth()
        if not auth:
            raise ValueError("WordPress username and application password are required")
        return auth

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
        meta: Optional[Dict[str, Any]] = None,
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
        auth = self._require_auth()

        post_data: Dict[str, Any] = {
            "title": title,
            "content": content,
            "status": status,
        }

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
                    auth=auth,
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
                except Exception:
                    error_detail = "Invalid request data"

            raise Exception(f"WordPress API error ({e.response.status_code}): {error_detail}")
        except httpx.RequestError as e:
            raise Exception(f"Request to WordPress failed: {str(e)}")

    async def get_posts(
        self,
        per_page: int = 10,
        page: int = 1,
        status: Optional[str] = None,
        after: Optional[str] = None,
        orderby: str = "date",
        order: str = "desc",
        fields: Optional[str] = None,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Получает список постов из WordPress.

        Args:
            per_page: Количество постов на странице
            page: Номер страницы
            status: Статус постов (publish, draft, etc.)
            after: Дата после которой получать посты (ISO 8601)
            orderby: Поле сортировки
            order: asc | desc
            fields: WP REST `_fields` comma-separated list
            context: `edit` returns title/content.raw when Application Password is valid

        Returns:
            Словарь с данными постов и пагинацией
        """
        params: Dict[str, Any] = {
            "per_page": per_page,
            "page": page,
            "orderby": orderby,
            "order": order,
        }

        if status:
            params["status"] = status
        if after:
            params["after"] = after
        if fields:
            params["_fields"] = fields
        if context:
            params["context"] = context

        auth = self._auth()
        try:
            return await self._fetch_posts(params, auth, page=page, per_page=per_page)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 and auth is not None:
                logger.warning(
                    "WordPress get_posts auth failed for %s, retrying public REST",
                    self.site_url,
                )
                public_params = dict(params)
                public_params.pop("context", None)
                try:
                    return await self._fetch_posts(
                        public_params, None, page=page, per_page=per_page
                    )
                except httpx.HTTPStatusError as retry_error:
                    raise Exception(
                        "WordPress API error "
                        f"({retry_error.response.status_code}): Failed to get posts"
                    ) from retry_error
                except httpx.RequestError as retry_error:
                    raise Exception(
                        f"Request to WordPress failed: {retry_error}"
                    ) from retry_error
            raise Exception(
                f"WordPress API error ({e.response.status_code}): Failed to get posts"
            ) from e
        except httpx.RequestError as e:
            raise Exception(f"Request to WordPress failed: {str(e)}") from e

    async def _fetch_posts(
        self,
        params: Dict[str, Any],
        auth: Optional[Tuple[str, str]],
        *,
        page: int,
        per_page: int,
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/posts",
                params=params,
                auth=auth,
            )
            response.raise_for_status()

        total_posts = int(response.headers.get("X-WP-Total", 0))
        total_pages = int(response.headers.get("X-WP-TotalPages", 0))
        return {
            "posts": response.json(),
            "total": total_posts,
            "total_pages": total_pages,
            "page": page,
            "per_page": per_page,
        }

    async def get_page(self, page_id: int) -> Dict[str, Any]:
        """GET /wp/v2/pages/{id}."""
        auth = self._require_auth()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/pages/{int(page_id)}",
                    auth=auth,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(
                f"WordPress API error ({e.response.status_code}): Failed to get page"
            )
        except httpx.RequestError as e:
            raise Exception(f"Request to WordPress failed: {str(e)}")

    async def get_page_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """GET /wp/v2/pages?slug=… — first match or None."""
        auth = self._require_auth()
        cleaned = str(slug or "").strip()
        if not cleaned:
            return None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/pages",
                    params={"slug": cleaned, "per_page": 1},
                    auth=auth,
                )
                response.raise_for_status()
                pages = response.json()
                if isinstance(pages, list) and pages:
                    return pages[0]
                return None
        except httpx.HTTPStatusError as e:
            raise Exception(
                f"WordPress API error ({e.response.status_code}): Failed to get page by slug"
            )
        except httpx.RequestError as e:
            raise Exception(f"Request to WordPress failed: {str(e)}")

    async def update_page(
        self,
        page_id: int,
        *,
        title: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """POST /wp/v2/pages/{id} — update page fields (needs edit_pages)."""
        auth = self._require_auth()
        body: Dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if content is not None:
            body["content"] = content
        if status is not None:
            body["status"] = status
        if not body:
            raise ValueError("At least one of title, content, status is required")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/pages/{int(page_id)}",
                    json=body,
                    headers={"Content-Type": "application/json"},
                    auth=auth,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = "Failed to update page"
            if e.response.status_code == 401:
                error_detail = "Authentication failed. Check username and application password."
            elif e.response.status_code == 403:
                error_detail = "Permission denied. User may not have edit_pages capability."
            elif e.response.status_code == 404:
                error_detail = f"Page {page_id} not found"
            else:
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get("message", error_detail)
                except Exception:
                    pass
            raise Exception(f"WordPress API error ({e.response.status_code}): {error_detail}")
        except httpx.RequestError as e:
            raise Exception(f"Request to WordPress failed: {str(e)}")

    async def get_categories(self) -> list[Dict[str, Any]]:
        """Получает список категорий."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/categories",
                    auth=self._auth(),
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(
                f"WordPress API error ({e.response.status_code}): Failed to get categories"
            )
        except httpx.RequestError as e:
            raise Exception(f"Request to WordPress failed: {str(e)}")

    async def get_tags(self) -> list[Dict[str, Any]]:
        """Получает список тегов."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/tags",
                    auth=self._auth(),
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(
                f"WordPress API error ({e.response.status_code}): Failed to get tags"
            )
        except httpx.RequestError as e:
            raise Exception(f"Request to WordPress failed: {str(e)}")

    async def upload_media(
        self,
        file_path: str,
        title: Optional[str] = None,
        alt_text: Optional[str] = None,
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
        auth = self._require_auth()
        try:
            content = await async_fs.read_bytes(file_path)
            filename = Path(file_path).name
            files = {"file": (filename, BytesIO(content))}
            data: Dict[str, Any] = {}
            if title:
                data["title"] = title
            if alt_text:
                data["alt_text"] = alt_text

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/media",
                    files=files,
                    data=data,
                    auth=auth,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(
                f"WordPress API error ({e.response.status_code}): Failed to upload media"
            )
        except httpx.RequestError as e:
            raise Exception(f"Request to WordPress failed: {str(e)}")
        except FileNotFoundError:
            raise Exception(f"File not found: {file_path}")
