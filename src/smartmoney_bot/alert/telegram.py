from __future__ import annotations

import os

import aiohttp
import structlog

log = structlog.get_logger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


async def send_message(text: str) -> None:
    if not TELEGRAM_TOKEN or not CHAT_ID:
        log.info("telegram_not_configured")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(url, json={"chat_id": CHAT_ID, "text": text})
        except Exception as exc:  # pragma: no cover - network issues
            log.error("telegram_send_failed", error=str(exc))
