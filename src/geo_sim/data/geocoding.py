"""座標計算ユーティリティ。"""

from __future__ import annotations

import numpy as np

EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """2点間のhaversine距離 (km)。"""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def distance_matrix(
    origins: np.ndarray, destinations: np.ndarray
) -> np.ndarray:
    """距離行列を計算する (km)。

    Parameters
    ----------
    origins : ndarray, shape (N, 2)
        [[lat, lon], ...] 出発点
    destinations : ndarray, shape (M, 2)
        [[lat, lon], ...] 到着点

    Returns
    -------
    ndarray, shape (N, M)
        距離行列 (km)
    """
    n = origins.shape[0]
    m = destinations.shape[0]
    result = np.zeros((n, m))
    for i in range(n):
        for j in range(m):
            result[i, j] = haversine(
                origins[i, 0], origins[i, 1],
                destinations[j, 0], destinations[j, 1],
            )
    return result
