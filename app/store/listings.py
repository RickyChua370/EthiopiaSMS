"""Listing storage.

Phase 1 uses a simple JSON-file store (zero setup, easy to inspect and to feed the
static site generator). The interface is small enough to swap for SQLite/Postgres
later without touching callers.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_STORE = Path("data/listings.json")


@dataclass
class Listing:
    phone: str                      # owner phone (contact / "call to book")
    category_en: str
    name_en: str
    source_lang: str                # amh / orm / eng
    price_etb: str | None = None
    lat: float | None = None
    lon: float | None = None
    area: str | None = None         # fallback when no coordinates
    description_en: str = ""
    # original (untranslated) owner-provided text, kept for review/audit
    name_src: str = ""
    description_src: str = ""
    needs_review: bool = False      # low-confidence translation gate
    images_pending: bool = True
    image_paths: list[str] = field(default_factory=list)
    upload_token: str = ""
    published: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if not self.upload_token:
            self.upload_token = secrets.token_urlsafe(8)


class ListingStore:
    def __init__(self, path: Path = DEFAULT_STORE) -> None:
        self.path = Path(path)
        self._items: list[Listing] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._items = [Listing(**r) for r in raw]

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([asdict(i) for i in self._items], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(self, listing: Listing) -> Listing:
        self._items.append(listing)
        self._save()
        return listing

    def all(self) -> list[Listing]:
        return list(self._items)

    def published(self) -> list[Listing]:
        return [i for i in self._items if i.published and not i.needs_review]

    def find_by_token(self, token: str) -> Listing | None:
        return next((i for i in self._items if i.upload_token == token), None)

    def attach_images(self, token: str, paths: list[str]) -> bool:
        listing = self.find_by_token(token)
        if not listing:
            return False
        listing.image_paths.extend(paths)
        listing.images_pending = False
        self._save()
        return True
