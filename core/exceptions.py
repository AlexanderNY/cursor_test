"""Исключения домена Core."""


class QuotaExceededError(Exception):
    """Превышена квота тарифа (например, постов в месяц)."""

    def __init__(
        self,
        *,
        resource: str,
        limit: int,
        used: int,
        message: str | None = None,
    ) -> None:
        self.resource = resource
        self.limit = limit
        self.used = used
        super().__init__(message or f"Quota exceeded for {resource}: {used}/{limit}")
