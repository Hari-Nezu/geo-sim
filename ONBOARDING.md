# ONBOARDING — テクニカルガイド

## アーキテクチャ概観

```
geo-sim/
├── src/geo_sim/        ← Python バックエンド（CLI + ロジック）
│   ├── data/           ← データ取得・座標計算
│   ├── model/          ← 売上シミュレーション（重力モデル）
│   ├── explorer/       ← 街プロファイリング
│   └── cli.py          ← Typer CLI エントリポイント
├── web/                ← Next.js フロントエンド
│   ├── app/            ← App Router (page.tsx = SPA)
│   ├── components/     ← React コンポーネント
│   └── lib/            ← ビジネスロジック（TS移植）
├── data/raw/           ← 入力データ（CSV）
└── tests/              ← pytest テストスイート
```

このプロジェクトは2つの独立した実行系を持つ:

1. **Python CLI** — 売上シミュレーション + 街プロファイリング（CLIベース）
2. **Next.js Web** — 街プロファイリングのWeb UI（地図インタラクティブ）

両者はロジックを共有していない（TSとPythonで同じアルゴリズムを実装）。

---

## データフロー

### 売上シミュレータ (`python -m geo_sim.cli simulate`)

```
stations_central3.csv
       │
       ▼
[station_loader] → GeoDataFrame (駅名, 座標, 乗降客数)
       │
       ▼
[catchment.generate_grid_candidates] → 候補地点グリッド (N×2 ndarray)
       │
       ▼
[geocoding.distance_matrix] → 距離行列 (N_stations × M_candidates)
       │
       ▼
[gravity.GravityModel.score] → 日次流入人数 (M_candidates,)
       │
       ▼
[sales_estimator.estimate_annual_sales] → 推定年間売上 (M_candidates,)
```

### 街プロファイラ (`python -m geo_sim.cli explore explore` / Web版)

```
(緯度, 経度, 半径)
       │
       ▼
[osm_fetcher.fetch_facilities] → Overpass API → 施設カテゴリ別カウント
       │
       ▼
[profile.classify_town] → 街類型スコア (5類型, 0.0〜1.0)
[profile.compute_livability] → 生活利便性スコア (6軸, 0〜5)
       │
       ▼
[crowd_pattern.estimate_crowd_pattern] → 時間帯別賑わいパターン (24h)
```

---

## コアアルゴリズム

### 修正Huff型重力モデル

```
P(駅i → 地点j) = (Aj / dij^β) / Σk(Ak / dik^β)

流入人数j = Σi(passengers_i / 2 × P(i→j))
年間売上 = 流入人数 × 来店率 × 客単価 × 営業日数
```

- `β` (距離減衰): 大きいほど近距離重視。業態で異なる。
- `Aj` (魅力度): 現状は全候補均一(=1.0)。将来的に面積・ブランド力で差別化。
- `passengers / 2`: 乗降客数は往復合計なので片道に変換。
- 分母にグリッド内の全候補地点が含まれるため、候補同士が「仮想的な競合」として機能する。

### 街類型判定

施設カテゴリ × 重み行列のスコアで5類型を判定:

| 類型 | 高重みカテゴリ |
|------|---------------|
| ビジネス街 | office(×3), bank(×1.5) |
| 繁華街 | restaurant(×2), bar(×2), shop(×1.5) |
| ファミリー住宅 | school(×3), kindergarten(×3), park(×2) |
| 単身者住宅 | convenience(×2), laundry(×2), gym(×1.5) |
| 学生街 | university(×3), library(×2), bookstore(×2) |

最大スコアで正規化(0〜1)し、最高スコアの類型を`primaryType`とする。

### 時間帯パターン推定

ビジネス/商業/住宅の3パターンの加重平均。重みは類型スコアから算出。
実測データではなく一般的なパターンの推定値であることに注意。

---

## 外部依存・API

| リソース | 用途 | レート制限 |
|---------|------|-----------|
| Overpass API (`overpass-api.de`) | OSM施設データ取得 | 2req/sec推奨、重いクエリは10秒待ち |
| OpenStreetMap Tiles | 地図タイル | Fair use policy |
| 国土数値情報 | 駅乗降客数 (オフラインCSV) | N/A |

Overpass APIはブラウザ（Web版）/ Python urllib（CLI）から直接呼ぶ。バックエンドサーバーは不要。

---

## 技術スタック

### Python (src/geo_sim)

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| pandas | >=2.0 | データ処理 |
| geopandas | >=0.14 | 地理データ |
| shapely | >=2.0 | 空間演算 |
| numpy/scipy | — | 距離計算・数値演算 |
| typer | >=0.9 | CLI |

Python 3.9+対応（`from __future__ import annotations`で型ヒント互換）。

### Next.js (web/)

| パッケージ | 用途 |
|-----------|------|
| next | App Router, SSR/SSG |
| react-leaflet / leaflet | 地図表示 |
| tailwindcss | スタイリング |

`MapView`は`dynamic(() => import(...), { ssr: false })`でクライアントのみレンダリング（Leafletがwindowに依存するため）。

---

## 開発ガイド

### ローカル起動

```bash
# Python CLI
pip install -e .
python -m geo_sim.cli simulate
python -m geo_sim.cli explore explore 35.6812 139.7671

# Web
cd web && npm install && npm run dev
```

### テスト

```bash
python -m pytest tests/ -v
```

### 新しい施設カテゴリを追加する

1. `src/geo_sim/explorer/osm_fetcher.py` の `TAG_TO_CATEGORY` に追加
2. `web/lib/constants.ts` の `TAG_TO_CATEGORY` に同じ追加
3. 必要なら `CATEGORY_WEIGHTS` にも追加（類型判定に影響させる場合）

Python版とTS版で同じ定数を二重管理している点に注意。

### 新しい業態を追加する

`src/geo_sim/model/sales_estimator.py` の `DEFAULTS` に追加:

```python
"new_type": {
    "visit_rate": 0.003,
    "spend_per_visit": 800,
    "operating_days": 340,
}
```

---

## 既知の制約と今後の課題

- **人流メッシュ未統合**: 国交省の1kmメッシュデータ（2019-2021）は未使用。駅データのみで推定している。
- **時間帯パターンは推定値**: 実測ではなく一般的な分布の加重平均。
- **Overpass API依存**: レート制限を超えるとタイムアウトする。キャッシュ層がない。
- **定数の二重管理**: Python/TSで同じカテゴリ定数を持っている。共通のJSON定義にする余地あり。
- **検証データなし**: POSデータ等がないため売上推定の精度検証は未実施。
