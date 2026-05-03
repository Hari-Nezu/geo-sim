"""街プロファイル生成。

施設構成・人流パターンから街のキャラクターを類型化する。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


# 街の類型
TOWN_TYPES = {
    "business": "ビジネス街",
    "commercial": "繁華街・商業地",
    "residential_family": "ファミリー住宅街",
    "residential_single": "単身者向け住宅街",
    "student": "学生街",
    "mixed": "複合エリア",
}

# 施設カテゴリとその重み付け（街類型判定用）
CATEGORY_WEIGHTS = {
    "business": {
        "office": 3.0,
        "bank": 1.5,
        "conference": 1.0,
    },
    "commercial": {
        "restaurant": 2.0,
        "cafe": 1.5,
        "bar": 2.0,
        "shop": 1.5,
        "entertainment": 2.0,
    },
    "residential_family": {
        "school": 3.0,
        "kindergarten": 3.0,
        "park": 2.0,
        "supermarket": 2.0,
        "clinic": 1.5,
    },
    "residential_single": {
        "convenience": 2.0,
        "laundry": 2.0,
        "gym": 1.5,
        "cafe": 1.0,
    },
    "student": {
        "university": 3.0,
        "library": 2.0,
        "cafe": 1.5,
        "bookstore": 2.0,
        "ramen": 1.5,
    },
}


@dataclass
class TownProfile:
    """街プロファイル。"""

    lat: float
    lon: float
    radius_m: int
    facility_counts: dict[str, int] = field(default_factory=dict)
    type_scores: dict[str, float] = field(default_factory=dict)
    primary_type: str = "mixed"
    livability_scores: dict[str, float] = field(default_factory=dict)

    @property
    def primary_type_label(self) -> str:
        return TOWN_TYPES.get(self.primary_type, "不明")

    def summary(self) -> str:
        lines = [
            f"📍 ({self.lat:.5f}, {self.lon:.5f}) 半径{self.radius_m}m",
            f"街タイプ: {self.primary_type_label}",
            "",
            "施設構成:",
        ]
        for cat, count in sorted(self.facility_counts.items(), key=lambda x: -x[1]):
            if count > 0:
                lines.append(f"  {cat}: {count}")

        lines.append("")
        lines.append("類型スコア:")
        for ttype, score in sorted(self.type_scores.items(), key=lambda x: -x[1]):
            bar = "█" * int(score * 10)
            lines.append(f"  {TOWN_TYPES[ttype]:<10} {bar} ({score:.2f})")

        if self.livability_scores:
            lines.append("")
            lines.append("生活利便性:")
            for key, score in self.livability_scores.items():
                stars = "★" * int(score) + "☆" * (5 - int(score))
                lines.append(f"  {key}: {stars}")

        return "\n".join(lines)


def classify_town(facility_counts: dict[str, int]) -> dict[str, float]:
    """施設構成から街類型スコアを計算。"""
    scores = {}
    for town_type, weights in CATEGORY_WEIGHTS.items():
        score = 0.0
        for category, weight in weights.items():
            score += facility_counts.get(category, 0) * weight
        scores[town_type] = score

    # 正規化 (0-1)
    max_score = max(scores.values()) if scores else 1.0
    if max_score > 0:
        scores = {k: v / max_score for k, v in scores.items()}

    return scores


def compute_livability(facility_counts: dict[str, int]) -> dict[str, float]:
    """生活利便性スコアを計算 (0-5)。"""
    checks = {
        "買い物": ["supermarket", "convenience", "shop"],
        "飲食": ["restaurant", "cafe", "ramen"],
        "医療": ["clinic", "hospital", "pharmacy"],
        "教育": ["school", "kindergarten", "library"],
        "公園・緑": ["park"],
        "交通": ["station", "bus_stop"],
    }

    scores = {}
    for label, categories in checks.items():
        total = sum(facility_counts.get(c, 0) for c in categories)
        # 対数スケールで0-5に変換（1件=1, 3件=2.5, 10件=4, 20件+=5）
        if total == 0:
            scores[label] = 0.0
        else:
            scores[label] = min(5.0, np.log1p(total) / np.log1p(20) * 5.0)

    return scores


def build_profile(
    lat: float,
    lon: float,
    facility_counts: dict[str, int],
    radius_m: int = 800,
) -> TownProfile:
    """施設カウントから街プロファイルを生成。"""
    type_scores = classify_town(facility_counts)
    primary_type = max(type_scores, key=type_scores.get) if type_scores else "mixed"
    livability = compute_livability(facility_counts)

    return TownProfile(
        lat=lat,
        lon=lon,
        radius_m=radius_m,
        facility_counts=facility_counts,
        type_scores=type_scores,
        primary_type=primary_type,
        livability_scores=livability,
    )
