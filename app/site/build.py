"""Build the public site into a Pages-ready output directory.

Renders the public English site to `_site/` by default — the directory GitHub
Pages / Actions deploys. Run manually with:

    python -m app.site.build            # -> _site/index.html

The site is populated with REAL businesses sourced from OpenStreetMap
(© OpenStreetMap contributors, ODbL) — actual names, phones and coordinates across
several Ethiopian cities and categories. Two businesses that have a genuinely free,
openly-licensed photo on Wikimedia Commons display it; every other listing has NO
photo and shows an honest "owner hasn't added photos yet" note (the owner would add
their own via the SMS upload flow).

Only published (reviewed-and-approved) listings are rendered.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

from data.categories import get_category
from data.real_osm_listings import REAL_BUSINESSES
from app.site.generator import render_html
from app.store.listings import Listing, ListingStore

BUSINESS_PHOTO_DIR = Path("site_assets/business_photos")


def _location_label(desc: str) -> str:
    """Derive a human city/location label from the trailing 'in <City>.' of the
    factual description, falling back to 'Ethiopia'."""
    import re
    m = re.search(r"\bin ([A-Z][A-Za-z' ]+?)\.?$", desc.strip())
    return m.group(1).strip() if m else "Ethiopia"


def _add_real_osm_businesses(store: ListingStore) -> None:
    for name, cat_id, phone, lat, lon, desc, photo in REAL_BUSINESSES:
        cat = get_category(cat_id)
        image_paths = []
        if photo and (Path("site_assets") / Path(photo)).exists():
            image_paths = [photo]
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
            area=_location_label(desc),
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

    output_dir.mkdir(parents=True, exist_ok=True)
    index = output_dir / "index.html"
    index.write_text(render_html(store.published()), encoding="utf-8")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    # Real business photos (the two openly-licensed ones), served as
    # `business_photos/<file>` next to index.html.
    if BUSINESS_PHOTO_DIR.exists():
        shutil.copytree(BUSINESS_PHOTO_DIR, output_dir / "business_photos", dirs_exist_ok=True)

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
