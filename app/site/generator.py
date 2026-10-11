"""Static website generator — renders published listings to an English site.

Outputs plain HTML + a little vanilla JavaScript (no framework, no build step) so it
can be committed to the repo and served via GitHub Pages. Tourists can:
  * search by name/description,
  * filter by category and by location/city,
  * tap "Message on Telegram" to reach the owner for free via the Telegram↔SMS bridge.

Listings without a photo show an honest note that the owner has not added photos
yet — we never fill the gap with stock imagery of a place we don't represent.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from app.store.listings import Listing, ListingStore

DEFAULT_OUTPUT = Path("docs/site")

# The Telegram bot tourists message to reach a business. Replace with your real
# bot's username when you deploy one; the website links deep-link into it with the
# business as the `start` parameter so the bridge knows which owner to connect.
TELEGRAM_BOT_USERNAME = "EthiopiaSMSBot"


def _maps_link(listing: Listing) -> str | None:
    if listing.lat is not None and listing.lon is not None:
        return (f"https://www.openstreetmap.org/?mlat={listing.lat}&mlon={listing.lon}"
                f"#map=17/{listing.lat}/{listing.lon}")
    return None


def _location_of(listing: Listing) -> str:
    return (listing.area or "Ethiopia").strip()


def _card(listing: Listing) -> str:
    name = html.escape(listing.name_en or "Unnamed business")
    cat = html.escape(listing.category_en)
    desc = html.escape(listing.description_en or "")
    price = html.escape(listing.price_etb) if listing.price_etb else None
    loc = _maps_link(listing)
    location = _location_of(listing)
    area = html.escape(location)

    if listing.image_paths:
        img = f'<img src="{html.escape(listing.image_paths[0])}" alt="{name}" loading="lazy">'
    else:
        img = ('<div class="placeholder">'
               '<span>📷</span><small>The owner hasn\'t added photos yet</small></div>')

    meta = [f'<span class="cat">{cat}</span>', f'<span class="area">📍 {area}</span>']
    if price:
        meta.append(f'<span class="price">{price}</span>')

    # Booking goes through the Telegram ↔ SMS bridge: the tourist chats for FREE on
    # Telegram and the platform relays to the owner over cheap LOCAL SMS — no
    # expensive international SMS/calls for the tourist. The `start` parameter tells
    # the bot which business to connect the tourist to.
    import urllib.parse
    start = urllib.parse.quote(listing.upload_token or listing.name_en)
    tg = f"https://t.me/{TELEGRAM_BOT_USERNAME}?start={start}"
    links = [f'<a class="book" href="{html.escape(tg)}" target="_blank" rel="noopener">💬 Message on Telegram</a>']
    if loc:
        links.append(f'<a class="map" href="{loc}" target="_blank" rel="noopener">🗺️ Map</a>')

    # data-* attributes power the client-side search/filter.
    search_blob = html.escape(f"{listing.name_en} {listing.description_en} {cat} {location}".lower())
    return f"""      <article class="card" data-category="{cat}" data-location="{area}" data-search="{search_blob}">
        {img}
        <h2>{name}</h2>
        <div class="meta">{''.join(meta)}</div>
        <p>{desc}</p>
        <div class="links">{''.join(links)}</div>
      </article>"""


# Revenue products shown on the public site: a customisable itinerary planner, with
# tiered passes that also bundle SMS "texting credits" (used to message MSME owners
# via the Telegram↔SMS bridge). Prices in EUR.
PLANS = [
    {"name": "Day Pass", "price": "1", "benefit": "3× 1-day itineraries in one village / town",
     "credits": "5 SMS credits", "featured": False},
    {"name": "Trip Pack", "price": "3", "benefit": "3× 3-day itineraries in one region",
     "credits": "20 SMS credits", "featured": True},
    {"name": "Route Pass", "price": "5", "benefit": "5× 5–7 day itineraries across multiple regions",
     "credits": "Unlimited SMS credits", "featured": False},
    {"name": "Message Top-up", "price": "2", "benefit": "15× extra vendor SMS texts",
     "credits": "15 SMS credits", "featured": False},
]


def _pricing_section() -> str:
    cards = []
    for p in PLANS:
        tag = '<span class="tag">Most popular</span>' if p["featured"] else ""
        cls = "plan featured" if p["featured"] else "plan"
        choose_cls = "choose" if p["featured"] else "choose ghost"
        cards.append(f"""      <div class="{cls}">
        {tag}
        <h3>{p['name']}</h3>
        <div class="price">€{p['price']} <small>one-off</small></div>
        <p class="benefit">{p['benefit']}</p>
        <span class="credits">💬 {p['credits']}</span>
        <a class="{choose_cls}" href="#" onclick="return choosePlan('{p['name']}')">Choose {p['name']}</a>
      </div>""")
    plans_html = "\n".join(cards)
    return f"""  <section class="pricing" id="plans">
    <div class="pricing-inner">
      <h2>Plan your trip — and reach the businesses</h2>
      <p class="lede">Buy a pass to generate custom itineraries from real local reviews, and
         get SMS credits to message MSME owners directly for prices, directions and bookings.</p>

      <div class="features">
        <div class="feature">
          <h3>🗺️ Customisable itinerary planner</h3>
          <ul>
            <li>Itineraries built from tourist reviews — by trip length, location &amp; preferences.</li>
            <li>A nominal fee for convenient, ready-to-go trip planning.</li>
          </ul>
        </div>
        <div class="feature">
          <h3>💬 Texting credits</h3>
          <ul>
            <li>Message MSME operators directly for more information.</li>
            <li>Credits are included with every itinerary plan you buy.</li>
          </ul>
        </div>
      </div>

      <div class="plans">
{plans_html}
      </div>
      <p class="note">Prototype pricing shown for demonstration. Checkout &amp; payments are
         not yet connected — selecting a plan is illustrative only.</p>
    </div>
  </section>"""


def render_html(listings: list[Listing]) -> str:
    cards = "\n".join(_card(l) for l in listings) or '<p class="empty">No listings yet.</p>'
    categories = sorted({l.category_en for l in listings})
    locations = sorted({_location_of(l) for l in listings})
    cat_options = "".join(f'<option value="{html.escape(c)}">{html.escape(c)}</option>'
                          for c in categories)
    loc_options = "".join(f'<option value="{html.escape(l)}">{html.escape(l)}</option>'
                          for l in locations)
    total = len(listings)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Discover Local Ethiopia — Tourism Listings</title>
  <style>
    :root {{ --accent:#0a7d3c; }}
    * {{ box-sizing:border-box; }}
    body {{ font-family:system-ui,Segoe UI,Roboto,sans-serif; margin:0; background:#faf8f3; color:#222; }}
    header {{ background:var(--accent); color:#fff; padding:2rem 1rem; text-align:center; }}
    header h1 {{ margin:0 0 .25rem; }}
    header p {{ margin:0; opacity:.9; }}
    .controls {{ position:sticky; top:0; z-index:5; background:#fff; border-bottom:1px solid #e7e2d8;
                 padding:.9rem 1rem; display:flex; flex-wrap:wrap; gap:.6rem; justify-content:center;
                 box-shadow:0 1px 4px rgba(0,0,0,.05); }}
    .controls input, .controls select {{ padding:.55rem .7rem; border:1px solid #cbd5cf;
                 border-radius:8px; font-size:.9rem; background:#fff; }}
    .controls input {{ flex:1; min-width:200px; max-width:360px; }}
    .controls button {{ border:1px solid #cbd5cf; background:#f3f6f3; border-radius:8px;
                 padding:.55rem .8rem; cursor:pointer; font-size:.9rem; }}
    .count {{ text-align:center; color:#666; font-size:.85rem; padding:.6rem; }}
    main {{ max-width:1050px; margin:0 auto; padding:0 1rem 1.5rem;
            display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:1.25rem; }}
    .card {{ background:#fff; border:1px solid #e7e2d8; border-radius:12px; overflow:hidden;
             box-shadow:0 1px 3px rgba(0,0,0,.06); display:flex; flex-direction:column; }}
    .card img, .placeholder {{ width:100%; height:150px; object-fit:cover; }}
    .placeholder {{ display:flex; flex-direction:column; gap:.3rem; align-items:center;
                    justify-content:center; background:#f0ece2; color:#a99; text-align:center; padding:0 1rem; }}
    .placeholder span {{ font-size:1.6rem; }} .placeholder small {{ font-size:.78rem; }}
    .card h2 {{ font-size:1.1rem; margin:.75rem .9rem .25rem; }}
    .meta {{ margin:0 .9rem; display:flex; flex-wrap:wrap; gap:.4rem; }}
    .meta span {{ font-size:.75rem; padding:.15rem .5rem; border-radius:999px; background:#eef5ef; color:var(--accent); }}
    .card p {{ margin:.6rem .9rem; font-size:.9rem; color:#444; flex:1; }}
    .links {{ display:flex; gap:.5rem; padding:.9rem; border-top:1px solid #f0ece2; }}
    .links a {{ flex:1; text-align:center; text-decoration:none; font-size:.85rem; padding:.5rem; border-radius:8px; }}
    .book {{ background:var(--accent); color:#fff; }}
    .map {{ background:#eef5ef; color:var(--accent); }}
    footer {{ text-align:center; padding:1.5rem 1rem; font-size:.8rem; color:#888; }}
    .empty {{ grid-column:1/-1; text-align:center; color:#888; padding:2rem; }}
    /* pricing / plans section */
    .pricing {{ background:#fff; border-top:1px solid #e7e2d8; padding:2.5rem 1rem; }}
    .pricing-inner {{ max-width:1050px; margin:0 auto; }}
    .pricing h2 {{ text-align:center; color:var(--accent); margin:0 0 .25rem; font-size:1.6rem; }}
    .pricing .lede {{ text-align:center; color:#555; margin:0 auto 2rem; max-width:640px; font-size:.95rem; }}
    .features {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
                 gap:1.25rem; margin-bottom:2rem; }}
    .feature {{ border:1px solid #e7e2d8; border-radius:12px; padding:1.1rem 1.25rem; background:#faf8f3; }}
    .feature h3 {{ margin:0 0 .5rem; color:#1a1a1a; font-size:1.05rem; }}
    .feature ul {{ margin:0; padding-left:1.1rem; color:#444; font-size:.9rem; }}
    .feature li {{ margin:.3rem 0; }}
    .plans {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:1.1rem; }}
    .plan {{ border:1px solid #e7e2d8; border-radius:14px; padding:1.25rem; display:flex;
             flex-direction:column; box-shadow:0 1px 3px rgba(0,0,0,.05); position:relative; }}
    .plan.featured {{ border-color:var(--accent); box-shadow:0 4px 16px rgba(10,125,60,.15); }}
    .plan .tag {{ position:absolute; top:-11px; left:50%; transform:translateX(-50%);
                  background:var(--accent); color:#fff; font-size:.68rem; padding:.15rem .6rem;
                  border-radius:999px; letter-spacing:.03em; }}
    .plan h3 {{ margin:.25rem 0 .25rem; font-size:1.1rem; }}
    .plan .price {{ font-size:1.9rem; font-weight:700; color:var(--accent); }}
    .plan .price small {{ font-size:.8rem; color:#888; font-weight:400; }}
    .plan .benefit {{ color:#444; font-size:.9rem; margin:.6rem 0; flex:1; }}
    .plan .credits {{ font-size:.82rem; color:#0a7d3c; background:#eef5ef; border-radius:999px;
                      padding:.2rem .6rem; align-self:flex-start; }}
    .plan .choose {{ margin-top:1rem; text-align:center; text-decoration:none; background:var(--accent);
                     color:#fff; border-radius:8px; padding:.55rem; font-size:.9rem; }}
    .plan .choose.ghost {{ background:#eef5ef; color:var(--accent); }}
    .pricing .note {{ text-align:center; color:#999; font-size:.78rem; margin-top:1.25rem; }}
  </style>
</head>
<body>
  <header>
    <h1>Discover Local Ethiopia</h1>
    <p>Authentic businesses, direct from the owners.</p>
  </header>

  <div class="controls">
    <input id="q" type="search" placeholder="Search businesses, food, places…"
           aria-label="Search" oninput="applyFilters()">
    <select id="cat" aria-label="Filter by category" onchange="applyFilters()">
      <option value="">All categories</option>
      {cat_options}
    </select>
    <select id="loc" aria-label="Filter by location" onchange="applyFilters()">
      <option value="">All locations</option>
      {loc_options}
    </select>
    <button type="button" onclick="resetFilters()">Clear</button>
    <a href="#plans" style="text-decoration:none;"><button type="button">💶 Plans &amp; pricing</button></a>
  </div>
  <div class="count" id="count">{total} businesses</div>

  <main id="grid">
{cards}
    <p class="empty" id="noresults" style="display:none">No businesses match your search. Try clearing the filters.</p>
  </main>

{_pricing_section()}

  <footer>
    Tap <strong>Message on Telegram</strong> to reach a business free of charge — your
    message is relayed to the owner by local SMS and their reply comes back to you, so
    there are no international SMS or call costs.<br>
    Business names, phone numbers &amp; locations © OpenStreetMap contributors (ODbL).
    Most listings have no photo yet — owners add their own via SMS. The two photographed
    businesses use openly-licensed images (Wikimedia Commons: Ben Abeba CC BY 2.0; Sheraton Addis, public domain).
  </footer>

  <script>
    const TOTAL = {total};
    function applyFilters() {{
      const q = document.getElementById('q').value.trim().toLowerCase();
      const cat = document.getElementById('cat').value;
      const loc = document.getElementById('loc').value;
      let shown = 0;
      document.querySelectorAll('.card').forEach(card => {{
        const matchQ = !q || card.dataset.search.includes(q);
        const matchCat = !cat || card.dataset.category === cat;
        const matchLoc = !loc || card.dataset.location === loc;
        const show = matchQ && matchCat && matchLoc;
        card.style.display = show ? '' : 'none';
        if (show) shown++;
      }});
      document.getElementById('count').textContent =
        shown === TOTAL ? TOTAL + ' businesses' : shown + ' of ' + TOTAL + ' businesses';
      document.getElementById('noresults').style.display = shown ? 'none' : '';
    }}
    function resetFilters() {{
      document.getElementById('q').value = '';
      document.getElementById('cat').value = '';
      document.getElementById('loc').value = '';
      applyFilters();
    }}
    function choosePlan(name) {{
      alert("You chose the " + name + " plan.\\n\\nThis is a prototype — payment "
            + "checkout isn't connected yet. In the full product this would start "
            + "secure payment and credit your SMS texting balance.");
      return false;
    }}
  </script>
</body>
</html>
"""


def build_site(store: ListingStore, output_dir: Path = DEFAULT_OUTPUT) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    index = output_dir / "index.html"
    index.write_text(render_html(store.published()), encoding="utf-8")
    return index
