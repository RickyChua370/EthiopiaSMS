"""FLORES-200 translation evaluation harness.

Measures translation quality on the FLORES-200 benchmark (CC BY-SA 4.0) for the
directions this project cares about:

    amh_Ethi -> eng_Latn    (Amharic owner input -> English website)
    gaz_Latn -> eng_Latn    (Afaan Oromo owner input -> English website)
    eng_Latn -> lit_Latn    (English -> Lithuanian, for judge verification)

Metrics: chrF (character n-gram F-score) and a token-level BLEU-ish score. Both are
implemented here in pure Python so the harness runs with NO third-party packages;
if `sacrebleu` is installed it is used instead for standard, citable scores.

Usage:
    # Quick smoke test on the tiny bundled sample (no download, no model):
    python -m eval.flores_eval --sample

    # Real evaluation with the actual NLLB model + a FLORES subset:
    ETHIOPIASMS_REAL_NLLB=1 python -m eval.flores_eval --n 50 --flores-dir path/to/flores200

The harness is model-agnostic: it calls the same Translator interface the live
pipeline uses, so the numbers reflect exactly what owners/judges would get.
"""

from __future__ import annotations

import argparse
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from app.ai.translation import get_translator

# Directions we report on: (name, source_lang, target_lang)
DIRECTIONS = [
    ("Amharic → English", "amh", "eng"),
    ("Oromo → English", "orm", "eng"),
    ("English → Lithuanian", "eng", "lit"),
]


# --------------------------------------------------------------------------- metrics

def _char_ngrams(text: str, n: int) -> Counter:
    text = text.replace(" ", "")
    return Counter(text[i:i + n] for i in range(len(text) - n + 1)) if len(text) >= n else Counter()


def chrf(hypothesis: str, reference: str, max_n: int = 6, beta: float = 2.0) -> float:
    """Character n-gram F-score (chrF), 0..100. Pure-Python implementation."""
    if not hypothesis or not reference:
        return 0.0
    precisions, recalls = [], []
    for n in range(1, max_n + 1):
        h, r = _char_ngrams(hypothesis, n), _char_ngrams(reference, n)
        overlap = sum((h & r).values())
        if sum(h.values()):
            precisions.append(overlap / sum(h.values()))
        if sum(r.values()):
            recalls.append(overlap / sum(r.values()))
    if not precisions or not recalls:
        return 0.0
    p = sum(precisions) / len(precisions)
    r = sum(recalls) / len(recalls)
    if p + r == 0:
        return 0.0
    beta2 = beta * beta
    return 100.0 * (1 + beta2) * p * r / (beta2 * p + r)


def bleu(hypothesis: str, reference: str, max_n: int = 4) -> float:
    """A simple corpus-free sentence BLEU (0..100) with brevity penalty."""
    hyp = hypothesis.split()
    ref = reference.split()
    if not hyp or not ref:
        return 0.0
    log_sum, used = 0.0, 0
    for n in range(1, max_n + 1):
        h = Counter(tuple(hyp[i:i + n]) for i in range(len(hyp) - n + 1))
        r = Counter(tuple(ref[i:i + n]) for i in range(len(ref) - n + 1))
        overlap = sum((h & r).values())
        total = max(sum(h.values()), 1)
        if total and sum(h.values()):
            p = overlap / total
            log_sum += math.log(p) if p > 0 else math.log(1e-9)
            used += 1
    if not used:
        return 0.0
    geo = math.exp(log_sum / used)
    bp = 1.0 if len(hyp) > len(ref) else math.exp(1 - len(ref) / max(len(hyp), 1))
    return 100.0 * bp * geo


def _try_sacrebleu():
    try:
        import sacrebleu  # type: ignore
        return sacrebleu
    except Exception:
        return None


# --------------------------------------------------------------------------- data

@dataclass
class EvalPair:
    source: str
    reference: str


