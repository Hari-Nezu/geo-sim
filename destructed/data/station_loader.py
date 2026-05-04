"""国土数値情報・駅別乗降客数データの読み込み。

データソース: https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-v3_0.html
形式: GeoJSON (JGD2011 / EPSG:6668)
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

TARGET_WARDS = ["港区", "千代田区", "中央区"]

# 国土数値情報の駅別乗降客数 属性名マッピング (v3.0)
COLUMN_MAP = {
    "S12_001": "station_name",
    "S12_001c": "station_code",
    "S12_002": "operator",
    "S12_003": "line_name",
    "S12_033": "passengers_2022",  # 最新年度の乗降客数
    "S12_032": "passengers_2021",
    "S12_031": "passengers_2020",
}


def load_stations(geojson_path: Path, wards: list[str] | None = None) -> gpd.GeoDataFrame:
    """駅データを読み込み、対象区に絞り込む。

    Parameters
    ----------
    geojson_path : Path
        国土数値情報の駅別乗降客数GeoJSONファイルパス
    wards : list[str] | None
        絞り込み対象の区名リスト。Noneなら全データ返却。

    Returns
    -------
    gpd.GeoDataFrame
        columns: station_name, operator, line_name, passengers, geometry
    """
    gdf = gpd.read_file(geojson_path)

    # カラム名のリネーム（存在するもののみ）
    rename = {k: v for k, v in COLUMN_MAP.items() if k in gdf.columns}
    gdf = gdf.rename(columns=rename)

    # 乗降客数: 最新年度を優先して取得
    passenger_cols = ["passengers_2022", "passengers_2021", "passengers_2020"]
    available = [c for c in passenger_cols if c in gdf.columns]
    if available:
        gdf["passengers"] = pd.to_numeric(gdf[available[0]], errors="coerce").fillna(0).astype(int)
    else:
        numeric_cols = gdf.select_dtypes(include="number").columns
        if len(numeric_cols) > 0:
            gdf["passengers"] = gdf[numeric_cols[-1]].fillna(0).astype(int)
        else:
            gdf["passengers"] = 0

    # CRS統一 (WGS84)
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    # 対象区による絞り込み（逆ジオコーディングの代わりにバウンディングボックスで近似）
    if wards:
        gdf = _filter_by_ward_bbox(gdf, wards)

    # 必要列のみ残す
    keep = ["station_name", "operator", "line_name", "passengers", "geometry"]
    keep = [c for c in keep if c in gdf.columns]
    return gdf[keep].copy()


def _filter_by_ward_bbox(gdf: gpd.GeoDataFrame, wards: list[str]) -> gpd.GeoDataFrame:
    """港区・千代田区・中央区のバウンディングボックスでフィルタ。"""
    # 3区を覆う概略バウンディングボックス (WGS84)
    WARD_BBOXES = {
        "港区": (139.719, 35.626, 139.775, 35.672),
        "千代田区": (139.731, 35.670, 139.782, 35.703),
        "中央区": (139.760, 35.660, 139.790, 35.692),
    }
    from shapely.geometry import box

    union_bbox = None
    for ward in wards:
        if ward in WARD_BBOXES:
            b = box(*WARD_BBOXES[ward])
            union_bbox = b if union_bbox is None else union_bbox.union(b)

    if union_bbox is None:
        return gdf

    return gdf[gdf.geometry.within(union_bbox)].copy()


def load_stations_from_csv(csv_path: Path) -> gpd.GeoDataFrame:
    """簡易CSV形式の駅データ読み込み（テスト・デモ用）。

    CSV columns: station_name, lat, lon, passengers
    """
    df = pd.read_csv(csv_path)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lon"], df["lat"]),
        crs="EPSG:4326",
    )
    return gdf
