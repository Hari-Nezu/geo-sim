"""商圏（到達圏）分析。"""

from __future__ import annotations

import numpy as np
import geopandas as gpd
from shapely.geometry import Point

from geo_sim.data.geocoding import haversine


def stations_in_catchment(
    candidate_lat: float,
    candidate_lon: float,
    stations: gpd.GeoDataFrame,
    radius_km: float = 2.0,
) -> gpd.GeoDataFrame:
    """候補地点から指定半径内の駅を抽出。"""
    distances = stations.geometry.apply(
        lambda geom: haversine(candidate_lat, candidate_lon, geom.y, geom.x)
    )
    return stations[distances <= radius_km].copy()


def generate_grid_candidates(
    bbox: tuple[float, float, float, float],
    step_km: float = 0.2,
) -> np.ndarray:
    """バウンディングボックス内にグリッド状の候補地点を生成。

    Parameters
    ----------
    bbox : (min_lon, min_lat, max_lon, max_lat)
    step_km : グリッド間隔 (km)

    Returns
    -------
    ndarray, shape (N, 2) — [[lat, lon], ...]
    """
    min_lon, min_lat, max_lon, max_lat = bbox

    # 緯度1度 ≈ 111km、経度1度 ≈ 91km (東京付近)
    lat_step = step_km / 111.0
    lon_step = step_km / 91.0

    lats = np.arange(min_lat, max_lat, lat_step)
    lons = np.arange(min_lon, max_lon, lon_step)

    grid = np.array([[lat, lon] for lat in lats for lon in lons])
    return grid


# 港区・千代田区・中央区を覆うBBOX
CENTRAL_3WARDS_BBOX = (139.719, 35.626, 139.790, 35.703)
