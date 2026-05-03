"""重力モデルのテスト。"""

import numpy as np
import pytest

from geo_sim.model.gravity import GravityModel


def test_score_single_station_multiple_candidates():
    model = GravityModel(beta=2.0, max_distance_km=2.0)
    # 1駅、2候補地点（近い方がスコア高い）
    distances = np.array([[0.5, 1.5]])
    passengers = np.array([100000.0])

    scores = model.score(distances, passengers)
    assert scores[0] > scores[1]


def test_score_zero_beyond_max_distance():
    model = GravityModel(beta=2.0, max_distance_km=1.0)
    distances = np.array([[0.5, 3.0]])
    passengers = np.array([100000.0])

    scores = model.score(distances, passengers)
    assert scores[1] == 0.0


def test_score_proportional_to_passengers():
    model = GravityModel(beta=2.0, max_distance_km=2.0)
    distances = np.array([[1.0], [1.0]])
    passengers_a = np.array([100000.0, 50000.0])

    scores = model.score(distances, passengers_a)
    # 2駅同距離なら乗降客数に比例
    expected_ratio = 150000.0 / 2.0  # (100k + 50k) / 2 (片道)
    assert scores[0] == pytest.approx(expected_ratio, rel=0.01)


def test_competitors_reduce_score():
    model = GravityModel(beta=2.0, max_distance_km=2.0)
    distances = np.array([[1.0]])
    passengers = np.array([100000.0])

    score_no_comp = model.score(distances, passengers)

    comp_distances = np.array([[0.5]])
    score_with_comp = model.score_with_competitors(
        distances, passengers, comp_distances
    )

    assert score_with_comp[0] < score_no_comp[0]
