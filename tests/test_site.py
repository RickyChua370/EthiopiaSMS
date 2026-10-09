"""Tests for the public site generator: real listings, photo honesty, search/filter."""

from __future__ import annotations

from data.categories import get_category
from data.real_osm_listings import REAL_BUSINESSES
from app.site.generator import render_html
from app.store.listings import Listing


def _listings_from_real() -> list[Listing]:
    out = []
    for name, cat_id, phone, lat, lon, desc, photo in REAL_BUSINESSES:
        cat = get_category(cat_id)
        out.append(Listing(
            phone=phone, category_en=cat.en, name_en=name, name_src=name,
            description_en=desc, description_src=desc, source_lang="eng",
            lat=lat, lon=lon, area=(desc.rsplit(" in ", 1)[-1].rstrip(".") if " in " in desc else "Ethiopia"),
            image_paths=[photo] if photo else [], images_pending=not photo,
            published=True, needs_review=False,
        ))
    return out


def test_has_thirty_real_businesses():
    assert len(REAL_BUSINESSES) == 30


def test_exactly_two_have_photos():
    with_photo = [b for b in REAL_BUSINESSES if b[6]]
    assert len(with_photo) == 2
    names = {b[0] for b in with_photo}
    assert "Ben Abeba Restaurant" in names
    assert "Sheraton Addis" in names


def test_photoless_listings_show_honest_placeholder():
    html = render_html(_listings_from_real())
    # 28 listings have no photo -> 28 honest placeholders
    assert html.count("hasn't added photos yet") == 28


def test_search_and_filter_controls_present():
    html = render_html(_listings_from_real())
    for marker in ['id="q"', 'id="cat"', 'id="loc"', "applyFilters",
                   "All categories", "All locations"]:
        assert marker in html


def test_cards_carry_filter_data_attributes():
    html = render_html(_listings_from_real())
    assert 'data-category=' in html
    assert 'data-location=' in html
    assert 'data-search=' in html


def test_multiple_cities_and_categories_in_filters():
    html = render_html(_listings_from_real())
    # a few known cities should appear as filter options
    for city in ["Addis Ababa", "Lalibela", "Gondar", "Hawassa"]:
        assert f'>{city}</option>' in html
