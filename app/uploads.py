"""Deferred, connection-aware image upload server.

A listing goes live from SMS text immediately (no internet needed on the owner's
side). The owner is texted a unique link like:

    https://.../upload/<token>

They open it **whenever they next have internet** (a wifi spot, a relative's phone)
to attach photos. Uploaded images are saved and linked to the already-live listing,
so they appear on the public website without the listing ever having been blocked
on connectivity.

Stdlib only (http.server + manual multipart parsing), consistent with the rest of
the project. Run:

    python -m app.uploads        # then open http://localhost:8001/upload/<token>
"""

from __future__ import annotations

import re
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from app.store.listings import ListingStore

HOST, PORT = "0.0.0.0", 8001
UPLOAD_DIR = Path("uploads")                 # where image bytes are stored
ALLOWED = {b"\xff\xd8\xff": "jpg",           # JPEG magic
           b"\x89PNG": "png"}                # PNG magic
MAX_BYTES = 6 * 1024 * 1024                  # 6 MB per request guard
_store = ListingStore(Path("data/web_demo_listings.json"))


# --------------------------------------------------------------------- multipart

def _parse_multipart(body: bytes, boundary: bytes) -> list[tuple[str, bytes]]:
    """Minimal multipart/form-data parser.

    Returns a list of (filename, file_bytes) for each uploaded file part.
    """
    files: list[tuple[str, bytes]] = []
    delimiter = b"--" + boundary
    for part in body.split(delimiter):
        part = part.strip(b"\r\n")
        if not part or part == b"--":
            continue
        header_blob, _, data = part.partition(b"\r\n\r\n")
        if not data:
            continue
        headers = header_blob.decode("latin-1", "ignore")
        m = re.search(r'filename="([^"]*)"', headers)
        if not m or not m.group(1):
            continue  # skip non-file fields
        files.append((m.group(1), data.rstrip(b"\r\n")))
    return files


def _detect_ext(data: bytes) -> str | None:
    for magic, ext in ALLOWED.items():
        if data.startswith(magic):
            return ext
    return None


def _save_images(token: str, files: list[tuple[str, bytes]]) -> list[str]:
    """Validate + persist image files; return relative web paths that were saved."""
    saved: list[str] = []
    dest = UPLOAD_DIR / token
    dest.mkdir(parents=True, exist_ok=True)
    for _name, data in files:
        ext = _detect_ext(data)
        if ext is None:
            continue  # not a real JPEG/PNG — reject silently
        fname = f"{secrets.token_hex(6)}.{ext}"
        (dest / fname).write_bytes(data)
        # relative path the generated site can reference
        saved.append(str(Path("uploads") / token / fname))
    return saved


# --------------------------------------------------------------------- rendering

def _upload_page(token: str) -> tuple[int, str]:
    listing = _store.find_by_token(token)
    if listing is None:
        return 404, _simple("Link not found",
                            "This upload link is not valid. Please check the SMS you received.")
    existing = "".join(
        f'<img src="/{p}" alt="photo">' for p in listing.image_paths
    ) or '<p class="muted">No photos yet.</p>'
    return 200, f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Add photos — {_esc(listing.name_en)}</title>
<style>
  body{{font-family:system-ui,sans-serif;background:#faf8f3;margin:0;color:#222}}
  .card{{max-width:460px;margin:2rem auto;background:#fff;border:1px solid #e7e2d8;
         border-radius:14px;padding:1.5rem;box-shadow:0 2px 10px rgba(0,0,0,.06)}}
  h1{{font-size:1.2rem;margin:.2rem 0}} .cat{{color:#0a7d3c;font-size:.85rem}}
  .thumbs{{display:flex;gap:.5rem;flex-wrap:wrap;margin:1rem 0}}
  .thumbs img{{width:72px;height:72px;object-fit:cover;border-radius:8px}}
  .muted{{color:#999;font-size:.9rem}}
  input[type=file]{{display:block;margin:1rem 0;width:100%}}
  button{{background:#0a7d3c;color:#fff;border:0;border-radius:8px;padding:.7rem 1.2rem;
          font-size:1rem;cursor:pointer;width:100%}}
  .note{{font-size:.8rem;color:#666;margin-top:1rem}}
</style></head>
<body>
  <div class="card">
    <div class="cat">{_esc(listing.category_en)}</div>
    <h1>{_esc(listing.name_en)}</h1>
    <p class="muted">Your listing is already live. Add photos below — they'll appear on
      your public page right away.</p>
    <div class="thumbs">{existing}</div>
    <form method="POST" enctype="multipart/form-data" action="/upload/{token}">
      <input type="file" name="photos" accept="image/png,image/jpeg" multiple required>
      <button type="submit">Upload photos</button>
    </form>
    <p class="note">JPEG or PNG. You only need internet for this step — your listing was
      published from your SMS already.</p>
  </div>
</body></html>"""


def _result_page(token: str, n: int) -> str:
    return _simple(
        "Photos added ✓",
        f"{n} photo(s) added to your listing. They are now visible to tourists. "
        f'<br><br><a href="/upload/{token}">Add more</a>',
    )


def _simple(title: str, body: str) -> str:
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{_esc(title)}</title>
<style>body{{font-family:system-ui,sans-serif;background:#faf8f3;color:#222;
text-align:center;padding:3rem 1rem}}a{{color:#0a7d3c}}</style></head>
<body><h1>{_esc(title)}</h1><p>{body}</p></body></html>"""


def _esc(s: str) -> str:
    import html
    return html.escape(s or "")


# --------------------------------------------------------------------- server

class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path.startswith("/upload/"):
            token = path[len("/upload/"):]
            code, html = _upload_page(token)
            self._send(code, html.encode("utf-8"), "text/html; charset=utf-8")
        elif path.startswith("/uploads/"):
            self._serve_image(path.lstrip("/"))
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not path.startswith("/upload/"):
            self._send(404, b"not found", "text/plain")
            return
        token = path[len("/upload/"):]
        if _store.find_by_token(token) is None:
            self._send(404, _simple("Link not found", "Invalid link.").encode(), "text/html")
            return
        ctype = self.headers.get("Content-Type", "")
        m = re.search(r"boundary=(.+)", ctype)
        length = int(self.headers.get("Content-Length", 0))
        if not m or length <= 0 or length > MAX_BYTES:
            self._send(400, _simple("Upload failed", "Could not read the upload.").encode(),
                       "text/html")
            return
        body = self.rfile.read(length)
        files = _parse_multipart(body, m.group(1).encode("latin-1"))
        saved = _save_images(token, files)
        if saved:
            _store.attach_images(token, saved)
            self._send(200, _result_page(token, len(saved)).encode(), "text/html; charset=utf-8")
        else:
            self._send(400, _simple("No valid images",
                                    "Please upload JPEG or PNG files.").encode(), "text/html")

    def _serve_image(self, relpath: str) -> None:
        p = Path(relpath)
        if ".." in p.parts or not p.exists() or not str(p).startswith("uploads/"):
            self._send(404, b"not found", "text/plain")
            return
        ctype = "image/png" if p.suffix == ".png" else "image/jpeg"
        self._send(200, p.read_bytes(), ctype)

    def log_message(self, *args) -> None:
        pass


def main() -> None:
    UPLOAD_DIR.mkdir(exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"EthiopiaSMS upload server running: http://localhost:{PORT}/upload/<token>")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
