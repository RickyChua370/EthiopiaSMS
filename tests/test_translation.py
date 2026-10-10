"""Tests for the translator factory and backends (no network required)."""

from __future__ import annotations

import os

from app.ai.translation import (
    ISO_CODE,
    MockTranslator,
    MyMemoryTranslator,
    NllbTranslator,
    TranslationResult,
    get_translator,
)


def test_factory_defaults_to_mock(monkeypatch):
    monkeypatch.delenv("ETHIOPIASMS_REAL_NLLB", raising=False)
    monkeypatch.delenv("ETHIOPIASMS_TRANSLATOR", raising=False)
    assert isinstance(get_translator(), MockTranslator)


def test_factory_selects_mymemory(monkeypatch):
    monkeypatch.delenv("ETHIOPIASMS_REAL_NLLB", raising=False)
    monkeypatch.setenv("ETHIOPIASMS_TRANSLATOR", "mymemory")
    assert isinstance(get_translator(), MyMemoryTranslator)


def test_factory_nllb_takes_precedence(monkeypatch):
    monkeypatch.setenv("ETHIOPIASMS_REAL_NLLB", "1")
    monkeypatch.setenv("ETHIOPIASMS_TRANSLATOR", "mymemory")
    assert isinstance(get_translator(), NllbTranslator)


def test_iso_codes_cover_all_languages():
    assert ISO_CODE == {"eng": "en", "amh": "am", "orm": "om", "lit": "lt"}


def test_mymemory_identity_no_network():
    t = MyMemoryTranslator()
    r = t.translate("hello", "eng", "eng")  # same lang -> no API call
    assert r.text == "hello"
    assert r.confidence == 1.0


def test_mymemory_empty_text_no_network():
    t = MyMemoryTranslator()
    r = t.translate("   ", "eng", "lit")  # empty -> no API call
    assert r.confidence == 1.0


def test_mymemory_handles_api_via_monkeypatched_urlopen(monkeypatch):
    """Simulate the MyMemory HTTP response without hitting the network."""
    import io
    import json
    import urllib.request

    payload = json.dumps({
        "responseStatus": 200,
        "responseData": {"translatedText": "Labas pasauli"},
    }).encode("utf-8")

    class FakeResp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: FakeResp(payload))
    r = MyMemoryTranslator().translate("Hello world", "eng", "lit")
    assert r.text == "Labas pasauli"
    assert r.engine == "mymemory"
    assert r.confidence == 0.9


def test_mymemory_network_failure_falls_back(monkeypatch):
    import urllib.request

    def boom(*a, **k):
        raise OSError("no network")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    r = MyMemoryTranslator().translate("Hello", "eng", "lit")
    # falls back to original text, low confidence, never raises
    assert r.text == "Hello"
    assert r.confidence == 0.3
    assert "unavailable" in r.engine
