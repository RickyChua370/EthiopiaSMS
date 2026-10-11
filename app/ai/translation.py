"""Translation component — mockable interface over NLLB-200.

Design goal (Small AI): a SINGLE model (NLLB-200) covers every direction we need:
    amh_Ethi -> eng_Latn      (owner Amharic -> website English)
    gaz_Latn -> eng_Latn      (owner Oromo   -> website English)
    eng_Latn -> lit_Latn      (English -> Lithuanian, for judge accuracy testing)

Phase 1 defaults to MockTranslator so the whole pipeline runs instantly with no
model download. Set ETHIOPIASMS_REAL_NLLB=1 (and install transformers) to use the
real model via NllbTranslator — same interface, no core changes.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

# FLORES-200 language codes used by NLLB-200.
NLLB_CODE = {
    "eng": "eng_Latn",
    "amh": "amh_Ethi",
    "orm": "gaz_Latn",   # West Central Oromo
    "lit": "lit_Latn",
}

# ISO-639-1 codes used by the MyMemory web API.
ISO_CODE = {
    "eng": "en",
    "amh": "am",
    "orm": "om",
    "lit": "lt",
}


@dataclass
class TranslationResult:
    text: str
    confidence: float      # 0..1 — low values get flagged for human review
    source_lang: str
    target_lang: str
    engine: str


class Translator(ABC):
    @abstractmethod
    def translate(self, text: str, source: str, target: str) -> TranslationResult:
        ...


# Low-resource languages where output should be treated as less reliable and
# routed through human review before publishing.
_LOW_RESOURCE = {"orm"}


class MockTranslator(Translator):
    """Deterministic placeholder translator for local dev / tests / demos.

    It does not actually translate; it tags the text so the pipeline is fully
    exercisable and the confidence-gating logic (esp. for Oromo) can be tested.
    """

    def translate(self, text: str, source: str, target: str) -> TranslationResult:
        if source == target:
            return TranslationResult(text, 1.0, source, target, "mock(identity)")
        rendered = f"[{source}->{target}] {text}"
        conf = 0.55 if source in _LOW_RESOURCE else 0.9
        return TranslationResult(rendered, conf, source, target, "mock")


class NllbTranslator(Translator):
    """Real NLLB-200 translator (lazy-loaded). Requires `transformers` + `torch`.

    Enabled when ETHIOPIASMS_REAL_NLLB=1. Kept import-light so the mock path has
    zero heavy dependencies.
    """

    def __init__(self, model_name: str = "facebook/nllb-200-distilled-600M") -> None:
        self.model_name = model_name
        self._tokenizer = None
        self._model = None

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        from transformers import (  # type: ignore
            AutoModelForSeq2SeqLM,
            AutoTokenizer,
        )
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)

    def translate(self, text: str, source: str, target: str) -> TranslationResult:
        if source == target:
            return TranslationResult(text, 1.0, source, target, "identity")
        self._ensure_loaded()
        assert self._tokenizer is not None and self._model is not None
        self._tokenizer.src_lang = NLLB_CODE[source]
        encoded = self._tokenizer(text, return_tensors="pt")
        bos = self._tokenizer.convert_tokens_to_ids(NLLB_CODE[target])
        generated = self._model.generate(**encoded, forced_bos_token_id=bos, max_length=256)
        out = self._tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
        conf = 0.6 if source in _LOW_RESOURCE else 0.9
        return TranslationResult(out, conf, source, target, self.model_name)


class MyMemoryTranslator(Translator):
    """Lightweight real translation via the free MyMemory web API.

    No model download and no API key (anonymous tier), so it fits comfortably on a
    small free host (e.g. Render) — unlike the 2.4 GB NLLB model. Covers all four
    languages we need (am / om / lt / en). Falls back gracefully to the original
    text if the service is unreachable, so the demo never hard-fails.

    Enabled with ETHIOPIASMS_TRANSLATOR=mymemory.
    """

    ENDPOINT = "https://api.mymemory.translated.net/get"

    def __init__(self, email: str | None = None) -> None:
        # Providing an email (optional) raises MyMemory's free daily quota.
        self.email = email or os.environ.get("MYMEMORY_EMAIL")

    # Secondary provider used only if MyMemory fails, so one service hiccup doesn't
    # break the demo. LibreTranslate public instance, no key needed.
    LIBRE_ENDPOINT = "https://libretranslate.com/translate"

    def translate(self, text: str, source: str, target: str) -> TranslationResult:
        if source == target or not text.strip():
            return TranslationResult(text, 1.0, source, target, "identity")

        conf = 0.6 if source in _LOW_RESOURCE else 0.9

        # 1) MyMemory with up to 2 retries (handles transient timeouts/rate-limits).
        out = self._mymemory(text, source, target, attempts=2)
        if out is not None:
            return TranslationResult(out, conf, source, target, "mymemory")

        # 2) Fallback to LibreTranslate so a single-provider hiccup doesn't fail.
        out = self._libre(text, source, target)
        if out is not None:
            return TranslationResult(out, conf, source, target, "libretranslate")

        # 3) Both unavailable — honest fallback (never hard-fail the demo).
        return TranslationResult(text, 0.3, source, target, "unavailable")

    # -- providers -----------------------------------------------------------

    def _mymemory(self, text: str, source: str, target: str, attempts: int = 2):
        import html
        import json as _json
        import sys
        import time
        import urllib.parse
        import urllib.request

        params = {
            "q": text,
            "langpair": f"{ISO_CODE[source]}|{ISO_CODE[target]}",
            "de": self.email or "ethiopiasms.demo@example.com",
        }
        url = f"{self.ENDPOINT}?{urllib.parse.urlencode(params)}"
        for attempt in range(1, attempts + 1):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "EthiopiaSMS/1.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = _json.loads(resp.read().decode("utf-8"))
                rd = data.get("responseData", {}) or {}
                out = html.unescape(rd.get("translatedText") or "")
                status = str(data.get("responseStatus"))
                looks_like_error = out.isupper() and len(out.split()) > 3
                if status == "200" and out and not looks_like_error:
                    return out
                reason = (data.get("responseDetails") or out or f"status {status}")
                print(f"  [translate] MyMemory issue ({source}->{target}, try {attempt}): "
                      f"{reason[:120]}", file=sys.stderr)
            except Exception as exc:
                print(f"  [translate] MyMemory call failed ({source}->{target}, try "
                      f"{attempt}): {exc}", file=sys.stderr)
            if attempt < attempts:
                time.sleep(1.0 * attempt)  # simple backoff
        return None

    def _libre(self, text: str, source: str, target: str):
        import json as _json
        import sys
        import urllib.request

        try:
            payload = _json.dumps({
                "q": text, "source": ISO_CODE[source], "target": ISO_CODE[target],
                "format": "text",
            }).encode("utf-8")
            req = urllib.request.Request(
                self.LIBRE_ENDPOINT, data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "EthiopiaSMS/1.0"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = _json.loads(resp.read().decode("utf-8"))
            out = data.get("translatedText")
            if out:
                return out
            print(f"  [translate] LibreTranslate empty ({source}->{target})", file=sys.stderr)
        except Exception as exc:
            print(f"  [translate] LibreTranslate failed ({source}->{target}): {exc}",
                  file=sys.stderr)
        return None


def get_translator() -> Translator:
    """Factory, selected by environment:
        ETHIOPIASMS_REAL_NLLB=1          -> local NLLB-200 model (best quality, heavy)
        ETHIOPIASMS_TRANSLATOR=mymemory  -> free MyMemory web API (light, host-friendly)
        (default)                        -> mock (instant, offline, placeholder output)
    """
    if os.environ.get("ETHIOPIASMS_REAL_NLLB") == "1":
        return NllbTranslator()
    if os.environ.get("ETHIOPIASMS_TRANSLATOR", "").lower() == "mymemory":
        return MyMemoryTranslator()
    return MockTranslator()
