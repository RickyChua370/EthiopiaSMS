"""Language identification: Amharic (amh) / Afaan Oromo (orm) / English (eng).

Phase 1 uses a lightweight, dependency-free heuristic that is highly reliable for
these three languages:

  * Amharic is written in the Ge'ez (Ethiopic) script — a trivially distinct Unicode
    block, so script detection alone separates it with near-perfect accuracy.
  * Oromo and English both use the Latin script, so we separate them with a small set
    of high-frequency Oromo function words / orthographic cues (e.g. the digraphs
    'dh', 'ph', 'ny' and words like 'fi', 'keessan', 'jedhaa').

In Phase 2 this can be swapped for a trained classifier (e.g. fastText `lid.176`)
behind the same `detect()` signature.
"""

from __future__ import annotations

import re

# Ge'ez / Ethiopic Unicode range (covers Amharic).
_ETHIOPIC = re.compile(r"[\u1200-\u137F]")

# Common Afaan Oromo cues (function words, greetings + characteristic digraphs).
_OROMO_WORDS = {
    "fi", "fkn", "yookaan", "yoo", "jedhaa", "jedha", "keessan", "keessa", "kana",
    "haa", "akka", "daldala", "nagaan", "nagaa", "baga", "maqaan", "gatiin", "iddoo",
    "naannoo", "guddaa", "gaarii", "mana", "buna", "nyaataa", "galatoomaa",
    "aadaa", "harka", "hojii", "hojjetaman", "meeshaalee", "gurgurra", "aartii",
    "harkaan", "dhufaa", "dhuftan", "bilisa", "turistoota", "turistootaaf",
}
# Characteristic Oromo digraphs that are rare in English words.
_OROMO_DIGRAPHS = re.compile(r"(dh|ny|aa|ii|oo|uu|ee)", re.IGNORECASE)

# Lithuanian-specific letters (with diacritics) + common function words. These
# diacritics do not occur in English/Oromo/Amharic-Latin, so they are a strong,
# unambiguous signal.
_LITHUANIAN_CHARS = re.compile(r"[ąčęėįšųūž]", re.IGNORECASE)
_LITHUANIAN_WORDS = {
    "sveiki", "labas", "ačiū", "aciu", "taip", "ne", "turime", "kambarį", "kambari",
    "naktį", "nakti", "naktims", "už", "uz", "kiek", "prašau", "prasau", "iki",
    "pasimatymo", "rytoj", "galite", "registruotis", "mano", "verslas", "kaina",
}


def detect(text: str) -> str:
    """Return 'amh', 'orm', 'lit', or 'eng'."""
    if _ETHIOPIC.search(text):
        return "amh"

    # Lithuanian first (Latin script like Oromo/English): its diacritics or common
    # words are a strong, distinct signal.
    lowered = text.lower()
    if _LITHUANIAN_CHARS.search(text):
        return "lit"
    lit_tokens = re.findall(r"[\w]+", lowered, re.UNICODE)
    if any(tok in _LITHUANIAN_WORDS for tok in lit_tokens):
        return "lit"

    tokens = re.findall(r"[a-zA-Z]+", lowered)
    if not tokens:
        return "eng"

    oromo_hits = sum(1 for tok in tokens if tok in _OROMO_WORDS)
    digraph_hits = len(_OROMO_DIGRAPHS.findall(text))

    # An explicit Oromo word is a strong signal on its own (e.g. a greeting "nagaa").
    # Otherwise fall back to the density of characteristic digraphs (double vowels,
    # dh/ny), which are common in Oromo and rare in English.
    if oromo_hits >= 1:
        return "orm"
    if digraph_hits >= 2 and digraph_hits >= len(tokens):
        return "orm"
    return "eng"


def confidence(text: str) -> float:
    """Rough confidence 0..1 for the detected language (used for review gating)."""
    if _ETHIOPIC.search(text):
        return 0.99
    tokens = re.findall(r"[a-zA-Z]+", text.lower())
    if not tokens:
        return 0.5
    oromo_hits = sum(1 for tok in tokens if tok in _OROMO_WORDS)
    if oromo_hits >= 2:
        return 0.85
    if oromo_hits == 1:
        return 0.65
    return 0.9  # defaulting to English on Latin text is usually safe
