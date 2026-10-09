"""Tests for the deferred image-upload flow (multipart parsing + attach)."""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from app.adapters.base import OutboundMessage
from app.adapters.mock import MockAdapter
from app.conversation.flow import ConversationEngine
from app.store.listings import ListingStore
from app.uploads import _detect_ext, _parse_multipart

# A minimal valid 1x1 PNG.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def test_detect_ext_png():
    assert _detect_ext(PNG) == "png"


def test_detect_ext_jpeg():
    assert _detect_ext(b"\xff\xd8\xff\xe0rest") == "jpg"


def test_detect_ext_rejects_non_image():
    assert _detect_ext(b"not an image") is None


def test_multipart_parse_extracts_file():
    boundary = b"X-BOUNDARY"
    body = (
        b"--X-BOUNDARY\r\n"
        b'Content-Disposition: form-data; name="photos"; filename="a.png"\r\n'
        b"Content-Type: image/png\r\n\r\n" + PNG + b"\r\n"
        b"--X-BOUNDARY--\r\n"
    )
    files = _parse_multipart(body, boundary)
    assert len(files) == 1
    assert files[0][0] == "a.png"
    assert files[0][1] == PNG


def test_multipart_skips_non_file_fields():
    boundary = b"B"
    body = (
        b"--B\r\n"
        b'Content-Disposition: form-data; name="note"\r\n\r\n'
        b"hello\r\n"
        b"--B--\r\n"
    )
    assert _parse_multipart(body, boundary) == []


def test_attach_images_updates_listing():
    tmp = Path(tempfile.mkdtemp()) / "listings.json"
    store = ListingStore(tmp)
    engine = ConversationEngine(store)
    adapter = MockAdapter()
    adapter.register_handler(
        lambda m: [OutboundMessage(m.sender, r) for r in engine.handle(m.sender, m.text)]
    )
    for msg in ["hello", "2", "Cafe X", "100 birr", "9.0, 38.7", "Nice place."]:
        adapter.receive("+251911000009", msg)
    listing = store.all()[0]
    assert listing.images_pending is True

    ok = store.attach_images(listing.upload_token, ["uploads/tok/x.png"])
    assert ok
    refreshed = store.all()[0]
    assert refreshed.image_paths == ["uploads/tok/x.png"]
    assert refreshed.images_pending is False


def test_attach_images_unknown_token():
    tmp = Path(tempfile.mkdtemp()) / "listings.json"
    store = ListingStore(tmp)
    assert store.attach_images("nonexistent", ["uploads/x/y.png"]) is False
