"""Async SMTP email service."""
from __future__ import annotations
import logging
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.src.infrastructure.config import settings

logger = logging.getLogger(__name__)


async def send_reset_email(to_email: str, reset_url: str) -> None:
    if not settings.smtp_host:
        logger.info("SMTP not configured — skipping password reset email")
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = "Gym Jam — Reset your password"
    message["From"] = settings.smtp_from
    message["To"] = to_email

    text = f"Open this link to reset your password (expires in 15 minutes):\n\n{reset_url}"
    html = f"""<p>Click the link below to reset your password (expires in 15 minutes):</p>
<p><a href="{reset_url}">{reset_url}</a></p>"""

    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user or None,
        password=settings.smtp_password or None,
        start_tls=True,
    )
