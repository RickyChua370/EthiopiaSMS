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


def get_translator() -> Translator:
    """Factory: real NLLB if explicitly enabled, else the mock."""
    if os.environ.get("ETHIOPIASMS_REAL_NLLB") == "1":
        return NllbTranslator()
    return MockTranslator()
