"""town-explorer モジュールのテスト。"""

import pytest

from geo_sim.explorer.profile import classify_town, compute_livability, build_profile
from geo_sim.explorer.osm_fetcher import categorize_element, fetch_facilities_offline
from geo_sim.explorer.crowd_pattern import estimate_crowd_pattern


def test_classify_town_business():
    facilities = {"office": 40, "bank": 8, "restaurant": 10, "cafe": 5}
    scores = classify_town(facilities)
    assert scores["business"] == 1.0  # 最大なので正規化後1.0


def test_classify_town_residential():
    facilities = {"school": 5, "kindergarten": 3, "park": 4, "supermarket": 3, "clinic": 2}
    scores = classify_town(facilities)
    assert scores["residential_family"] >= scores["business"]


def test_compute_livability_scores_range():
    facilities = {"supermarket": 3, "restaurant": 5, "clinic": 2, "park": 1}
    scores = compute_livability(facilities)
    for v in scores.values():
        assert 0.0 <= v <= 5.0


def test_build_profile_returns_profile():
    facilities = fetch_facilities_offline("tokyo_station")
    profile = build_profile(35.6812, 139.7671, facilities)
    assert profile.primary_type in ("business", "commercial", "mixed")
    assert len(profile.type_scores) == 5


def test_categorize_element_restaurant():
    tags = {"amenity": "restaurant", "cuisine": "italian", "name": "Test"}
    categories = categorize_element(tags)
    assert "restaurant" in categories


def test_categorize_element_ramen():
    tags = {"amenity": "restaurant", "cuisine": "ramen"}
    categories = categorize_element(tags)
    assert "ramen" in categories


def test_crowd_pattern_business_area():
    type_scores = {"business": 1.0, "commercial": 0.2, "residential_family": 0.0, "residential_single": 0.0, "student": 0.0}
    pattern = estimate_crowd_pattern(type_scores)
    assert pattern.pattern_type == "morning_peak"
    assert 7 in pattern.peak_hours or 8 in pattern.peak_hours
