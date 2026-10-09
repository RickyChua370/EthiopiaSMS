# EthiopiaSMS — Small AI SMS Platform for Tourism MSMEs

Bringing offline Ethiopian micro, small & medium enterprises (MSMEs) online through
**SMS** — the channel they already use — powered by a lightweight ("Small AI") pipeline.

A business owner texts basic details in **Amharic, Afaan Oromo, or English**. The system
detects the language, extracts the fields, translates them to English, and publishes a
clean listing to a **public English website** that international tourists can browse — with
a direct "call to book" channel back to the owner.

> **Why SMS?** In Ethiopia ~78% of adults own a mobile phone but only ~26% use mobile
> internet daily, and the government already reaches citizens via SMS. SMS meets owners
> where they are — no app, no data plan, works on a basic phone.

---

## The user journey

```
Owner texts (am / orm / en)        Small AI pipeline                 Public website (English)
──────────────────────────   ───────────────────────────────   ──────────────────────────────
"ቡና ቤት፣ ዋጋ 150 ብር፣ ቦሌ"      1. Language ID                     ┌────────────────────────┐
                             2. Field extraction                │ Bole Coffee House      │
                             3. Translate → English             │ Café · ~150 ETB · Bole │
                             4. Confidence check                │ 📞 Call to book        │
                                                                └────────────────────────┘
```

Images are **not** required to publish: a listing goes live from SMS text immediately and
is marked `images_pending`. The owner receives an upload link they can open **whenever they
next have internet** to attach photos, which then appear on the already-live listing.

---

## Architecture (gateway-agnostic)

```
SMS ─▶ Gateway Adapter (interface)
       ├─ MockAdapter        (local/dev — no account needed)
       ├─ AfricasTalkingAdapter
       └─ TwilioAdapter
          │
          ▼
     Conversation state machine (per phone number)
          │
          ▼
     Small AI pipeline
       1. Language ID        (amh / orm / eng)
       2. Field extraction   (rules + slots)
       3. Translation        (NLLB-200: am/orm → en ; en → lt for judges)
       4. Confidence gate     (flag low-confidence — esp. Oromo — for review)
          │
          ▼
     Listing store (SQLite/JSON) + deferred image uploads
          │
          ▼
     Static site generator → English listings → GitHub Pages
```

Everything behind the **gateway adapter interface** runs fully with the `MockAdapter`, so
the whole flow works locally with no telecom account.

---

## Languages

| Language | Code | Role | Notes |
|----------|------|------|-------|
| English | `eng` | pipeline + website output | high quality |
| Amharic | `amh` | owner input | good support |
| Afaan Oromo | `orm` | owner input | low-resource — low-confidence flagged for review |
| Lithuanian | `lit` | **judge testing** | high quality; English→Lithuanian for accuracy demos |

---

## How to test (no phone / no SMS account needed)

| Level | What | Command |
|-------|------|---------|
| 1 | **CLI simulator** — chat like an owner in your terminal | `python -m app.simulate` |
| 1 | **Web simulator** — on-screen phone + live website, best for demos | `python -m app.web` → http://localhost:8000 |
| 2 | **Automated tests** — scripted conversations + metric checks | `pytest` |
| 2 | **Translation accuracy** — FLORES-200 chrF/BLEU (incl. en→Lithuanian) | `python -m eval.flores_eval --sample` |
| 3 | **Webhook test** — POST sample gateway payloads to a local server | see `docs/testing.md` |
| 4 | **Real SMS** — Africa's Talking / Twilio + ngrok tunnel | see `docs/testing.md` |

See [`docs/testing.md`](docs/testing.md) for the full guide.

---

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.simulate          # start chatting as a business owner
```

---

## Project layout

```
app/
  adapters/        SMS gateway adapters (mock, africastalking, twilio)
  ai/              Small AI pipeline (language id, extraction, translation)
  conversation/    onboarding state machine + multilingual prompts
  store/           listing storage + deferred image uploads
  site/            static website generator
  simulate.py      CLI SMS simulator
  web.py           web-based SMS simulator (on-screen phone + live site)
data/              category taxonomy, prompt strings
eval/              FLORES-200 translation evaluation harness (chrF/BLEU)
docs/              testing & deployment guides
tests/             automated tests (pytest)
```

---

## Status

🚧 **Phase 1 scaffold** — end-to-end flow against the Mock adapter, with mockable NLLB
translation. Phase 2 will fold in fetched Amharic/Oromo parallel data and fine-tuning.

## License / data attribution

- Business/place discovery seeded from **OpenStreetMap** © OpenStreetMap contributors (ODbL).
- Translation via **NLLB-200** (Meta). Evaluation uses **FLORES-200** (CC BY-SA 4.0).
- Field-extraction warm-start references **MASSIVE** (Amazon, CC BY 4.0).