# Tiny bundled sample (business-domain sentences) so the harness is runnable with
# no download. These are illustrative references, not official FLORES sentences.
SAMPLE: dict[tuple[str, str], list[EvalPair]] = {
    ("amh", "eng"): [
        EvalPair("ባህላዊ የኢትዮጵያ ምግብ የሚቀርብበት ቤት።", "A house serving traditional Ethiopian food."),
        EvalPair("ጥንታዊ የቡና ቤት በአዲስ አበባ መሃል።", "A historic coffee house in the center of Addis Ababa."),
    ],
    ("orm", "eng"): [
        EvalPair("Meeshaalee aadaa harkaan hojjetaman gurgurra.", "We sell handmade cultural items."),
        EvalPair("Mana buna aadaa naannoo kanaa.", "A traditional coffee house in this area."),
    ],
    ("eng", "lit"): [
        EvalPair("A historic coffee house in the heart of Addis Ababa.",
                 "Istorinė kavinė Adis Abebos širdyje."),
        EvalPair("Family-run guesthouse with a quiet garden.",
                 "Šeimos svečių namai su ramiu sodu."),
    ],
}


def load_flores_subset(flores_dir: Path, src: str, tgt: str, n: int) -> list[EvalPair]:
    """Load n parallel lines from a local FLORES-200 devtest directory.

    Expects files named like `<flores_code>.devtest` (e.g. amh_Ethi.devtest).
    """
    from app.ai.translation import NLLB_CODE
    sdir = flores_dir / f"{NLLB_CODE[src]}.devtest"
    tdir = flores_dir / f"{NLLB_CODE[tgt]}.devtest"
    srcs = sdir.read_text(encoding="utf-8").splitlines()
    tgts = tdir.read_text(encoding="utf-8").splitlines()
    return [EvalPair(s, t) for s, t in list(zip(srcs, tgts))[:n]]


# --------------------------------------------------------------------------- runner

def evaluate(pairs: list[EvalPair], src: str, tgt: str) -> dict:
    translator = get_translator()
    sb = _try_sacrebleu()
    hyps, refs, chrfs = [], [], []
    for pair in pairs:
        out = translator.translate(pair.source, src, tgt).text
        hyps.append(out)
        refs.append(pair.reference)
        chrfs.append(chrf(out, pair.reference))

    if sb:
        chrf_score = sb.corpus_chrf(hyps, [refs]).score
        bleu_score = sb.corpus_bleu(hyps, [refs]).score
        metric_src = "sacrebleu"
    else:
        chrf_score = sum(chrfs) / len(chrfs) if chrfs else 0.0
        bleu_score = sum(bleu(h, r) for h, r in zip(hyps, refs)) / max(len(hyps), 1)
        metric_src = "builtin"
    return {"chrf": chrf_score, "bleu": bleu_score, "n": len(pairs), "metric": metric_src}


def main() -> None:
    ap = argparse.ArgumentParser(description="FLORES-200 translation evaluation")
    ap.add_argument("--sample", action="store_true", help="use the tiny bundled sample")
    ap.add_argument("--n", type=int, default=50, help="sentences per direction (FLORES mode)")
    ap.add_argument("--flores-dir", type=Path, help="path to FLORES-200 devtest files")
    args = ap.parse_args()

    print("=" * 64)
    print(" FLORES-200 translation evaluation")
    translator = get_translator()
    print(f" translator: {type(translator).__name__}")
    if type(translator).__name__ == "MockTranslator":
        print(" ⚠️  MOCK translator — numbers are placeholders. Set ETHIOPIASMS_REAL_NLLB=1")
        print("     (and install transformers/torch) for real scores.")
    print("=" * 64)

    rows = []
    for name, src, tgt in DIRECTIONS:
        if args.flores_dir and not args.sample:
            pairs = load_flores_subset(args.flores_dir, src, tgt, args.n)
        else:
            pairs = SAMPLE[(src, tgt)]
        res = evaluate(pairs, src, tgt)
        rows.append((name, res))

    print(f"\n{'Direction':<24}{'chrF':>8}{'BLEU':>8}{'n':>5}  metric")
    print("-" * 56)
    for name, res in rows:
        print(f"{name:<24}{res['chrf']:>8.1f}{res['bleu']:>8.1f}{res['n']:>5}  {res['metric']}")
    print("\nchrF/BLEU are 0–100 (higher is better). Oromo is low-resource; expect lower")
    print("scores there — those listings are routed through human review before publishing.")


if __name__ == "__main__":
    main()
