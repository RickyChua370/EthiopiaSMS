"""Web-based SMS simulator — a demo-ready, on-screen "phone".

Run:
    python -m app.web          # then open http://localhost:8000

Left panel: a phone that sends/receives SMS through the real pipeline.
Right panel: the live public website, which refreshes as listings are published.

Uses only the Python standard library (no framework) so it runs with zero installs,
consistent with Phase 1. The same ConversationEngine powers CLI, web, and (later)
real gateways — this is purely another front-end over the gateway-agnostic core.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from app.adapters.mock import MockAdapter
from app.adapters.telegram_mock import MockTelegramAdapter
from app.bridge.hub import BridgeHub
from app.conversation.flow import ConversationEngine
from app.site.generator import render_html
from app.store.listings import ListingStore

HOST, PORT = "0.0.0.0", 8000

# Each browser "phone number" gets its own conversation; a simple in-memory store
# keeps the demo self-contained (no file writes needed for the live demo).
_store = ListingStore(Path("data/web_demo_listings.json"))
_engine = ConversationEngine(_store)
_translator = _engine.translator  # same translator the pipeline uses
_lock = threading.Lock()

# --- Booking bridge (Telegram <-> SMS) for the on-screen booking demo ---------
# The web page polls the two mock adapters' outboxes to render the tourist's chat
# (Telegram side) and the owner's phone (SMS side).
_bk_sms = MockAdapter()
_bk_tg = MockTelegramAdapter()
_bridge = BridgeHub(_bk_sms, _bk_tg, translator=_translator)
_BK_CHAT = "web-tourist"           # single tourist chat for the demo
_bk_tg_seen = 0                    # how many tourist(Telegram) msgs the page has shown
_bk_sms_seen = 0                   # how many owner(SMS) msgs the page has shown


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EthiopiaSMS — Live Demo</title>
<style>
  * { box-sizing:border-box; }
  body { margin:0; font-family:system-ui,Segoe UI,Roboto,sans-serif; background:#eef1f4; color:#1a1a1a; }
  header { background:#0a7d3c; color:#fff; padding:1rem 1.5rem; }
  header h1 { margin:0; font-size:1.2rem; }
  header p { margin:.25rem 0 0; opacity:.9; font-size:.85rem; }
  .wrap { display:flex; gap:1.5rem; padding:1.5rem; align-items:flex-start; flex-wrap:wrap; }
  /* phone */
  .phone { width:330px; background:#111; border-radius:28px; padding:12px; box-shadow:0 10px 30px rgba(0,0,0,.25); }
  .screen { background:#e5ddd5; border-radius:18px; height:520px; display:flex; flex-direction:column; overflow:hidden; }
  .bar { background:#0a7d3c; color:#fff; padding:.6rem .9rem; font-size:.85rem; }
  .bar small { opacity:.85; }
  .msgs { flex:1; padding:.75rem; overflow-y:auto; display:flex; flex-direction:column; gap:.5rem; }
  .b { max-width:80%; padding:.5rem .7rem; border-radius:12px; font-size:.85rem; white-space:pre-wrap;
       line-height:1.3; overflow-wrap:break-word; word-break:break-word; }
  .in { align-self:flex-end; background:#dcf8c6; }
  .out { align-self:flex-start; background:#fff; }
  .compose { display:flex; border-top:1px solid #ccc; }
  .compose input { flex:1; border:0; padding:.7rem; font-size:.9rem; outline:none; background:#fff; }
  .compose button { border:0; background:#0a7d3c; color:#fff; padding:0 1rem; cursor:pointer; }
  .quick { padding:.5rem .75rem; background:#f7f7f7; border-top:1px solid #eee; font-size:.75rem; }
  .quick b { color:#0a7d3c; }
  .quick button { margin:.15rem; border:1px solid #cbd5cf; background:#fff; border-radius:999px;
                  padding:.2rem .55rem; cursor:pointer; font-size:.75rem; }
  .reset { margin:.5rem 0 0; }
  .reset button { background:#b23; color:#fff; border:0; border-radius:8px; padding:.4rem .8rem; cursor:pointer; }
  /* site preview */
  .site { flex:1; min-width:340px; background:#fff; border-radius:14px; overflow:hidden;
          box-shadow:0 4px 16px rgba(0,0,0,.08); }
  .site .sitehead { background:#0a7d3c; color:#fff; padding:.6rem 1rem; display:flex; justify-content:space-between; align-items:center; }
  .site iframe { width:100%; height:520px; border:0; }
  .hint { font-size:.8rem; color:#555; }
  /* booking bridge section */
  .section-title { padding:1rem 1.5rem .25rem; font-size:1.05rem; font-weight:600; }
  .section-sub { padding:0 1.5rem 1rem; font-size:.85rem; color:#555; max-width:900px; }
  .tg-bar { background:#2aabee; }        /* Telegram blue for the tourist side */
  .tg-in { background:#cfeffd; }         /* tourist's own messages */
  .biz-pick { padding:.5rem .75rem; background:#f7f7f7; border-top:1px solid #eee; font-size:.78rem; }
  .biz-pick select { width:100%; padding:.4rem; border:1px solid #cbd5cf; border-radius:6px; margin-top:.25rem; }
</style>
</head>
<body>
<header>
  <h1>EthiopiaSMS — Live Demo</h1>
  <p>Top: a business owner onboards via SMS → listing appears on the website.
     Bottom: a tourist books via Telegram ↔ the owner's SMS, translated both ways.</p>
</header>
<div class="wrap">
  <div>
    <div class="phone">
      <div class="screen">
        <div class="bar">EthiopiaSMS service <small id="who"></small></div>
        <div class="msgs" id="msgs"></div>
        <div class="quick" id="quick">
          <b>Quick fill:</b>
          <div>
            <button onclick="fill('en')">🇬🇧 English flow</button>
            <button onclick="fill('am')">🇪🇹 Amharic flow</button>
            <button onclick="fill('om')">Oromo flow</button>
            <button onclick="lithuanianTest()">🇱🇹 Lithuanian (judge test)</button>
          </div>
        </div>
        <div class="compose">
          <input id="inp" placeholder="Type a message…" autocomplete="off"
                 onkeydown="if(event.key==='Enter')send()">
          <button onclick="send()">Send</button>
        </div>
      </div>
    </div>
    <div class="reset"><button onclick="reset()">↺ New owner (reset conversation)</button></div>
    <p class="hint">Each reset uses a new phone number, like a different owner texting in.</p>
  </div>

  <div class="site">
    <div class="sitehead"><span>🌍 Public website (what tourists see)</span>
      <span class="hint" style="color:#dfe">auto-refreshes</span></div>
    <iframe id="siteframe" src="/site"></iframe>
  </div>
</div>

<!-- ================= Booking bridge: Telegram <-> SMS ================= -->
<div class="section-title">💬 Booking bridge — tourist (Telegram) ↔ owner (SMS)</div>
<div class="section-sub">
  A tourist chats for <b>free on Telegram</b>; the message is translated and relayed to the
  owner as a cheap <b>local SMS</b>. The owner replies by SMS and it comes back to the
  tourist — no expensive international SMS. Pick a business, send an inquiry on the left,
  then reply as the owner on the right.
</div>
<div class="wrap">
  <!-- Tourist side (Telegram) -->
  <div>
    <div class="phone">
      <div class="screen">
        <div class="bar tg-bar">🧳 Tourist · Telegram</div>
        <div class="msgs" id="tg-msgs"></div>
        <div class="biz-pick">
          <label for="biz">Inquiring about:</label>
          <select id="biz" onchange="startBooking()">
            <option value="Tomoca Coffee|+251911223344|amh">Tomoca Coffee (Amharic owner)</option>
            <option value="Harka Hojii Aadaa|+251922556677|orm">Harka Hojii Aadaa (Oromo owner)</option>
            <option value="Sheraton Addis|+251115171717|eng">Sheraton Addis (English owner)</option>
          </select>
        </div>
        <div class="compose">
          <input id="tg-inp" placeholder="Ask the business (English)…" autocomplete="off"
                 onkeydown="if(event.key==='Enter')touristSend()">
          <button onclick="touristSend()">Send</button>
        </div>
      </div>
    </div>
    <p class="hint">The tourist writes in English, free over Telegram.</p>
  </div>

  <!-- Owner side (SMS) -->
  <div>
    <div class="phone">
      <div class="screen">
        <div class="bar">📟 Owner · SMS (basic phone)</div>
        <div class="msgs" id="own-msgs"></div>
        <div class="compose">
          <input id="own-inp" placeholder="Reply as the owner (their language)…" autocomplete="off"
                 onkeydown="if(event.key==='Enter')ownerSend()">
          <button onclick="ownerSend()">Reply</button>
        </div>
      </div>
    </div>
    <p class="hint">The owner only ever uses normal SMS — never needs Telegram.</p>
  </div>
</div>

<script>
let phone = newPhone();
function newPhone(){ return "+2519" + Math.floor(10000000 + Math.random()*89999999); }
document.getElementById('who').textContent = "("+phone+")";

const scripts = {
  en: ["hello","2","Tomoca Coffee","150 birr","9.0105, 38.7612",
       "Historic coffee house in the heart of Addis Ababa, roasting since 1953."],
  am: ["\u1230\u120b\u121d","1","\u12e8\u1200\u1260\u123b \u121d\u130d\u1265 \u1264\u1275","200 \u1265\u122d",
       "9.0300, 38.7600","\u1263\u1205\u120b\u12ca \u12e8\u12a2\u1275\u12ee\u1335\u12eb \u121d\u130d\u1265\u1362"],
  om: ["nagaa","4","Harka Hojii Aadaa","skip","7.0500, 38.4700",
       "Meeshaalee aadaa harkaan hojjetaman gurgurra."]
};
let queue = [];

function add(text, cls){
  const d=document.createElement('div'); d.className='b '+cls; d.textContent=text;
  const m=document.getElementById('msgs'); m.appendChild(d); m.scrollTop=m.scrollHeight;
}
async function send(){
  const inp=document.getElementById('inp'); const text=inp.value.trim();
  if(!text) return; inp.value=''; add(text,'in');
  const res=await fetch('/sms',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({phone:phone,text:text})});
  const data=await res.json();
  for(const r of data.replies){ add(r,'out'); }
  // refresh the website preview
  document.getElementById('siteframe').src='/site?t='+Date.now();
  if(queue.length){ setTimeout(()=>{ document.getElementById('inp').value=queue.shift(); send(); }, 500); }
}
function fill(lang){
  queue = scripts[lang].slice();
  document.getElementById('inp').value = queue.shift(); send();
}
// Judge aid: translate an English listing sentence to Lithuanian so Lithuanian
// judges can verify translation quality in their own language.
async function lithuanianTest(){
  const sample = "Historic coffee house in the heart of Addis Ababa, roasting since 1953.";
  add("🇱🇹 Judge test — translate English → Lithuanian", "in");
  add("English: " + sample, "out");
  try {
    const res = await fetch('/translate', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({text: sample, source:'eng', target:'lit'})});
    const data = await res.json();
    add("Lietuvių (Lithuanian): " + data.text, "out");
    add("Engine: " + data.engine + (data.mock ? " — enable real NLLB for live translation" : ""), "out");
  } catch(e){
    add("Translation unavailable in this session.", "out");
  }
}
function reset(){
  phone=newPhone(); document.getElementById('who').textContent="("+phone+")";
  document.getElementById('msgs').innerHTML=''; queue=[];
}

/* ---------------- Booking bridge (Telegram <-> SMS) ---------------- */
function addTo(elId, text, cls){
  const d=document.createElement('div'); d.className='b '+cls; d.textContent=text;
  const m=document.getElementById(elId); m.appendChild(d); m.scrollTop=m.scrollHeight;
}
function currentBiz(){
  const [name,phone,lang] = document.getElementById('biz').value.split('|');
  return {name, phone, lang};
}
async function startBooking(){
  const b = currentBiz();
  document.getElementById('tg-msgs').innerHTML='';
  document.getElementById('own-msgs').innerHTML='';
  await fetch('/booking/start',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({business:b.name, owner_phone:b.phone, owner_lang:b.lang})});
}
async function touristSend(){
  const inp=document.getElementById('tg-inp'); const text=inp.value.trim();
  if(!text) return; inp.value=''; addTo('tg-msgs', text, 'in tg-in');
  await fetch('/booking/tourist',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text})});
}
async function ownerSend(){
  const inp=document.getElementById('own-inp'); const text=inp.value.trim();
  if(!text) return; inp.value=''; addTo('own-msgs', text, 'in');
  await fetch('/booking/owner',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text})});
}
// Poll for relayed messages and render them on the correct side.
async function pollBooking(){
  try {
    const res = await fetch('/booking/poll'); const data = await res.json();
    for(const t of data.tourist){ addTo('tg-msgs', t, 'out'); }     // bot/owner -> tourist
    for(const o of data.owner){ addTo('own-msgs', o, 'out'); }      // tourist -> owner SMS
  } catch(e){}
  setTimeout(pollBooking, 1200);
}
startBooking();   // open the first thread on load
pollBooking();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/site":
            with _lock:
                html = render_html(_store.published())
            self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/booking/poll":
            # Return any new messages for the tourist (Telegram) and owner (SMS) sides.
            global _bk_tg_seen, _bk_sms_seen
            with _lock:
                tourist = [m.text for m in _bk_tg.outbox[_bk_tg_seen:]]
                owner = [m.text for m in _bk_sms.outbox[_bk_sms_seen:]]
                _bk_tg_seen = len(_bk_tg.outbox)
                _bk_sms_seen = len(_bk_sms.outbox)
            self._send(200, json.dumps({"tourist": tourist, "owner": owner}).encode("utf-8"),
                       "application/json; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")

        if path == "/sms":
            phone = str(payload.get("phone", "+251900000000"))
            text = str(payload.get("text", ""))
            with _lock:
                replies = _engine.handle(phone, text)
            self._send(200, json.dumps({"replies": replies}).encode("utf-8"),
                       "application/json; charset=utf-8")
        elif path == "/translate":
            text = str(payload.get("text", ""))
            source = str(payload.get("source", "eng"))
            target = str(payload.get("target", "lit"))
            result = _translator.translate(text, source, target)
            is_mock = type(_translator).__name__ == "MockTranslator"
            self._send(200, json.dumps({
                "text": result.text, "engine": result.engine, "mock": is_mock,
            }).encode("utf-8"), "application/json; charset=utf-8")
        elif path == "/booking/start":
            # Tourist taps "Message on Telegram" for a business.
            name = str(payload.get("business", "a business"))
            phone = str(payload.get("owner_phone", "+251911223344"))
            lang = str(payload.get("owner_lang", "amh"))
            with _lock:
                _bridge.start_inquiry(_BK_CHAT, phone, lang, name)
            self._send(200, b'{"ok":true}', "application/json; charset=utf-8")
        elif path == "/booking/tourist":
            # Tourist sends a message (English) via Telegram.
            text = str(payload.get("text", ""))
            with _lock:
                _bk_tg.receive(_BK_CHAT, text)
            self._send(200, b'{"ok":true}', "application/json; charset=utf-8")
        elif path == "/booking/owner":
            # Owner replies by SMS (in their language).
            text = str(payload.get("text", ""))
            thread = _bridge.thread_for_chat(_BK_CHAT)
            if thread:
                with _lock:
                    _bk_sms.receive(thread.owner_phone, f"[{thread.ref}] {text}")
            self._send(200, b'{"ok":true}', "application/json; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def log_message(self, *args) -> None:  # silence default logging
        pass


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"EthiopiaSMS web simulator running: http://localhost:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
