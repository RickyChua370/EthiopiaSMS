"""Real Telegram adapter (tourist side) using Telegram's HTTP Bot API.

Implements the same `TelegramAdapter` interface as the mock, so the bridge works
unchanged. Uses long-polling (getUpdates) over stdlib HTTP — no third-party
dependency. The bot token is read from the TELEGRAM_BOT_TOKEN environment variable
(never hardcoded / committed).

Run via `app.telegram_bridge`, which wires this to the bridge + a mock owner.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.parse
import urllib.request

from .telegram_base import (
    TelegramAdapter,
    TelegramHandler,
    TelegramInbound,
    TelegramOutbound,
)

API = "https://api.telegram.org/bot{token}/{method}"


class LiveTelegramAdapter(TelegramAdapter):
    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not self.token:
            raise RuntimeError("Set TELEGRAM_BOT_TOKEN (from @BotFather) to run the live bot.")
        self._handler: TelegramHandler | None = None
        self._offset = 0
        self._running = False
        self._thread: threading.Thread | None = None

    # --- API plumbing -------------------------------------------------------

    def _call(self, method: str, params: dict) -> dict:
        url = API.format(token=self.token, method=method)
        data = urllib.parse.urlencode(params).encode("utf-8")
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=65) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # --- TelegramAdapter interface -----------------------------------------

    def send(self, message: TelegramOutbound) -> None:
        self._call("sendMessage", {"chat_id": message.chat_id, "text": message.text})

    def register_handler(self, handler: TelegramHandler) -> None:
        self._handler = handler

    # --- long-polling loop --------------------------------------------------

    def start(self) -> None:
        """Begin receiving messages (blocking). Call in the main thread."""
        if self._handler is None:
            raise RuntimeError("register_handler() must be called before start()")
        self._running = True
        print("Telegram bot is live. Message it now; press Ctrl+C to stop.")
        while self._running:
            try:
                resp = self._call("getUpdates", {"offset": self._offset, "timeout": 50})
            except Exception as exc:  # transient network hiccup — back off and retry
                print(f"  (poll error: {exc}; retrying)")
                time.sleep(3)
                continue
            for update in resp.get("result", []):
                self._offset = update["update_id"] + 1
                self._handle_update(update)

    def stop(self) -> None:
        self._running = False

    def _handle_update(self, update: dict) -> None:
        msg = update.get("message") or update.get("edited_message")
        if not msg:
            return
        chat_id = str(msg["chat"]["id"])
        text = msg.get("text", "")
        if not text or self._handler is None:
            return
        for reply in self._handler(TelegramInbound(chat_id=chat_id, text=text)):
            self.send(reply)
