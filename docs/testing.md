# Testing the SMS platform (without a phone or SMS account)

Because the system is **gateway-agnostic**, you can test almost everything locally
with the Mock adapter. Here are the four levels, from easiest to most realistic.

---

## Level 1 — Local simulators (free, instant, no account)

### CLI simulator
Chat as a business owner directly in your terminal:

```bash
python -m app.simulate
```

Try a full flow in each language (type one message per line):

| English | Amharic | Oromo |
|---------|---------|-------|
| `hello` | `ሰላም` | `nagaa` |
| `2` | `1` | `4` |
| `Tomoca Coffee` | `የሀበሻ ምግብ ቤት` | `Harka Hojii Aadaa` |
| `150 birr` | `200 ብር` | `skip` |
| `9.0105, 38.7612` | `9.0300, 38.7600` | `7.0500, 38.4700` |
| a description | a description | a description |

Then type `site` to build the website and `listings` to see stored records.

> Note: Oromo is low-resource, so its translation is flagged for human review and
> will **not** auto-publish — you'll see "we are reviewing the translation" instead
> of an immediate "live" confirmation. This is the intended safeguard.

---

## Level 2 — Automated tests

Scripted conversations assert that the right listing comes out the other end:

```bash
pip install pytest
pytest
```

Translation accuracy can be measured against the **FLORES-200** benchmark with the
evaluation harness in `eval/` (see `eval/README.md`).

---

## Level 3 — Local webhook with simulated gateway payloads

Real gateways deliver inbound SMS to your server via an HTTP webhook. You can
replay a realistic payload against a locally-running server **before** connecting a
real account, to confirm your adapter parses it correctly. Sample payloads for
Africa's Talking and Twilio live in `docs/sample_payloads/`.

---

## Level 4 — Real end-to-end SMS (for a live demo)

1. **Pick a gateway.** Africa's Talking has an Ethiopia presence and a free
   **sandbox with a built-in SMS simulator**; Twilio offers free trial credit.
2. **Get a number / shortcode** and set its inbound webhook URL.
3. **Expose your local server** to the internet with a tunnel (no deployment needed):
   ```bash
   ngrok http 8000
   ```
   Point the gateway's webhook at the `https://…ngrok…/sms` URL.
4. A real phone texting that number now flows through the exact same pipeline.

> For a hackathon demo, **Levels 1–2 are recommended** — they're reliable and don't
> depend on live telecom (which can be slow or incur costs). Keep Level 4 as the
> optional "live" showcase.

---

## Translating to Lithuanian (for the judges)

The translation layer uses NLLB-200, which supports English→Lithuanian (`lit_Latn`)
at high quality. Judges can verify accuracy by translating a published English
listing to Lithuanian:

```bash
ETHIOPIASMS_REAL_NLLB=1 python -c "
from app.ai.translation import get_translator
t = get_translator()
print(t.translate('Historic coffee house in the heart of Addis Ababa.', 'eng', 'lit').text)
"
```

(Requires `pip install transformers torch sentencepiece`. Without the flag, a mock
translator runs so the pipeline works offline.)
