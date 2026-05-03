"""距離計算のテスト。"""

import numpy as np
import pytest

from geo_sim.data.geocoding import haversine, distance_matrix


def test_haversine_tokyo_to_shinbashi():
    # 東京駅→新橋: 約1.3km
    dist = haversine(35.6812, 139.7671, 35.6659, 139.7583)
    assert 1.0 < dist < 2.0


def test_haversine_same_point():
    dist = haversine(35.6812, 139.7671, 35.6812, 139.7671)
    assert dist == pytest.approx(0.0, abs=1e-10)


def test_distance_matrix_shape():
    origins = np.array([[35.6812, 139.7671], [35.6659, 139.7583]])
    destinations = np.array([[35.67, 139.76], [35.68, 139.77], [35.69, 139.75]])
    result = distance_matrix(origins, destinations)
    assert result.shape == (2, 3)


def test_distance_matrix_symmetry():
    points = np.array([[35.6812, 139.7671], [35.6659, 139.7583]])
    result = distance_matrix(points, points)
    assert result[0, 1] == pytest.approx(result[1, 0], rel=1e-10)
