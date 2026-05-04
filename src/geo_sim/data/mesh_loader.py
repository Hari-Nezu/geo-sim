"""国土交通省 人流オープンデータ（1kmメッシュ）の読み込み。

データソース: https://www.geospatial.jp/ckan/dataset/mlit-1702
形式: CSV
期間: 2019年1月〜2021年12月（月別）
メッシュ: 3次メッシュ（約1km四方）、JIS X 0410準拠

CSV列構成（推定、公開仕様に基づく）:
  mesh_code: 8桁の3次メッシュコード
  prefcode: 都道府県コード
  citycode: 市区町村コード
  year: 年
  month: 月
  dayflag: 0=休日, 1=平日, 2=全日
  timezone: 時間帯区分
  population: 滞在人口
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box


def mesh_to_latlon(mesh_code: str) -> tuple[float, float]:
    """3次メッシュコード（8桁）を中心座標(lat, lon)に変換。

    JIS X 0410:
      1次メッシュ（4桁）: 緯度方向2/3度、経度方向1度
      2次メッシュ（6桁）: 緯度方向5分、経度方向7.5分
      3次メッシュ（8桁）: 緯度方向30秒、経度方向45秒
    """
    code = str(mesh_code).zfill(8)

    # 1次メッシュ
    lat1 = int(code[0:2]) / 1.5
    lon1 = int(code[2:4]) + 100

    # 2次メッシュ
    lat2 = int(code[4]) * 5 / 60
    lon2 = int(code[5]) * 7.5 / 60

    # 3次メッシュ
    lat3 = int(code[6]) * 30 / 3600
    lon3 = int(code[7]) * 45 / 3600

    # メッシュ中心
    lat = lat1 + lat2 + lat3 + 15 / 3600
    lon = lon1 + lon2 + lon3 + 22.5 / 3600

    return lat, lon


def mesh_to_bbox(mesh_code: str) -> tuple[float, float, float, float]:
    """3次メッシュコードをバウンディングボックス(min_lon, min_lat, max_lon, max_lat)に変換。"""
    code = str(mesh_code).zfill(8)

    lat1 = int(code[0:2]) / 1.5
    lon1 = int(code[2:4]) + 100
    lat2 = int(code[4]) * 5 / 60
    lon2 = int(code[5]) * 7.5 / 60
    lat3 = int(code[6]) * 30 / 3600
    lon3 = int(code[7]) * 45 / 3600

    min_lat = lat1 + lat2 + lat3
    min_lon = lon1 + lon2 + lon3
    max_lat = min_lat + 30 / 3600
    max_lon = min_lon + 45 / 3600

    return min_lon, min_lat, max_lon, max_lat


def latlon_to_mesh(lat: float, lon: float) -> str:
    """緯度経度から3次メッシュコード（8桁）を逆算。"""
    # 1次メッシュ (緯度2/3度、経度1度)
    p = int(lat * 1.5)
    q = int(lon - 100)

    # 1次メッシュ南西端からの残差 (度)
    lat_rem = lat - p / 1.5
    lon_rem = lon - (q + 100)

    # 2次メッシュ (緯度5分、経度7.5分)
    u = int(lat_rem * 60 / 5)
    v = int(lon_rem * 60 / 7.5)

    lat_rem = lat_rem - u * 5 / 60
    lon_rem = lon_rem - v * 7.5 / 60

    # 3次メッシュ (緯度30秒、経度45秒)
    m = int(lat_rem * 3600 / 30)
    n = int(lon_rem * 3600 / 45)

    return f"{p:02d}{q:02d}{u}{v}{m}{n}"


# 港区・千代田区・中央区を含む3次メッシュの1次+2次メッシュ範囲
# 東京都心は 5339 (1次) の 45,46,55,56 (2次) あたり
CENTRAL_TOKYO_1ST_MESH = "5339"


def load_mesh_population(
    csv_path: Path,
    target_bbox: tuple[float, float, float, float] | None = None,
    dayflag: int | None = 1,
) -> gpd.GeoDataFrame:
    """人流メッシュCSVを読み込み、GeoDataFrameとして返す。

    Parameters
    ----------
    csv_path : Path
        人流メッシュCSVファイルパス
    target_bbox : (min_lon, min_lat, max_lon, max_lat) or None
        対象エリアのBBOX。指定するとこの範囲内のメッシュのみ返す。
    dayflag : int or None
        0=休日, 1=平日, 2=全日, None=フィルタなし

    Returns
    -------
    gpd.GeoDataFrame
        columns: mesh_code, lat, lon, population, geometry
    """
    # CSVカラム名は仕様により異なる可能性があるため、柔軟に対応
    df = pd.read_csv(csv_path, dtype={"mesh1kmid": str, "mesh_code": str})

    # メッシュコード列の特定
    mesh_col = _find_column(df, ["mesh1kmid", "mesh_code", "meshcode", "MESH_ID"])
    pop_col = _find_column(df, ["population", "pop", "daytime_pop", "nighttime_pop", "PTN_total"])
    dayflag_col = _find_column(df, ["dayflag", "day_flag", "daytype"], required=False)

    if mesh_col is None:
        raise ValueError(f"メッシュコード列が見つかりません: {df.columns.tolist()}")
    if pop_col is None:
        raise ValueError(f"人口列が見つかりません: {df.columns.tolist()}")

    # dayflagフィルタ
    if dayflag is not None and dayflag_col is not None:
        df = df[df[dayflag_col] == dayflag]

    # メッシュコードから座標を計算
    df = df.rename(columns={mesh_col: "mesh_code", pop_col: "population"})
    df["mesh_code"] = df["mesh_code"].astype(str).str.zfill(8)
    df["population"] = pd.to_numeric(df["population"], errors="coerce").fillna(0)

    # メッシュごとに集約（同一メッシュに複数行ある場合）
    df = df.groupby("mesh_code", as_index=False)["population"].sum()

    coords = df["mesh_code"].apply(mesh_to_latlon)
    df["lat"] = coords.apply(lambda x: x[0])
    df["lon"] = coords.apply(lambda x: x[1])

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lon"], df["lat"]),
        crs="EPSG:4326",
    )

    # BBOXフィルタ
    if target_bbox:
        min_lon, min_lat, max_lon, max_lat = target_bbox
        gdf = gdf.cx[min_lon:max_lon, min_lat:max_lat]

    return gdf[["mesh_code", "lat", "lon", "population", "geometry"]].copy()


def _find_column(df: pd.DataFrame, candidates: list[str], required: bool = True) -> str | None:
    """DataFrameから候補列名を探す。"""
    for col in candidates:
        if col in df.columns:
            return col
    # 大文字小文字を無視して再検索
    lower_cols = {c.lower(): c for c in df.columns}
    for col in candidates:
        if col.lower() in lower_cols:
            return lower_cols[col.lower()]
    return None


def generate_sample_mesh_data(
    bbox: tuple[float, float, float, float] = (139.719, 35.626, 139.790, 35.703),
) -> pd.DataFrame:
    """デモ用のサンプル人流メッシュデータを生成。

    実際の人流分布をシミュレート:
    - 東京駅・新橋周辺は高密度
    - 住宅エリアは低密度
    """
    min_lon, min_lat, max_lon, max_lat = bbox

    mesh_codes = []
    populations = []

    # BBOXをカバーするメッシュを生成
    lat = min_lat
    while lat < max_lat:
        lon = min_lon
        while lon < max_lon:
            code = latlon_to_mesh(lat + 15 / 3600, lon + 22.5 / 3600)
            mesh_codes.append(code)

            # 東京駅(35.681, 139.767)からの距離に応じて人口を設定
            dist = np.sqrt((lat - 35.681) ** 2 + (lon - 139.767) ** 2)
            base_pop = max(500, int(15000 * np.exp(-dist * 80)))
            noise = np.random.randint(-200, 200)
            populations.append(max(100, base_pop + noise))

            lon += 45 / 3600
        lat += 30 / 3600

    return pd.DataFrame({
        "mesh_code": mesh_codes,
        "population": populations,
        "dayflag": 1,
    })
