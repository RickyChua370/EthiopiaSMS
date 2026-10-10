# Deploying the simulator to a public URL (Render)

This gives judges a **clickable link** to the interactive simulator — no Python,
no commands. It deploys the owner-SMS onboarding, the public website, and the
tourist↔owner booking bridge, with **real translation** via the free MyMemory API
(no heavy model, so it fits Render's free tier).

> Why a host (not GitHub Pages)? The simulator is a running Python server, so it
> needs a host that runs processes. GitHub Pages only serves static files.

## One-time deploy (~5 minutes)

1. **Create a free Render account:** https://render.com (sign in with GitHub).
2. In the Render dashboard, click **New → Blueprint**.
3. **Connect this repository** (`RickyChua370/EthiopiaSMS`). Render reads
   `render.yaml` automatically.
4. Click **Apply**. Render builds and starts the service.
5. When it finishes, Render shows a public URL like
   `https://ethiopiasms-simulator.onrender.com` — **that's the link for judges.**

That's it. No build commands to type; `render.yaml` configures everything
(start command, Python version, and `ETHIOPIASMS_TRANSLATOR=mymemory` for real
translation).

## What judges will see at the link

- **Top:** a business owner onboarding by SMS → the listing appears on the website.
- **Bottom:** the booking bridge — a tourist (Telegram) and owner (SMS) chatting,
  translated both ways in real time.
- The **🇱🇹 Lithuanian (judge test)** button translates a listing to Lithuanian so
  judges can verify quality in their own language.

## Important note on the free tier

Render's free web services **sleep after ~15 minutes of inactivity**. The first
visit after a nap takes **~30–50 seconds to wake up** — this is normal, not a
crash. Tell judges: *"if the page is slow to load the first time, give it up to a
minute."* Keeping a browser tab open or pinging it shortly before judging avoids
the cold start.

## Translation on the hosted version

The hosted app uses the **MyMemory** free translation API (set via
`ETHIOPIASMS_TRANSLATOR=mymemory` in `render.yaml`). It covers all four languages
(Amharic, Afaan Oromo, Lithuanian, English) with no model download. The anonymous
free tier has a daily character limit; for a demo that's ample. To raise the limit,
add a `MYMEMORY_EMAIL` environment variable in Render with any email address.

## Alternatives

- **Railway** (https://railway.app): similar flow; use start command
  `python -m app.web` and set `ETHIOPIASMS_TRANSLATOR=mymemory`.
- **Hugging Face Spaces**: good if you later want the full 2.4 GB NLLB model
  (`ETHIOPIASMS_REAL_NLLB=1`) on paid hardware.

## Running locally instead

No deployment needed to try it yourself:
```bash
ETHIOPIASMS_TRANSLATOR=mymemory python -m app.web   # real translation, light
# or
python -m app.web                                   # mock (offline) translation
```
Then open http://localhost:8000.
