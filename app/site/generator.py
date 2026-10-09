"""Static website generator — renders published listings to an English site.

Outputs plain HTML (no framework, no build step) so it can be committed to the repo
and served via GitHub Pages. Tourists can browse listings and tap "Call to book",
which uses a `tel:` link to the owner's phone. Listings without photos yet show a
tasteful placeholder until images arrive.
"""

from __future__ import annotations

import html
from pathlib import Path

from app.store.listings import Listing, ListingStore

DEFAULT_OUTPUT = Path("docs/site")  # docs/ so GitHub Pages can serve it directly


def _maps_link(listing: Listing) -> str | None:
    if listing.lat is not None and listing.lon is not None:
        return f"https://www.openstreetmap.org/?mlat={listing.lat}&mlon={listing.lon}#map=17/{listing.lat}/{listing.lon}"
    return None


def _card(listing: Listing) -> str:
    name = html.escape(listing.name_en or "Unnamed business")
    cat = html.escape(listing.category_en)
    desc = html.escape(listing.description_en or "")
    price = html.escape(listing.price_etb) if listing.price_etb else None
    loc = _maps_link(listing)
    area = html.escape(listing.area) if listing.area else None

    if listing.image_paths:
        img = f'<img src="{html.escape(listing.image_paths[0])}" alt="{name}">'
    else:
        img = '<div class="placeholder">📷 Photos coming soon</div>'

    meta = [f'<span class="cat">{cat}</span>']
    if price:
        meta.append(f'<span class="price">{price}</span>')
    if area:
        meta.append(f'<span class="area">{area}</span>')

    links = [f'<a class="book" href="tel:{html.escape(listing.phone)}">📞 Call to book</a>']
    if loc:
        links.append(f'<a class="map" href="{loc}" target="_blank" rel="noopener">📍 View location</a>')

    return f"""      <article class="card">
        {img}
        <h2>{name}</h2>
        <div class="meta">{''.join(meta)}</div>
        <p>{desc}</p>
        <div class="links">{''.join(links)}</div>
      </article>"""


def render_html(listings: list[Listing]) -> str:
    cards = "\n".join(_card(l) for l in listings) or '<p class="empty">No listings yet.</p>'
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
    main {{ max-width:1000px; margin:0 auto; padding:1.5rem 1rem;
            display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:1.25rem; }}
    .card {{ background:#fff; border:1px solid #e7e2d8; border-radius:12px; overflow:hidden;
             box-shadow:0 1px 3px rgba(0,0,0,.06); display:flex; flex-direction:column; }}
    .card img, .placeholder {{ width:100%; height:150px; object-fit:cover; }}
    .placeholder {{ display:flex; align-items:center; justify-content:center;
                    background:#f0ece2; color:#998; font-size:.9rem; }}
    .card h2 {{ font-size:1.1rem; margin:.75rem .9rem .25rem; }}
    .meta {{ margin:0 .9rem; display:flex; flex-wrap:wrap; gap:.4rem; }}
    .meta span {{ font-size:.75rem; padding:.15rem .5rem; border-radius:999px; background:#eef5ef; color:var(--accent); }}
    .card p {{ margin:.6rem .9rem; font-size:.9rem; color:#444; flex:1; }}
    .links {{ display:flex; gap:.5rem; padding:.9rem; border-top:1px solid #f0ece2; }}
    .links a {{ flex:1; text-align:center; text-decoration:none; font-size:.85rem;
                padding:.5rem; border-radius:8px; }}
    .book {{ background:var(--accent); color:#fff; }}
    .map {{ background:#eef5ef; color:var(--accent); }}
    footer {{ text-align:center; padding:1.5rem 1rem; font-size:.8rem; color:#888; }}
    .empty {{ grid-column:1/-1; text-align:center; color:#888; }}
  </style>
</head>
<body>
  <header>
    <h1>Discover Local Ethiopia</h1>
    <p>Authentic businesses, direct from the owners.</p>
  </header>
  <main>
{cards}
  </main>
  <footer>
    Business names, phone numbers &amp; locations © OpenStreetMap contributors (ODbL).
    Category images are generic, openly-licensed illustrations (CC0 / CC BY / CC BY-SA
    via Wikimedia Commons) &mdash; not photos of the specific business; owners add their
    own photos via SMS.
  </footer>
</body>
</html>
"""


def build_site(store: ListingStore, output_dir: Path = DEFAULT_OUTPUT) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    index = output_dir / "index.html"
    index.write_text(render_html(store.published()), encoding="utf-8")
    return index
