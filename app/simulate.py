"""CLI SMS simulator — test the whole flow in your terminal, no phone needed.

Usage:
    python -m app.simulate

Type messages as if you were a business owner (in Amharic, Oromo, or English).
Type 'quit' to exit, 'site' to (re)build the website, 'listings' to dump stored data.
"""

from __future__ import annotations

from app.adapters.mock import MockAdapter
from app.adapters.base import InboundMessage, OutboundMessage
from app.conversation.flow import ConversationEngine
from app.site.generator import build_site
from app.store.listings import ListingStore

DEMO_PHONE = "+251911000000"


def main() -> None:
    store = ListingStore()
    engine = ConversationEngine(store)
    adapter = MockAdapter(echo=False)

    def handler(msg: InboundMessage) -> list[OutboundMessage]:
        replies = engine.handle(msg.sender, msg.text)
        return [OutboundMessage(recipient=msg.sender, text=r) for r in replies]

    adapter.register_handler(handler)

    print("=" * 60)
    print(" EthiopiaSMS — CLI simulator")
    print(" You are a business owner texting the service.")
    print(" Commands: 'quit', 'site', 'listings'")
    print("=" * 60)
    print("(Tip: send any first message to begin, e.g. 'hello' / 'ሰላም' / 'nagaa')\n")

    while True:
        try:
            text = input("you ✏️  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text.lower() in {"quit", "exit"}:
            break
        if text.lower() == "site":
            path = build_site(store)
            print(f"  🌐 site built: {path}\n")
            continue
        if text.lower() == "listings":
            for l in store.all():
                flag = " (needs review)" if l.needs_review else ""
                print(f"  • {l.name_en} [{l.category_en}]{flag}")
            print()
            continue

        for reply in adapter.receive(DEMO_PHONE, text):
            print(f"  📱 service > {reply.text}")
        print()


if __name__ == "__main__":
    main()
