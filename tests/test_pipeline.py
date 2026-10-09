"""Automated tests (Level 2) — scripted conversations + metric sanity checks.

Run with:  pytest    (or:  python -m pytest)
These use only the standard library + the mock pipeline, so they need no model
download and no SMS account.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.adapters.base import OutboundMessage
from app.adapters.mock import MockAdapter
from app.ai import language_id
from app.ai.extraction import parse_coordinates, parse_price
from app.conversation.flow import ConversationEngine
from app.store.listings import ListingStore
from eval.flores_eval import bleu, chrf


# ------------------------------------------------------------------ language ID

def test_language_id_amharic():
    assert language_id.detect("ሰላም ቡና ቤት") == "amh"


def test_language_id_oromo_greeting():
    assert language_id.detect("nagaa") == "orm"


def test_language_id_oromo_phrase():
    assert language_id.detect("Meeshaalee aadaa harkaan hojjetaman gurgurra.") == "orm"


def test_language_id_english_not_oromo():
    assert language_id.detect("Historic coffee house in the heart of Addis") == "eng"


# ------------------------------------------------------------------ extraction

def test_parse_coordinates_valid_ethiopia():
    c = parse_coordinates("9.0105, 38.7612")
    assert c and round(c.lat, 4) == 9.0105 and round(c.lon, 4) == 38.7612


def test_parse_coordinates_out_of_range():
    assert parse_coordinates("51.5, -0.12") is None  # London — outside Ethiopia


def test_parse_price():
    assert parse_price("150 birr") == "150 ETB"
    assert parse_price("skip") is None


# ------------------------------------------------------------------ metrics

def test_chrf_perfect_match_is_100():
    assert chrf("hello world", "hello world") > 99.0


def test_chrf_total_mismatch_is_low():
    assert chrf("abc", "xyz") < 20.0


def test_bleu_perfect_match_high():
    assert bleu("a quiet family guesthouse", "a quiet family guesthouse") > 80.0


# ------------------------------------------------------------------ conversation

def _engine():
    tmp = Path(tempfile.mkdtemp()) / "listings.json"
    store = ListingStore(tmp)
    engine = ConversationEngine(store)
    adapter = MockAdapter()
    adapter.register_handler(
        lambda m: [OutboundMessage(m.sender, r) for r in engine.handle(m.sender, m.text)]
    )
    return engine, store, adapter


def test_english_flow_publishes():
    _, store, adapter = _engine()
    for msg in ["hello", "2", "Tomoca Coffee", "150 birr", "9.0105, 38.7612",
                "Historic coffee house in Addis."]:
        adapter.receive("+251911000001", msg)
    listings = store.all()
    assert len(listings) == 1
    l = listings[0]
    assert l.category_en == "Café / Coffee"
    assert l.price_etb == "150 ETB"
    assert l.lat and l.lon
    assert l.published and not l.needs_review


def test_oromo_flow_is_gated_for_review():
    _, store, adapter = _engine()
    for msg in ["nagaa", "4", "Harka Hojii Aadaa", "skip", "7.0500, 38.4700",
                "Meeshaalee aadaa harkaan hojjetaman gurgurra."]:
        adapter.receive("+251911000003", msg)
    l = store.all()[0]
    assert l.source_lang == "orm"
    assert l.needs_review is True
    assert l.published is False
    assert l not in store.published()


def test_location_fallback_to_area():
    _, store, adapter = _engine()
    for msg in ["hello", "1", "Yod Abyssinia", "250 birr", "area",
                "Bole, Addis Ababa", "Traditional cuisine with live music."]:
        adapter.receive("+251911000004", msg)
    l = store.all()[0]
    assert l.area == "Bole, Addis Ababa"
    assert l.lat is None


def test_images_pending_on_publish():
    _, store, adapter = _engine()
    for msg in ["hello", "2", "Cafe X", "100 birr", "9.0, 38.7", "Nice place."]:
        adapter.receive("+251911000005", msg)
    l = store.all()[0]
    assert l.images_pending is True
    assert l.upload_token  # a link token was issued
