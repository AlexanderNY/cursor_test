"""SMTP helper for billing invoices. Optional: without SMTP_HOST mail is not sent."""

from __future__ import annotations

import logging
from email.message import EmailMessage

import aiosmtplib

from config import settings

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool((settings.SMTP_HOST or "").strip() and (settings.SMTP_FROM or "").strip())


async def send_plain_email(*, to_email: str, subject: str, body: str) -> bool:
    """Send a plaintext email. Returns True if accepted by SMTP."""
    if not smtp_configured():
        logger.warning("SMTP is not configured; skip send to %s", to_email)
        return False
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM.strip()
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST.strip(),
            port=int(settings.SMTP_PORT or 587),
            username=(settings.SMTP_USER or "").strip() or None,
            password=(settings.SMTP_PASSWORD or "").strip() or None,
            start_tls=bool(settings.SMTP_STARTTLS),
        )
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        raise
