"""
S3-совместимое хранилище (MinIO, AWS S3, Yandex Object Storage).
Единый интерфейс: put(key, body), get_presigned_url(key), get_bytes(key), list_objects(prefix).
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Optional: aioboto3 only when S3 is configured
_aioboto3 = None


def _get_aioboto3():
    global _aioboto3
    if _aioboto3 is None:
        try:
            import aioboto3
            _aioboto3 = aioboto3
        except ImportError:
            raise ImportError("aioboto3 is required for S3 storage. Install: pip install aioboto3")
    return _aioboto3


class S3Storage:
    """Асинхронное хранилище файлов в S3-совместимом бакете."""

    def __init__(
        self,
        bucket: str,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region_name: str = "us-east-1",
        use_ssl: bool = True,
    ):
        self.bucket = bucket
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.region_name = region_name
        self.use_ssl = use_ssl
        self._session = None

    def _client_kwargs(self) -> dict:
        kwargs = {
            "service_name": "s3",
            "region_name": self.region_name,
            "aws_access_key_id": self.access_key or "",
            "aws_secret_access_key": self.secret_key or "",
        }
        if self.endpoint_url:
            kwargs["endpoint_url"] = self.endpoint_url
        return kwargs

    async def _ensure_bucket(self, client) -> None:
        """Создаёт бакет, если его нет (для MinIO)."""
        try:
            await client.head_bucket(Bucket=self.bucket)
        except client.exceptions.ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("404", "NoSuchBucket"):
                try:
                    await client.create_bucket(Bucket=self.bucket)
                    logger.info("Created S3 bucket %s", self.bucket)
                except Exception as create_err:
                    logger.warning("Could not create bucket %s: %s", self.bucket, create_err)
            else:
                raise

    async def put(self, key: str, body: bytes, content_type: Optional[str] = None) -> None:
        """Загружает объект в бакет."""
        key = key.lstrip("/")
        if not key:
            raise ValueError("Storage key cannot be empty")
        aioboto3 = _get_aioboto3()
        session = aioboto3.Session()
        async with session.client(**self._client_kwargs()) as client:
            await self._ensure_bucket(client)
            extra = {}
            if content_type:
                extra["ContentType"] = content_type
            await client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=body,
                **extra,
            )
        logger.debug("Stored object s3://%s/%s", self.bucket, key)

    async def get_bytes(self, key: str) -> Optional[bytes]:
        """Скачивает объект и возвращает байты. None если объект не найден."""
        key = key.lstrip("/")
        if not key:
            return None
        aioboto3 = _get_aioboto3()
        session = aioboto3.Session()
        try:
            async with session.client(**self._client_kwargs()) as client:
                resp = await client.get_object(Bucket=self.bucket, Key=key)
                body = await resp["Body"].read()
                return body
        except Exception as e:
            try:
                from botocore.exceptions import ClientError
                if isinstance(e, ClientError):
                    code = (e.response or {}).get("Error", {}).get("Code", "")
                    if code in ("404", "NoSuchKey"):
                        return None
            except ImportError:
                pass
            logger.debug("get_bytes failed for key=%s: %s", key, e, exc_info=True)
            raise

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """Возвращает presigned URL для скачивания. None при ошибке."""
        key = key.lstrip("/")
        if not key:
            return None
        aioboto3 = _get_aioboto3()
        session = aioboto3.Session()
        try:
            async with session.client(**self._client_kwargs()) as client:
                url = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": key},
                    ExpiresIn=expires_in,
                )
                return url
        except Exception as e:
            logger.warning("get_presigned_url failed for key=%s: %s", key, e)
            return None

    async def exists(self, key: str) -> bool:
        """Проверяет существование объекта."""
        key = key.lstrip("/")
        if not key:
            return False
        aioboto3 = _get_aioboto3()
        session = aioboto3.Session()
        try:
            async with session.client(**self._client_kwargs()) as client:
                await client.head_object(Bucket=self.bucket, Key=key)
                return True
        except Exception:
            return False

    async def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000,
        continuation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Список объектов в бакете. Возвращает dict с ключами:
        - objects: список {key, size, last_modified} (last_modified — ISO строка или None)
        - next_continuation_token: str | None для пагинации
        """
        prefix = (prefix or "").lstrip("/")
        aioboto3 = _get_aioboto3()
        session = aioboto3.Session()
        result: List[Dict[str, Any]] = []
        next_token: Optional[str] = None
        async with session.client(**self._client_kwargs()) as client:
            params = {
                "Bucket": self.bucket,
                "MaxKeys": min(max_keys, 1000),
            }
            if prefix:
                params["Prefix"] = prefix
            if continuation_token:
                params["ContinuationToken"] = continuation_token
            resp = await client.list_objects_v2(**params)
            for obj in resp.get("Contents") or []:
                key = obj.get("Key")
                if key is None:
                    continue
                result.append({
                    "key": key,
                    "size": obj.get("Size", 0) or 0,
                    "last_modified": obj.get("LastModified").isoformat() if obj.get("LastModified") else None,
                })
            next_token = resp.get("NextContinuationToken")
        return {"objects": result, "next_continuation_token": next_token}

    async def delete_object(self, key: str) -> None:
        """Удаляет объект по ключу. Ошибка, если ключ пустой."""
        key = key.lstrip("/")
        if not key:
            raise ValueError("Storage key cannot be empty")
        aioboto3 = _get_aioboto3()
        session = aioboto3.Session()
        async with session.client(**self._client_kwargs()) as client:
            await client.delete_object(Bucket=self.bucket, Key=key)
        logger.info("Deleted object s3://%s/%s", self.bucket, key)


# Глобальный экземпляр (инициализируется из конфига при первом обращении)
_storage_instance: Optional[S3Storage] = None


def get_storage(
    bucket: str = "",
    endpoint_url: Optional[str] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    region_name: str = "us-east-1",
    use_ssl: bool = True,
) -> Optional[S3Storage]:
    """Возвращает экземпляр S3Storage при заданных параметрах, иначе None (хранилище отключено)."""
    if not bucket or not access_key or not secret_key:
        return None
    return S3Storage(
        bucket=bucket,
        endpoint_url=endpoint_url or None,
        access_key=access_key,
        secret_key=secret_key,
        region_name=region_name,
        use_ssl=use_ssl,
    )
