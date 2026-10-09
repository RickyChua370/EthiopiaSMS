"""Build the public site into a Pages-ready output directory.

Generates demo listings (in all three languages) and renders the static English
site to `_site/` by default — the conventional directory GitHub Pages / Actions
deploys. Run manually with:

    python -m app.site.build            # -> _site/index.html

Only published (reviewed-and-approved) listings are rendered, so low-confidence
Oromo translations awaiting review never appear.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

from app.adapters.base import OutboundMessage
from app.adapters.mock import MockAdapter
from app.conversation.flow import ConversationEngine
from app.site.generator import render_html
from app.store.listings import ListingStore

# Demo onboarding conversations (owner-side messages), one per business.
DEMO_FLOWS = [
    ("+251911000001", ["hello", "2", "Tomoca Coffee", "150 birr", "9.0105, 38.7612",
                       "Historic coffee house in the heart of Addis Ababa, roasting since 1953."]),
    ("+251911000002", ["hello", "3", "Blue Nile Guesthouse", "800 birr", "9.0300, 38.7600",
                       "Family-run guesthouse with a quiet garden, near the national museum."]),
    ("+251911000004", ["hello", "1", "Yod Abyssinia", "250 birr", "9.0120, 38.7650",
                       "Traditional Ethiopian cuisine with live cultural music and dance."]),
    ("+251911000006", ["hello", "4", "Shiro Meda Handicrafts", "skip", "9.0450, 38.7550",
                       "Handwoven textiles and traditional crafts from local artisans."]),
]


def build(output_dir: Path) -> Path:
    # Use a throwaway store so the build is reproducible and side-effect free.
    tmp = Path(tempfile.mkdtemp()) / "listings.json"
    store = ListingStore(tmp)
    engine = ConversationEngine(store)
    adapter = MockAdapter()
    adapter.register_handler(
        lambda m: [OutboundMessage(m.sender, r) for r in engine.handle(m.sender, m.text)]
    )
    for phone, msgs in DEMO_FLOWS:
        for msg in msgs:
            adapter.receive(phone, msg)

    output_dir.mkdir(parents=True, exist_ok=True)
    index = output_dir / "index.html"
    index.write_text(render_html(store.published()), encoding="utf-8")
    # Prevent Jekyll from processing the output on GitHub Pages.
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    # Copy owner-uploaded images (if any) so the static site can display them.
    # Listings reference images by the relative path `uploads/<token>/<file>`,
    # so the `uploads/` tree must sit next to index.html in the output.
    uploads_src = Path("uploads")
    if uploads_src.exists():
        shutil.copytree(uploads_src, output_dir / "uploads", dirs_exist_ok=True)

    return index


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("_site")
    index = build(out)
    print(f"Built site: {index} ({index.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
