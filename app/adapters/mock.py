"""Mock SMS adapter — simulates sending/receiving SMS locally, no account needed.

Outbound messages are collected (and optionally printed) instead of being sent over
a real network. Inbound messages are injected programmatically (by the CLI/web
simulator or tests), routed to the registered handler, and the replies captured.
"""

from __future__ import annotations

from .base import InboundMessage, MessageHandler, OutboundMessage, SMSAdapter


class MockAdapter(SMSAdapter):
    def __init__(self, echo: bool = False) -> None:
        self._handler: MessageHandler | None = None
        self.outbox: list[OutboundMessage] = []
        self._echo = echo

    def send(self, message: OutboundMessage) -> None:
        self.outbox.append(message)
        if self._echo:
            print(f"  📱 → {message.recipient}: {message.text}")

    def register_handler(self, handler: MessageHandler) -> None:
        self._handler = handler

    # --- test / simulator helpers -------------------------------------------

    def receive(self, sender: str, text: str) -> list[OutboundMessage]:
        """Inject an inbound SMS and return the replies the system produced."""
        if self._handler is None:
            raise RuntimeError("No handler registered on MockAdapter")
        msg = InboundMessage(sender=sender, text=text)
        replies = self._handler(msg)
        for reply in replies:
            self.send(reply)
        return replies
