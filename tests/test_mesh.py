"""人流メッシュデータのテスト。"""

import numpy as np
import pytest

from geo_sim.data.mesh_loader import (
    mesh_to_latlon,
    mesh_to_bbox,
    latlon_to_mesh,
    generate_sample_mesh_data,
)


def test_mesh_to_latlon_tokyo_station():
    # 東京駅付近のメッシュ
    code = latlon_to_mesh(35.681, 139.767)
    lat, lon = mesh_to_latlon(code)
    assert 35.6 < lat < 35.7
    assert 139.7 < lon < 139.8


def test_latlon_to_mesh_roundtrip():
    lat, lon = 35.681, 139.767
    code = latlon_to_mesh(lat, lon)
    recovered_lat, recovered_lon = mesh_to_latlon(code)
    assert abs(recovered_lat - lat) < 0.01
    assert abs(recovered_lon - lon) < 0.015


def test_mesh_to_bbox_valid():
    code = latlon_to_mesh(35.681, 139.767)
    min_lon, min_lat, max_lon, max_lat = mesh_to_bbox(code)
    assert min_lat < max_lat
    assert min_lon < max_lon
    assert abs(max_lat - min_lat - 30 / 3600) < 1e-10
    assert abs(max_lon - min_lon - 45 / 3600) < 1e-10


def test_generate_sample_mesh_data():
    df = generate_sample_mesh_data()
    assert len(df) > 0
    assert "mesh_code" in df.columns
    assert "population" in df.columns
    assert all(df["population"] > 0)
