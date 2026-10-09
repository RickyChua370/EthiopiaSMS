"""Business category taxonomy.

Owners select a category by replying with its number over SMS. Labels are provided
in all three input languages so the prompt can be rendered in the owner's language.
The canonical English label is what gets published to the website.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    id: int
    en: str          # canonical English label (published to website)
    amh: str         # Amharic label
    orm: str         # Afaan Oromo label


CATEGORIES: list[Category] = [
    Category(1, "Restaurant / Food", "ምግብ ቤት", "Mana Nyaataa"),
    Category(2, "Café / Coffee", "ቡና ቤት", "Mana Buna"),
    Category(3, "Hotel / Guesthouse / Lodging", "ሆቴል / እንግዳ ማረፊያ", "Hoteela / Keessummaa"),
    Category(4, "Arts & Crafts / Handicrafts", "ጥበብ እና እደ ጥበብ", "Harka Hojii Aartii"),
    Category(5, "Traditional Clothing / Textiles", "ባህላዊ ልብስ / ጨርቃ ጨርቅ", "Uffata Aadaa"),
    Category(6, "Jewelry / Accessories", "ጌጣጌጥ", "Faaya"),
    Category(7, "Tour Guide / Travel Service", "ጉብኝት መሪ / የጉዞ አገልግሎት", "Qajeelchaa Daawwannaa"),
    Category(8, "Cultural Experience / Music / Dance", "ባህላዊ ዝግጅት / ሙዚቃ / ዳንስ", "Muuxannoo Aadaa / Muuziiqaa"),
    Category(9, "Entertainment / Nightlife", "መዝናኛ", "Bashannana"),
    Category(10, "Market / Shop / Souvenirs", "ገበያ / ሱቅ / መታሰቢያ", "Gabaa / Suuqii"),
    Category(11, "Transport / Car Hire", "መጓጓዣ / መኪና ኪራይ", "Geejjiba / Kiraa Konkolaataa"),
    Category(12, "Spa / Wellness", "ስፓ / ጤና", "Spaa / Fayyaa"),
    Category(13, "Other", "ሌላ", "Kan biraa"),
]

OTHER_ID = 13

_BY_ID = {c.id: c for c in CATEGORIES}


def get_category(cat_id: int) -> Category | None:
    return _BY_ID.get(cat_id)


def category_menu(lang: str) -> str:
    """Render the numbered category menu in the given language (amh / orm / eng)."""
    lines = []
    for c in CATEGORIES:
        label = {"amh": c.amh, "orm": c.orm}.get(lang, c.en)
        lines.append(f"{c.id}. {label}")
    return "\n".join(lines)
