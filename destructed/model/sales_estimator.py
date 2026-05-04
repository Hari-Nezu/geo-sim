"""来店人数から売上を推定する。"""

from __future__ import annotations

import numpy as np
import pandas as pd


# 業態別デフォルトパラメータ
DEFAULTS = {
    "convenience": {
        "visit_rate": 0.005,     # 商圏内流入人数のうち実際に来店する割合
        "spend_per_visit": 650,  # 客単価 (円)
        "operating_days": 365,
    },
    "cafe": {
        "visit_rate": 0.003,
        "spend_per_visit": 580,
        "operating_days": 350,
    },
    "restaurant": {
        "visit_rate": 0.002,
        "spend_per_visit": 1100,
        "operating_days": 310,
    },
    "retail": {
        "visit_rate": 0.0025,
        "spend_per_visit": 2500,
        "operating_days": 340,
    },
}


def estimate_daily_sales(
    inflow: np.ndarray,
    visit_rate: float,
    spend_per_visit: float,
) -> np.ndarray:
    """日次売上を推定。

    Parameters
    ----------
    inflow : ndarray
        重力モデルによる候補地点への日次流入推定人数
    visit_rate : float
        来店率（流入人数のうち実際に来店する割合）
    spend_per_visit : float
        客単価 (円)

    Returns
    -------
    ndarray
        各候補地点の推定日次売上 (円)
    """
    return inflow * visit_rate * spend_per_visit


def estimate_annual_sales(
    inflow: np.ndarray,
    store_type: str = "convenience",
    **overrides,
) -> np.ndarray:
    """年間売上を推定。

    Parameters
    ----------
    inflow : ndarray
        日次流入人数
    store_type : str
        業態キー (convenience, cafe, restaurant, retail)
    **overrides
        デフォルトパラメータを上書きするキーワード引数

    Returns
    -------
    ndarray
        各候補地点の推定年間売上 (円)
    """
    params = DEFAULTS.get(store_type, DEFAULTS["convenience"]).copy()
    params.update(overrides)

    daily = estimate_daily_sales(
        inflow, params["visit_rate"], params["spend_per_visit"]
    )
    return daily * params["operating_days"]
