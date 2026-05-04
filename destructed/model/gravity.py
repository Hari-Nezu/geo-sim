"""Huffモデルベースの重力モデル。

各候補地点に対して、周辺駅からの流入ポテンシャルを計算し、
競合店舗の存在を考慮した来店確率を推定する。
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class GravityModel:
    """修正Huff型重力モデル。

    P(駅iの利用者が地点jを選ぶ) = (Aj / dij^β) / Σk(Ak / dik^β)

    Parameters
    ----------
    beta : float
        距離減衰パラメータ。大きいほど近距離を重視。
        参考値: コンビニ≈2.0, カフェ≈1.8, スーパー≈1.5, 家電≈1.0
    min_distance_km : float
        距離の下限値 (km)。0除算防止。
    max_distance_km : float
        この距離を超える駅からの流入は0とみなす。
    """

    def __init__(
        self,
        beta: float = 2.0,
        min_distance_km: float = 0.05,
        max_distance_km: float = 2.0,
    ):
        self.beta = beta
        self.min_distance_km = min_distance_km
        self.max_distance_km = max_distance_km

    def score(
        self,
        distance_matrix: np.ndarray,
        passengers: np.ndarray,
        attractiveness: np.ndarray | None = None,
    ) -> np.ndarray:
        """各候補地点のポテンシャルスコアを計算。

        Parameters
        ----------
        distance_matrix : ndarray, shape (N_stations, M_candidates)
            駅→候補地点の距離行列 (km)
        passengers : ndarray, shape (N_stations,)
            各駅の乗降客数
        attractiveness : ndarray, shape (M_candidates,) or None
            各候補地点の魅力度。Noneなら全て1.0（均一）。

        Returns
        -------
        ndarray, shape (M_candidates,)
            各候補地点の集客ポテンシャルスコア（日あたり推定来訪者数）
        """
        n_stations, m_candidates = distance_matrix.shape

        if attractiveness is None:
            attractiveness = np.ones(m_candidates)

        # 距離のクリッピング
        dist = np.clip(distance_matrix, self.min_distance_km, None)

        # 最大距離を超える組み合わせをマスク
        mask = dist <= self.max_distance_km

        # Huff分子: Aj / dij^β
        numerator = attractiveness[np.newaxis, :] / (dist ** self.beta)
        numerator *= mask  # 範囲外は0

        # Huff分母: 各駅から見た全候補地点の合計
        denominator = numerator.sum(axis=1, keepdims=True)
        denominator = np.where(denominator == 0, 1, denominator)  # 0除算防止

        # 選択確率
        probability = numerator / denominator

        # 各候補地点への流入人数 = Σi(passengers_i × P(i→j))
        # 乗降客数を「日あたり片道利用者」に変換（÷2で片道、概算）
        daily_users = passengers / 2.0
        inflow = (daily_users[:, np.newaxis] * probability).sum(axis=0)

        return inflow

    def score_with_competitors(
        self,
        distance_matrix: np.ndarray,
        passengers: np.ndarray,
        competitor_distances: np.ndarray,
        competitor_attractiveness: np.ndarray | None = None,
        candidate_attractiveness: np.ndarray | None = None,
    ) -> np.ndarray:
        """競合店舗を考慮したスコア計算。

        Parameters
        ----------
        distance_matrix : ndarray, shape (N_stations, M_candidates)
        passengers : ndarray, shape (N_stations,)
        competitor_distances : ndarray, shape (N_stations, K_competitors)
        competitor_attractiveness : ndarray, shape (K_competitors,) or None
        candidate_attractiveness : ndarray, shape (M_candidates,) or None

        Returns
        -------
        ndarray, shape (M_candidates,)
        """
        n_stations, m_candidates = distance_matrix.shape
        k_competitors = competitor_distances.shape[1]

        if candidate_attractiveness is None:
            candidate_attractiveness = np.ones(m_candidates)
        if competitor_attractiveness is None:
            competitor_attractiveness = np.ones(k_competitors)

        dist_cand = np.clip(distance_matrix, self.min_distance_km, None)
        dist_comp = np.clip(competitor_distances, self.min_distance_km, None)

        mask_cand = dist_cand <= self.max_distance_km
        mask_comp = dist_comp <= self.max_distance_km

        # 候補地点の効用
        util_cand = candidate_attractiveness[np.newaxis, :] / (dist_cand ** self.beta)
        util_cand *= mask_cand

        # 競合の効用
        util_comp = competitor_attractiveness[np.newaxis, :] / (dist_comp ** self.beta)
        util_comp *= mask_comp

        # 分母 = 候補 + 競合 の合計効用
        total_util = util_cand.sum(axis=1, keepdims=True) + util_comp.sum(axis=1, keepdims=True)
        total_util = np.where(total_util == 0, 1, total_util)

        probability = util_cand / total_util

        daily_users = passengers / 2.0
        inflow = (daily_users[:, np.newaxis] * probability).sum(axis=0)

        return inflow
