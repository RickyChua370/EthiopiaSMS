"""Mock Telegram adapter — simulates the tourist's Telegram chat locally.

Outbound messages (to the tourist) are collected instead of hitting Telegram's API.
Inbound messages (from the tourist) are injected via `receive()` by the simulator
or tests. No bot token or network needed — mirrors MockAdapter for SMS.
"""

from __future__ import annotations

from .telegram_base import (
    TelegramAdapter,
    TelegramHandler,
    TelegramInbound,
    TelegramOutbound,
)


class MockTelegramAdapter(TelegramAdapter):
    def __init__(self, echo: bool = False) -> None:
        self._handler: TelegramHandler | None = None
        self.outbox: list[TelegramOutbound] = []
        self._echo = echo

    def send(self, message: TelegramOutbound) -> None:
        self.outbox.append(message)
        if self._echo:
            print(f"  💬 → tourist[{message.chat_id}]: {message.text}")

    def register_handler(self, handler: TelegramHandler) -> None:
        self._handler = handler

    def receive(self, chat_id: str, text: str) -> list[TelegramOutbound]:
        """Inject an inbound tourist message; return replies sent back to the tourist."""
        if self._handler is None:
            raise RuntimeError("No handler registered on MockTelegramAdapter")
        replies = self._handler(TelegramInbound(chat_id=chat_id, text=text))
        for reply in replies:
            self.send(reply)
        return replies
