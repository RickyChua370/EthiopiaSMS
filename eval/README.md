# Translation evaluation (FLORES-200)

Quantifies translation quality for the three directions this project depends on:

| Direction | Why it matters |
|-----------|----------------|
| Amharic → English | owner input → public website |
| Afaan Oromo → English | owner input → public website (low-resource) |
| English → Lithuanian | **judges can verify accuracy in their own language** |

## Metrics

- **chrF** — character n-gram F-score (0–100). Robust for morphologically rich
  languages like Amharic/Oromo.
- **BLEU** — token n-gram precision with brevity penalty (0–100).

Both are implemented in pure Python, so the harness runs with **no dependencies**.
If `sacrebleu` is installed, it is used instead for standard, citable scores.

## Quick start (no download, no model)

Smoke-test the harness on a tiny bundled business-domain sample:

```bash
python -m eval.flores_eval --sample
```

> With the default **mock** translator the numbers are placeholders — the point of
> `--sample` is to prove the harness runs. For real scores, use the real model below.

## Real evaluation

1. Install the model deps:
   ```bash
   pip install transformers torch sentencepiece sacrebleu
   ```
2. Download the FLORES-200 `devtest` files (CC BY-SA 4.0) from
   https://github.com/facebookresearch/flores and point the harness at them. The
   files are named by FLORES code, e.g. `amh_Ethi.devtest`, `gaz_Latn.devtest`,
   `eng_Latn.devtest`, `lit_Latn.devtest`.
3. Run with the real NLLB model:
   ```bash
   ETHIOPIASMS_REAL_NLLB=1 python -m eval.flores_eval --n 100 --flores-dir /path/to/flores200
   ```

## Interpreting results

- **Lithuanian (en→lt)** should score high — it's well-resourced. Use this as the
  judge-facing confidence demo.
- **Amharic (am→en)** scores moderately — usable for publishing.
- **Oromo (orm→en)** scores lowest (low-resource). The pipeline deliberately routes
  low-confidence Oromo output through **human review before publishing**, so weak
  machine output never reaches tourists unchecked.

## Attribution

Evaluation data: **FLORES-200**, Meta AI, licensed CC BY-SA 4.0.
Translation model: **NLLB-200**, Meta AI.
