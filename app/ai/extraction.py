"""Field extraction helpers.

Phase 1 extracts the structured fields that can be parsed reliably with rules —
coordinates and price — regardless of language. Free-text fields (name,
description) are collected directly via the guided conversation flow, so they do
not need a model yet. In Phase 2 a slot-filling model (warm-started on MASSIVE,
which includes Amharic) can replace the guided flow with free-form extraction.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Ethiopia bounding box (approx) for sanity-checking coordinates.
LAT_MIN, LAT_MAX = 3.0, 15.5
LON_MIN, LON_MAX = 32.5, 48.5


@dataclass
class Coordinates:
    lat: float
    lon: float


def parse_coordinates(text: str) -> Coordinates | None:
    """Parse two decimal numbers as lat/lon and validate they fall within Ethiopia.

    Accepts separators like comma, space, or 'and'. Returns None if not parseable
    or out of range.
    """
    nums = re.findall(r"[-+]?\d{1,3}(?:\.\d+)?", text)
    if len(nums) < 2:
        return None
    lat, lon = float(nums[0]), float(nums[1])
    if LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX:
        return Coordinates(lat, lon)
    # Try swapped order (owner may send lon first).
    if LAT_MIN <= lon <= LAT_MAX and LON_MIN <= lat <= LON_MAX:
        return Coordinates(lon, lat)
    return None


def parse_price(text: str) -> str | None:
    """Extract an approximate price string, normalised to 'NNN ETB'.

    Recognises 'birr'/'ብር'/'ETB' or a bare number. Returns None for 'skip'/empty.
    """
    lowered = text.strip().lower()
    if lowered in {"skip", "none", "-", ""}:
        return None
    m = re.search(r"(\d[\d,\.]*)", text)
    if not m:
        return None
    amount = m.group(1).replace(",", "")
    return f"{amount} ETB"
