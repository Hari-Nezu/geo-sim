"""OpenStreetMap Overpass APIから施設データを取得。"""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
from collections import Counter

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# OSMタグ → 内部カテゴリのマッピング
TAG_TO_CATEGORY = {
    # 飲食
    ("amenity", "restaurant"): "restaurant",
    ("amenity", "cafe"): "cafe",
    ("amenity", "bar"): "bar",
    ("amenity", "pub"): "bar",
    ("amenity", "fast_food"): "restaurant",
    ("cuisine", "ramen"): "ramen",
    # 買い物
    ("shop", "supermarket"): "supermarket",
    ("shop", "convenience"): "convenience",
    ("shop", "mall"): "shop",
    ("shop", "clothes"): "shop",
    ("shop", "electronics"): "shop",
    ("shop", "books"): "bookstore",
    ("shop", "department_store"): "shop",
    # オフィス・ビジネス
    ("office", "company"): "office",
    ("office", "government"): "office",
    ("office", "it"): "office",
    ("amenity", "bank"): "bank",
    ("amenity", "conference_centre"): "conference",
    # 教育
    ("amenity", "school"): "school",
    ("amenity", "university"): "university",
    ("amenity", "college"): "university",
    ("amenity", "kindergarten"): "kindergarten",
    ("amenity", "library"): "library",
    # 医療
    ("amenity", "clinic"): "clinic",
    ("amenity", "hospital"): "hospital",
    ("amenity", "pharmacy"): "pharmacy",
    # 生活
    ("amenity", "childcare"): "kindergarten",
    ("leisure", "park"): "park",
    ("leisure", "fitness_centre"): "gym",
    ("shop", "laundry"): "laundry",
    # 交通
    ("railway", "station"): "station",
    ("highway", "bus_stop"): "bus_stop",
    # 娯楽
    ("amenity", "cinema"): "entertainment",
    ("amenity", "theatre"): "entertainment",
    ("leisure", "amusement_arcade"): "entertainment",
}


def build_query(lat: float, lon: float, radius_m: int = 800) -> str:
    """Overpass QLクエリを生成。"""
    return f"""
[out:json][timeout:30];
(
  node(around:{radius_m},{lat},{lon})["amenity"];
  node(around:{radius_m},{lat},{lon})["shop"];
  node(around:{radius_m},{lat},{lon})["office"];
  node(around:{radius_m},{lat},{lon})["leisure"];
  node(around:{radius_m},{lat},{lon})["railway"="station"];
  node(around:{radius_m},{lat},{lon})["highway"="bus_stop"];
  way(around:{radius_m},{lat},{lon})["amenity"];
  way(around:{radius_m},{lat},{lon})["shop"];
  way(around:{radius_m},{lat},{lon})["office"];
  way(around:{radius_m},{lat},{lon})["leisure"="park"];
);
out center;
"""


def categorize_element(tags: dict[str, str]) -> list[str]:
    """OSMタグから内部カテゴリに変換。"""
    categories = []
    for (tag_key, tag_value), category in TAG_TO_CATEGORY.items():
        if tags.get(tag_key) == tag_value:
            categories.append(category)

    # cuisine=ramen の特殊処理
    if tags.get("cuisine") == "ramen":
        categories.append("ramen")

    return categories if categories else _fallback_category(tags)


def _fallback_category(tags: dict[str, str]) -> list[str]:
    """マッピングに該当しない場合のフォールバック。"""
    if "shop" in tags:
        return ["shop"]
    if "office" in tags:
        return ["office"]
    if "amenity" in tags:
        amenity = tags["amenity"]
        if amenity in ("restaurant", "cafe", "bar"):
            return [amenity]
    return []


def fetch_facilities(lat: float, lon: float, radius_m: int = 800) -> dict[str, int]:
    """指定地点周辺の施設をカテゴリ別にカウント。

    Parameters
    ----------
    lat, lon : float
        中心座標
    radius_m : int
        検索半径 (m)

    Returns
    -------
    dict[str, int]
        カテゴリ別の施設数
    """
    query = build_query(lat, lon, radius_m)
    data = urllib.parse.urlencode({"data": query}).encode()

    req = urllib.request.Request(OVERPASS_URL, data=data)
    req.add_header("User-Agent", "geo-sim/0.1 (town-explorer)")

    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode())

    counter: Counter = Counter()
    for element in result.get("elements", []):
        tags = element.get("tags", {})
        for category in categorize_element(tags):
            counter[category] += 1

    return dict(counter)


def fetch_facilities_offline(sample_name: str = "tokyo_station") -> dict[str, int]:
    """オフラインテスト用のサンプルデータ。"""
    samples = {
        "tokyo_station": {
            "office": 45, "restaurant": 32, "cafe": 18, "shop": 25,
            "bank": 8, "convenience": 12, "station": 3, "bar": 5,
            "clinic": 3, "pharmacy": 4, "park": 1, "bus_stop": 6,
        },
        "kichijoji": {
            "restaurant": 28, "cafe": 22, "shop": 35, "bar": 12,
            "supermarket": 5, "park": 3, "school": 4, "clinic": 6,
            "convenience": 8, "bookstore": 4, "library": 1,
            "station": 1, "bus_stop": 8, "gym": 3,
        },
        "bunkyo_residential": {
            "school": 6, "kindergarten": 4, "park": 5, "supermarket": 3,
            "convenience": 6, "clinic": 8, "pharmacy": 3, "restaurant": 8,
            "cafe": 4, "library": 2, "station": 1, "bus_stop": 4,
        },
    }
    return samples.get(sample_name, samples["tokyo_station"])
