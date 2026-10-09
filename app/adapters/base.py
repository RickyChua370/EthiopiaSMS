"""Gateway-agnostic SMS adapter interface.

The rest of the system depends ONLY on this interface, never on a concrete
gateway. Swap MockAdapter (local/dev) for AfricasTalkingAdapter or TwilioAdapter
by changing one line of configuration — no core code changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


@dataclass
class InboundMessage:
    """A message received FROM a business owner."""
    sender: str   # the owner's phone number (E.164, e.g. +2519...)
    text: str     # the raw message body


@dataclass
class OutboundMessage:
    """A message to send TO a business owner."""
    recipient: str
    text: str


# A handler takes an inbound message and returns the reply(ies) to send back.
MessageHandler = Callable[[InboundMessage], list[OutboundMessage]]


class SMSAdapter(ABC):
    """Abstract SMS gateway. Concrete adapters implement send() and inbound routing."""

    @abstractmethod
    def send(self, message: OutboundMessage) -> None:
        """Deliver one outbound SMS."""

    @abstractmethod
    def register_handler(self, handler: MessageHandler) -> None:
        """Register the function that processes inbound messages."""
