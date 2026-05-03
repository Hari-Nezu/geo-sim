"""人流パターン分析。

駅乗降客数と一般的な時間帯パターンから、エリアの賑わいの時間推移を推定する。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# 時間帯別の相対的な人流パターン（0-23時、合計=1.0に正規化）
# 出典: 一般的な都市部鉄道利用パターンから推定
HOURLY_PATTERNS = {
    "business": np.array([
        0.005, 0.003, 0.002, 0.002, 0.003, 0.010, 0.040, 0.100,
        0.130, 0.100, 0.070, 0.060, 0.065, 0.060, 0.055, 0.050,
        0.045, 0.060, 0.050, 0.035, 0.025, 0.015, 0.010, 0.005,
    ]),
    "commercial": np.array([
        0.010, 0.008, 0.005, 0.003, 0.003, 0.005, 0.010, 0.020,
        0.030, 0.040, 0.055, 0.070, 0.080, 0.075, 0.070, 0.065,
        0.065, 0.070, 0.075, 0.070, 0.060, 0.050, 0.035, 0.020,
    ]),
    "residential": np.array([
        0.010, 0.008, 0.005, 0.005, 0.005, 0.015, 0.040, 0.080,
        0.070, 0.050, 0.045, 0.045, 0.050, 0.045, 0.045, 0.050,
        0.055, 0.065, 0.075, 0.070, 0.060, 0.045, 0.035, 0.020,
    ]),
}

# 正規化
for k in HOURLY_PATTERNS:
    HOURLY_PATTERNS[k] = HOURLY_PATTERNS[k] / HOURLY_PATTERNS[k].sum()


@dataclass
class CrowdPattern:
    """時間帯別の賑わいパターン。"""

    hourly_relative: np.ndarray  # shape (24,), 合計=1.0
    peak_hours: list[int]
    quiet_hours: list[int]
    pattern_type: str  # "morning_peak", "evening_peak", "daytime", "nightlife", "flat"

    def describe(self) -> str:
        type_labels = {
            "morning_peak": "朝型（通勤ピーク）",
            "evening_peak": "夜型（飲食・娯楽）",
            "daytime": "日中型（商業・買い物）",
            "nightlife": "深夜型（繁華街）",
            "flat": "均一型（住宅街）",
        }
        label = type_labels.get(self.pattern_type, self.pattern_type)
        peak_str = ", ".join(f"{h}時" for h in self.peak_hours[:3])
        quiet_str = ", ".join(f"{h}時" for h in self.quiet_hours[:3])
        return f"パターン: {label}\nピーク: {peak_str}\n静かな時間: {quiet_str}"

    def hourly_bar_chart(self) -> str:
        """テキストベースの時間帯別バーチャート。"""
        max_val = self.hourly_relative.max()
        lines = []
        for hour in range(24):
            bar_len = int(self.hourly_relative[hour] / max_val * 20)
            bar = "▓" * bar_len
            lines.append(f"  {hour:02d}:00 {bar}")
        return "\n".join(lines)


def estimate_crowd_pattern(
    type_scores: dict[str, float],
    station_passengers: int = 0,
) -> CrowdPattern:
    """街類型スコアから時間帯別パターンを推定。

    Parameters
    ----------
    type_scores : dict
        classify_townの出力（街類型別スコア）
    station_passengers : int
        最寄り駅の乗降客数（規模感の参考）

    Returns
    -------
    CrowdPattern
    """
    # 各パターンの加重平均
    business_weight = type_scores.get("business", 0)
    commercial_weight = max(
        type_scores.get("commercial", 0),
        type_scores.get("student", 0),
    )
    residential_weight = max(
        type_scores.get("residential_family", 0),
        type_scores.get("residential_single", 0),
    )

    total_weight = business_weight + commercial_weight + residential_weight
    if total_weight == 0:
        total_weight = 1.0

    hourly = (
        HOURLY_PATTERNS["business"] * business_weight
        + HOURLY_PATTERNS["commercial"] * commercial_weight
        + HOURLY_PATTERNS["residential"] * residential_weight
    ) / total_weight

    # ピーク/静かな時間帯を特定
    sorted_hours = np.argsort(hourly)
    peak_hours = sorted(sorted_hours[-3:].tolist())
    quiet_hours = sorted(sorted_hours[:3].tolist())

    # パターン分類
    morning = hourly[7:10].sum()
    evening = hourly[18:22].sum()
    daytime = hourly[10:17].sum()
    night = hourly[22:24].sum() + hourly[0:3].sum()

    if morning > evening and morning > daytime * 0.5:
        pattern_type = "morning_peak"
    elif night > 0.15:
        pattern_type = "nightlife"
    elif evening > morning and evening > daytime * 0.4:
        pattern_type = "evening_peak"
    elif daytime > morning + evening:
        pattern_type = "daytime"
    else:
        pattern_type = "flat"

    return CrowdPattern(
        hourly_relative=hourly,
        peak_hours=peak_hours,
        quiet_hours=quiet_hours,
        pattern_type=pattern_type,
    )
