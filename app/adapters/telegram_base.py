"""Gateway-agnostic Telegram adapter interface (tourist side).

Mirrors the SMS adapter design: the bridge depends only on this interface, never on
a concrete Telegram client. Swap MockTelegramAdapter (local/dev) for a real
python-telegram-bot adapter later with no change to the bridge logic.

Tourists are the online, connected party — they chat for free over Telegram
(wifi/data). The bridge relays their messages to owners over cheap *local* SMS, so
no expensive international SMS is ever involved.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


@dataclass
class TelegramInbound:
    """A message received FROM a tourist on Telegram."""
    chat_id: str          # Telegram chat identifier (one per tourist conversation)
    text: str


@dataclass
class TelegramOutbound:
    """A message to send TO a tourist on Telegram."""
    chat_id: str
    text: str


TelegramHandler = Callable[[TelegramInbound], list[TelegramOutbound]]


class TelegramAdapter(ABC):
    @abstractmethod
    def send(self, message: TelegramOutbound) -> None:
        """Deliver one outbound Telegram message to a tourist."""

    @abstractmethod
    def register_handler(self, handler: TelegramHandler) -> None:
        """Register the function that processes inbound tourist messages."""
