"""Interactive demo of the two-way Telegram ↔ SMS booking bridge.

Run:
    python -m app.bridge_demo

Simulates a tourist (Telegram) and a business owner (SMS) talking to each other
through the bridge, with live translation in both directions. No bot token, no
telecom account — uses the mock adapters.

Commands:
    t: <message>     send a message AS THE TOURIST (English, via Telegram)
    o: <message>     send a message AS THE OWNER (their language, via SMS)
    switch           change which business/owner-language you're inquiring to
    quit
"""

from __future__ import annotations

from app.adapters.mock import MockAdapter
from app.adapters.telegram_mock import MockTelegramAdapter
from app.bridge.hub import BridgeHub

TOURIST_CHAT = "demo-tourist"

# A couple of businesses the tourist can "tap into" (as if from the website).
BUSINESSES = [
    ("Tomoca Coffee", "+251911223344", "amh"),
    ("Harka Hojii Aadaa (crafts)", "+251922556677", "orm"),
    ("Sheraton Addis", "+251115171717", "eng"),
]


def main() -> None:
    sms = MockAdapter()
    tg = MockTelegramAdapter()
    hub = BridgeHub(sms, tg)

    # Capture outbound so we can print what each side receives.
    tg_seen = 0
    sms_seen = 0

    name, phone, lang = BUSINESSES[0]
    thread = hub.start_inquiry(TOURIST_CHAT, phone, lang, name)

    print("=" * 64)
    print(" Telegram ↔ SMS booking bridge — interactive demo")
    print(f" Tourist is inquiring to: {name} (owner language: {lang})")
    print(" Commands:  t: <msg>  (as tourist)   o: <msg>  (as owner)")
    print("            switch     quit")
    print("=" * 64)

    def flush():
        nonlocal tg_seen, sms_seen
        for m in tg.outbox[tg_seen:]:
            print(f"  📱 TOURIST (Telegram) sees: {m.text}")
        tg_seen = len(tg.outbox)
        for m in sms.outbox[sms_seen:]:
            print(f"  ✉️  OWNER (SMS) gets      : {m.text}")
        sms_seen = len(sms.outbox)

    flush()
    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.lower() in {"quit", "exit"}:
            break
        if line.lower() == "switch":
            for i, (n, p, l) in enumerate(BUSINESSES):
                print(f"  {i+1}. {n} ({l})")
            sel = input("  choose business #: ").strip()
            try:
                name, phone, lang = BUSINESSES[int(sel) - 1]
                thread = hub.start_inquiry(TOURIST_CHAT, phone, lang, name)
                print(f"  → now inquiring to {name} ({lang})")
                flush()
            except (ValueError, IndexError):
                print("  invalid choice")
            continue
        if line.startswith("t:"):
            tg.receive(TOURIST_CHAT, line[2:].strip())
            flush()
        elif line.startswith("o:"):
            # owner replies by SMS, quoting the active thread's ref
            sms.receive(phone, f"[{thread.ref}] {line[2:].strip()}")
            flush()
        else:
            print("  prefix with 't:' (tourist) or 'o:' (owner), or 'switch' / 'quit'")


if __name__ == "__main__":
    main()
