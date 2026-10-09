"""Onboarding conversation state machine (one per owner phone number).

Drives the guided SMS flow:
    welcome -> category -> name -> price -> location (compass) -> description
    -> translate + confidence gate -> publish + image-upload link

The flow is deliberately linear and short so it works over SMS on a basic phone.
Language is detected from the owner's FIRST substantive reply and then used for all
subsequent prompts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from data.categories import category_menu, get_category
from data.prompts import t
from app.ai import language_id
from app.ai.extraction import parse_coordinates, parse_price
from app.ai.translation import Translator, get_translator
from app.store.listings import Listing, ListingStore

UPLOAD_BASE_URL = "https://ethiopiasms.example/upload"
REVIEW_CONFIDENCE_THRESHOLD = 0.7


class Step(Enum):
    START = auto()
    CATEGORY = auto()
    NAME = auto()
    PRICE = auto()
    LOCATION = auto()
    AREA_FALLBACK = auto()
    DESCRIPTION = auto()
    DONE = auto()


@dataclass
class Session:
    phone: str
    lang: str = "eng"
    step: Step = Step.START
    draft: dict = field(default_factory=dict)


class ConversationEngine:
    """Processes one inbound text for a session and returns reply text(s)."""

    def __init__(self, store: ListingStore, translator: Translator | None = None) -> None:
        self.store = store
        self.translator = translator or get_translator()
        self._sessions: dict[str, Session] = {}

    def session_for(self, phone: str) -> Session:
        return self._sessions.setdefault(phone, Session(phone=phone))

    def handle(self, phone: str, text: str) -> list[str]:
        s = self.session_for(phone)
        text = text.strip()

        if s.step == Step.START:
            s.lang = language_id.detect(text) if text else "eng"
            s.step = Step.CATEGORY
            return [t("welcome", s.lang),
                    t("ask_category", s.lang) + "\n" + category_menu(s.lang)]

        if s.step == Step.CATEGORY:
            cat = get_category(_first_int(text))
            if not cat:
                return [t("ask_category", s.lang) + "\n" + category_menu(s.lang)]
            s.draft["category_en"] = cat.en
            s.step = Step.NAME
            return [t("ask_name", s.lang)]

        if s.step == Step.NAME:
            # re-detect language from richer free text if first msg was just a number
            s.lang = language_id.detect(text) or s.lang
            s.draft["name_src"] = text
            s.step = Step.PRICE
            return [t("ask_price", s.lang)]

        if s.step == Step.PRICE:
            s.draft["price_etb"] = parse_price(text)
            s.step = Step.LOCATION
            return [t("ask_location_intro", s.lang), t("ask_location_steps", s.lang)]

        if s.step == Step.LOCATION:
            if text.lower() == "area":
                s.step = Step.AREA_FALLBACK
                return [t("ask_area_fallback", s.lang)]
            coords = parse_coordinates(text)
            if not coords:
                return [t("location_invalid", s.lang)]
            s.draft["lat"] = coords.lat
            s.draft["lon"] = coords.lon
            s.step = Step.DESCRIPTION
            return [t("ask_description", s.lang)]

        if s.step == Step.AREA_FALLBACK:
            s.draft["area"] = text
            s.step = Step.DESCRIPTION
            return [t("ask_description", s.lang)]

        if s.step == Step.DESCRIPTION:
            s.draft["description_src"] = text
            return self._finalize(s)

        return [t("unknown", s.lang)]

    # ------------------------------------------------------------------ finalize

    def _finalize(self, s: Session) -> list[str]:
        d = s.draft
        name_tr = self.translator.translate(d.get("name_src", ""), s.lang, "eng")
        desc_tr = self.translator.translate(d.get("description_src", ""), s.lang, "eng")
        min_conf = min(name_tr.confidence, desc_tr.confidence)
        needs_review = min_conf < REVIEW_CONFIDENCE_THRESHOLD

        listing = Listing(
            phone=s.phone,
            category_en=d.get("category_en", "Other"),
            name_en=name_tr.text,
            name_src=d.get("name_src", ""),
            description_en=desc_tr.text,
            description_src=d.get("description_src", ""),
            source_lang=s.lang,
            price_etb=d.get("price_etb"),
            lat=d.get("lat"),
            lon=d.get("lon"),
            area=d.get("area"),
            needs_review=needs_review,
            published=not needs_review,
        )
        self.store.add(listing)
        s.step = Step.DONE

        upload_url = f"{UPLOAD_BASE_URL}/{listing.upload_token}"
        replies = []
        if needs_review:
            replies.append(t("review_pending", s.lang))
        else:
            replies.append(t("confirm_published", s.lang, name=listing.name_en))
        replies.append(t("images_link", s.lang, upload_url=upload_url))
        return replies


def _first_int(text: str) -> int:
    import re
    m = re.search(r"\d+", text)
    return int(m.group()) if m else -1
