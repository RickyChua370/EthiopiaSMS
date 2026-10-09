"""Build the public site into a Pages-ready output directory.

Renders the public English site to `_site/` by default — the directory GitHub
Pages / Actions deploys. Run manually with:

    python -m app.site.build            # -> _site/index.html

The site combines two sources of listings:
  1. A few illustrative demo onboarding flows (one per language), to show the
     SMS → listing pipeline.
  2. REAL Addis Ababa businesses sourced from OpenStreetMap (© OpenStreetMap
     contributors, ODbL) — actual names, phones and coordinates. These carry a
     generic, openly-licensed CATEGORY image (not a photo of the specific place);
     in production the photo slot stays a placeholder until the owner uploads one.

Only published (reviewed-and-approved) listings are rendered, so low-confidence
Oromo translations awaiting review never appear.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

from data.categories import get_category
from data.real_osm_listings import REAL_BUSINESSES
from app.adapters.base import OutboundMessage
from app.adapters.mock import MockAdapter
from app.conversation.flow import ConversationEngine
from app.site.generator import render_html
from app.store.listings import Listing, ListingStore

CATEGORY_IMAGE_DIR = Path("site_assets/category_images")

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


def _add_demo_flows(store: ListingStore) -> None:
    engine = ConversationEngine(store)
    adapter = MockAdapter()
    adapter.register_handler(
        lambda m: [OutboundMessage(m.sender, r) for r in engine.handle(m.sender, m.text)]
    )
    for phone, msgs in DEMO_FLOWS:
        for msg in msgs:
            adapter.receive(phone, msg)


def _add_real_osm_businesses(store: ListingStore) -> None:
    """Add real OSM-sourced businesses straight to the store (they come from OSM
    data, not an SMS conversation), each with a generic category image."""
    for name, cat_id, phone, lat, lon, desc, img_key in REAL_BUSINESSES:
        cat = get_category(cat_id)
        image_paths = []
        if img_key and (CATEGORY_IMAGE_DIR / f"{img_key}.jpg").exists():
            image_paths = [f"category_images/{img_key}.jpg"]
        store.add(Listing(
            phone=phone,
            category_en=cat.en if cat else "Other",
            name_en=name,
            name_src=name,
            description_en=desc,
            description_src=desc,
            source_lang="eng",
            lat=lat,
            lon=lon,
            image_paths=image_paths,
            images_pending=not image_paths,
            published=True,
            needs_review=False,
        ))


def build(output_dir: Path) -> Path:
    # Throwaway store so the build is reproducible and side-effect free.
    tmp = Path(tempfile.mkdtemp()) / "listings.json"
    store = ListingStore(tmp)
    _add_real_osm_businesses(store)
    _add_demo_flows(store)

    output_dir.mkdir(parents=True, exist_ok=True)
    index = output_dir / "index.html"
    index.write_text(render_html(store.published()), encoding="utf-8")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    # Generic category images (openly licensed) used by the real OSM listings.
    if CATEGORY_IMAGE_DIR.exists():
        shutil.copytree(CATEGORY_IMAGE_DIR, output_dir / "category_images", dirs_exist_ok=True)

    # Owner-uploaded images (if any) referenced as `uploads/<token>/<file>`.
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
