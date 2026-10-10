"""Run the LIVE Telegram bot wired to the bridge, with a MOCK owner you control.

This lets real people message your Telegram bot (tourist side) while you play the
business owner from your terminal (owner side) — no telecom account needed.

Setup:
    1. Get a bot token from @BotFather in Telegram.
    2. export TELEGRAM_BOT_TOKEN=<your token>   (Windows: $env:TELEGRAM_BOT_TOKEN=...)
    3. python -m app.telegram_bridge

Then open your bot in Telegram and send /start. Whatever a tourist sends appears in
this terminal as an SMS to the "owner"; type the owner's reply here and it goes back
to the tourist's Telegram chat — translated both ways.

A tourist can also deep-link from the website button (t.me/<bot>?start=<token>),
which auto-connects them to that specific business.
"""

from __future__ import annotations

import os
import threading

from app.adapters.base import InboundMessage, OutboundMessage, SMSAdapter, MessageHandler
from app.adapters.telegram_live import LiveTelegramAdapter
from app.adapters.telegram_base import TelegramInbound, TelegramOutbound
from app.bridge.hub import BridgeHub

# A demo "owner" the tourist is connected to (mock SMS side).
DEMO_OWNER_PHONE = "+251911223344"
DEMO_OWNER_LANG = "amh"            # the owner's language (messages to them are translated to this)
DEMO_BUSINESS = "Tomoca Coffee"


class PrintingMockSMS(SMSAdapter):
    """Mock SMS gateway that prints outbound 'SMS to owner' to the terminal and lets
    you type the owner's replies back in."""

    def __init__(self) -> None:
        self._handler: MessageHandler | None = None

    def send(self, message: OutboundMessage) -> None:
        print(f"\n  ✉️  SMS to OWNER [{message.recipient}]:")
        print(f"      {message.text}")
        print("  (type the owner's reply with  o: <text>  below)\n")

    def register_handler(self, handler: MessageHandler) -> None:
        self._handler = handler

    def owner_says(self, sender: str, text: str) -> None:
        if self._handler:
            self._handler(InboundMessage(sender=sender, text=text))


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN first (see module docstring).")

    sms = PrintingMockSMS()
    telegram = LiveTelegramAdapter(token=token)
    hub = BridgeHub(sms, telegram)

    # Wrap the tourist handler so a /start (optionally with a business token) opens a
    # thread before the normal bridge logic runs.
    original_handler = telegram._handler  # set by BridgeHub

    def tourist_handler(msg: TelegramInbound):
        text = msg.text.strip()
        if text.startswith("/start"):
            hub.start_inquiry(msg.chat_id, DEMO_OWNER_PHONE, DEMO_OWNER_LANG, DEMO_BUSINESS)
            return []  # start_inquiry already greeted the tourist
        return original_handler(msg) if original_handler else []

    telegram.register_handler(tourist_handler)

    # Terminal input loop (owner side) runs in a background thread so the Telegram
    # long-poll can own the main thread.
    def owner_console():
        print("=" * 64)
        print(" You are the BUSINESS OWNER. When a tourist messages the bot, you'll")
        print(" see their inquiry here. Reply with:  o: <your message>")
        print(f" (You are: {DEMO_BUSINESS}, language={DEMO_OWNER_LANG})")
        print("=" * 64)
        while True:
            try:
                line = input()
            except (EOFError, KeyboardInterrupt):
                return
            if line.strip().startswith("o:"):
                reply = line.split("o:", 1)[1].strip()
                # route to whichever tourist thread is active for this owner phone
                sms.owner_says(DEMO_OWNER_PHONE, reply)

    threading.Thread(target=owner_console, daemon=True).start()
    telegram.start()  # blocks, polling Telegram


if __name__ == "__main__":
    main()
