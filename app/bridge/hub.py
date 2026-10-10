"""Telegram ↔ SMS booking bridge (two-way).

Solves the "international SMS is expensive" problem: tourists chat for FREE over
Telegram (wifi/data); the bridge relays to owners over cheap *local* SMS. The
platform pays only domestic SMS — never international.

Flow
----
    Tourist (Telegram) --inquiry--> Hub --translate EN->owner lang--> SMS to owner
    Owner (SMS) --reply----------> Hub --translate owner lang->EN--> Telegram to tourist

Each tourist↔owner pair is a "thread" identified by a short reference code. The
owner only ever sees normal SMS (prefixed with the code so their reply routes back);
they never need to know Telegram exists. Messages are translated in both directions
using the same Translator the rest of the pipeline uses.

Adapter-agnostic: works with the mock SMS/Telegram adapters for local demos, and
with real gateways later, unchanged.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field

from app.adapters.base import InboundMessage, OutboundMessage, SMSAdapter
from app.adapters.telegram_base import (
    TelegramAdapter,
    TelegramInbound,
    TelegramOutbound,
)
from app.ai.translation import Translator, get_translator


@dataclass
class Thread:
    """One booking conversation between a tourist and an owner."""
    ref: str
    chat_id: str          # tourist's Telegram chat
    owner_phone: str      # owner's SMS number
    owner_lang: str       # amh / orm / eng — for translating messages to the owner
    business_name: str
    messages: list[tuple[str, str]] = field(default_factory=list)  # (who, text)


class BridgeHub:
    def __init__(
        self,
        sms: SMSAdapter,
        telegram: TelegramAdapter,
        translator: Translator | None = None,
    ) -> None:
        self.sms = sms
        self.telegram = telegram
        self.translator = translator or get_translator()
        self._threads: dict[str, Thread] = {}            # ref -> Thread
        self._by_chat: dict[str, str] = {}               # chat_id -> ref (active thread)
        self._by_phone: dict[str, str] = {}              # owner_phone -> ref (latest)
        # wire both inbound directions
        self.telegram.register_handler(self._on_tourist_message)
        self.sms.register_handler(self._on_owner_sms)

    # ---------------------------------------------------------------- start

    def start_inquiry(
        self, chat_id: str, owner_phone: str, owner_lang: str, business_name: str
    ) -> Thread:
        """Begin (or reuse) a booking thread for a tourist about a specific business.

        Called when a tourist taps "Message on Telegram" for a listing. The website
        link carries the business so the bot knows which owner to connect.
        """
        existing_ref = self._by_chat.get(chat_id)
        if existing_ref and self._threads[existing_ref].owner_phone == owner_phone:
            return self._threads[existing_ref]
        ref = self._new_ref()
        thread = Thread(ref=ref, chat_id=chat_id, owner_phone=owner_phone,
                        owner_lang=owner_lang, business_name=business_name)
        self._threads[ref] = thread
        self._by_chat[chat_id] = ref
        self._by_phone[owner_phone] = ref
        # Greet the tourist on Telegram.
        self.telegram.send(TelegramOutbound(
            chat_id=chat_id,
            text=(f"You're now connected to {business_name}. Type your question or "
                  f"booking request and we'll pass it on. (Ref {ref})"),
        ))
        return thread

    # ---------------------------------------------------------------- tourist -> owner

    def _on_tourist_message(self, msg: TelegramInbound) -> list[TelegramOutbound]:
        ref = self._by_chat.get(msg.chat_id)
        if not ref:
            return [TelegramOutbound(
                chat_id=msg.chat_id,
                text=("Please open a business listing and tap 'Message on Telegram' "
                      "to start an inquiry."),
            )]
        thread = self._threads[ref]
        thread.messages.append(("tourist", msg.text))

        # Translate the tourist's English into the owner's language for the SMS.
        translated = self.translator.translate(msg.text, "eng", thread.owner_lang).text
        # Local SMS to the owner, tagged with the ref so their reply routes back.
        self.sms.send(OutboundMessage(
            recipient=thread.owner_phone,
            text=f"[{ref}] Tourist inquiry for {thread.business_name}: {translated}\n"
                 f"(Reply to this SMS to respond.)",
        ))
        # Acknowledge to the tourist.
        return [TelegramOutbound(
            chat_id=msg.chat_id,
            text="✓ Sent to the business. We'll relay their reply here.",
        )]

    # ---------------------------------------------------------------- owner -> tourist

    def _on_owner_sms(self, msg: InboundMessage) -> list[OutboundMessage]:
        """An owner replied by SMS. Route it back to the right tourist's Telegram.

        We match the thread by an explicit [ref] in the text if present, otherwise by
        the owner's phone number (their most recent thread).
        """
        ref = self._extract_ref(msg.text) or self._by_phone.get(msg.sender)
        if not ref or ref not in self._threads:
            # Not part of a bridge conversation (e.g. an onboarding SMS) — ignore here.
            return []
        thread = self._threads[ref]
        body = self._strip_ref(msg.text)
        thread.messages.append(("owner", body))

        # Translate the owner's reply (their language) back into English for the tourist.
        translated = self.translator.translate(body, thread.owner_lang, "eng").text
        self.telegram.send(TelegramOutbound(
            chat_id=thread.chat_id,
            text=f"💬 {thread.business_name} replied: {translated}",
        ))
        # No SMS reply back to the owner needed.
        return []

    # ---------------------------------------------------------------- helpers

    def thread_for_chat(self, chat_id: str) -> Thread | None:
        ref = self._by_chat.get(chat_id)
        return self._threads.get(ref) if ref else None

    def _on_owner_sms_text(self, sender: str, text: str) -> list[OutboundMessage]:
        """Convenience: route a raw owner SMS (sender + text) through the bridge."""
        return self._on_owner_sms(InboundMessage(sender=sender, text=text))

    def _new_ref(self) -> str:
        while True:
            ref = secrets.token_hex(2).upper()  # e.g. "A3F9"
            if ref not in self._threads:
                return ref

    @staticmethod
    def _extract_ref(text: str) -> str | None:
        import re
        m = re.search(r"\[([0-9A-Fa-f]{4})\]", text)
        return m.group(1).upper() if m else None

    @staticmethod
    def _strip_ref(text: str) -> str:
        import re
        return re.sub(r"^\s*\[[0-9A-Fa-f]{4}\]\s*", "", text).strip()
