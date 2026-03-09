from __future__ import annotations

import httpx


class TelegramClientError(RuntimeError):
    pass


class TelegramClient:
    def __init__(self, api_base_url: str, bot_token: str, chat_id: str, timeout_seconds: int = 20) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout_seconds = timeout_seconds

    async def send_message(self, text: str) -> None:
        url = f"{self.api_base_url}/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TelegramClientError(f"Telegram sendMessage failed: {exc}") from exc
