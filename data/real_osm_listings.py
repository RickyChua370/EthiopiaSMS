"""Real Addis Ababa businesses sourced from OpenStreetMap.

These are ACTUAL places — names, phone numbers and coordinates come straight from
OpenStreetMap (© OpenStreetMap contributors, ODbL). They are the "mappable but
website-less" tourism MSMEs this project targets.

Photos: OSM has essentially no photos for these businesses, and we will NOT scrape
copyrighted images or fake a specific business's premises. Instead, each listing may
carry an openly-licensed, clearly-GENERIC category image (see data/category_images)
— exactly mirroring the real product, where the photo slot stays a placeholder until
the *owner* uploads their own via their upload link.

Descriptions are short, factual summaries derived from the OSM tags (category,
cuisine) — not marketing copy invented about the business.
"""

from __future__ import annotations

# (name, category_id, phone, lat, lon, short factual description, generic_image_key|None)
REAL_BUSINESSES = [
    ("Abucci", 1, "+251 912 501 828", 9.0002, 38.7830,
     "Italian restaurant in Addis Ababa.", "restaurant"),
    ("Arirang Korean Restaurant", 1, "+251 911 22 53 19", 8.9997, 38.7200,
     "Korean restaurant in Addis Ababa.", "restaurant"),
    ("Aman Catering and Agelgil", 1, "+251916137579", 7.0446, 38.5115,
     "Restaurant serving Ethiopian cuisine.", "ethiopian_food"),
    ("Antica Cafe & Restaurant", 1, "+251116634841", 8.9964, 38.7793,
     "Cafe and restaurant known for pizza.", "restaurant"),
    ("Ambrosia Cafe", 2, "+251115521110", 9.0049, 38.7672,
     "Cafe in Addis Ababa.", "coffee"),
    ("Alem Buna", 2, "+251111570887", 9.0335, 38.7549,
     "Traditional Ethiopian coffee house.", "coffee"),
    ("Ambassador Hotel Bole", 3, "+251116188284", 8.9921, 38.7880,
     "Hotel in the Bole area of Addis Ababa.", "hotel"),
    ("Adot Tina Hotel", 3, "+251114673939", 8.9914, 38.7671,
     "Hotel in Addis Ababa.", "hotel"),
    ("Aaran Hotel", 3, "+251116392240", 8.9833, 38.7762,
     "Hotel in Addis Ababa.", "hotel"),
]
