# ONBOARDING — テクニカルガイド

## アーキテクチャ概観

```
geo-sim/
├── src/geo_sim/        ← Python バックエンド（CLI + ロジック）
│   ├── data/           ← データ取得・座標計算
│   ├── model/          ← 売上シミュレーション（重力モデル）
│   ├── explorer/       ← 街プロファイリング
│   └── cli.py          ← Typer CLI エントリポイント
├── web/                ← Next.js フロントエンド + APIサーバー
│   ├── app/
│   │   ├── page.tsx    ← メインUI（地図 + サイドバー）
│   │   └── api/explore/route.ts ← POST /api/explore
│   ├── components/     ← React コンポーネント
│   └── lib/            ← ビジネスロジック + DB + キャッシュ
├── db/init.sql         ← PostgreSQL スキーマ
├── docker-compose.yml  ← PostgreSQL コンテナ
├── data/raw/           ← 入力データ（CSV）
└── tests/              ← pytest テストスイート
```

このプロジェクトは2つの独立した実行系を持つ:

1. **Python CLI** — 売上シミュレーション + 街プロファイリング（CLIベース）
2. **Next.js Web** — 街プロファイリングのWeb UI + APIサーバー

両者はロジックを共有していない（TSとPythonで同じアルゴリズムを実装）。

---

## システム構成図

```
┌──────────────┐       ┌───────────────────────────────────┐       ┌─────────────┐
│   ブラウザ    │       │        Next.js (web/)              │       │  外部API     │
│              │       │                                   │       │             │
│  MapView     │ POST  │  /api/explore (route.ts)          │       │  Overpass   │
│  Sidebar     │──────▶│    │                              │       │  API        │
│  ScoreBar    │       │    ├─ cacheKey(lat,lon,radius)    │       │             │
│  HourlyChart │◀──────│    ├─ getCache(key)               │       └──────┬──────┘
│              │ JSON   │    │    ├─ ヒット → 即返却        │              │
└──────────────┘       │    │    └─ ミス ↓                 │              │
                       │    ├─ fetchFacilitiesFromOverpass ─┼──── fetch ───┘
                       │    ├─ putCache(key, data)          │
                       │    └─ buildProfile → レスポンス    │
                       │                                   │
                       │  lib/                             │
                       │    ├─ db.ts         (pg Pool)     │
                       │    ├─ cache.ts      (CRUD)        │
                       │    ├─ overpass.ts   (API呼び出し) │
                       │    ├─ rate-limiter.ts (キュー)    │
                       │    ├─ profile.ts    (類型判定)    │
                       │    └─ constants.ts  (定数)        │
                       └────────────────┬──────────────────┘
                                        │
                                        ▼
                       ┌────────────────────────────────────┐
                       │  PostgreSQL (Docker)                │
                       │                                    │
                       │  overpass_cache                    │
                       │  ├─ cache_key (UNIQUE)             │
                       │  ├─ lat, lon, radius               │
                       │  ├─ facilities (JSONB)             │
                       │  ├─ fetched_at                     │
                       │  └─ expires_at (TTL: 14日)         │
                       └────────────────────────────────────┘
```

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

### 街プロファイラ (Web API)

```
POST /api/explore { lat, lon, radius }
       │
       ▼
[cache.ts] cacheKey() → "35.681_139.767_800"
       │
       ▼
[cache.ts] getCache(key) ─── ヒット → buildProfile() → レスポンス
       │
       ミス
       │
       ▼
[rate-limiter.ts] キューに追加（同時1リクエスト、間隔1秒）
       │
       ▼
[overpass.ts] fetchFacilitiesFromOverpass()
       │
       ▼
[cache.ts] putCache(key, facilities)
       │
       ▼
[profile.ts] buildProfile() → レスポンス
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

## キャッシュ戦略

### 空間量子化

```typescript
function cacheKey(lat: number, lon: number, radius: number): string {
  return `${lat.toFixed(3)}_${lon.toFixed(3)}_${radius}`;
}
```

小数3桁に丸め（≈111m精度）。半径800mの探索で100m程度のズレは結果にほぼ影響しない。
同じエリアを複数ユーザーが探索した場合、キャッシュが共有される。

### TTLとライフサイクル

- **TTL: 14日** — OSM編集頻度（都心で数日に1回程度の更新）に対して妥当
- **UPSERT** — 同一キーの再取得時はデータとTTLを更新
- **期限切れ削除** — 定期的に `DELETE WHERE expires_at < NOW()` で掃除

### レート制限

```
[リクエスト1] → 即実行
[リクエスト2] → キューに入る → 1秒後に実行
[リクエスト3] → キューに入る → 2秒後に実行
```

同時実行数1、間隔1秒。Overpass APIの推奨（2req/sec）より保守的に設定。

---

## DBスキーマ

```sql
CREATE TABLE overpass_cache (
    id         SERIAL PRIMARY KEY,
    cache_key  TEXT UNIQUE NOT NULL,  -- "35.681_139.767_800"
    lat        NUMERIC(8,5) NOT NULL,
    lon        NUMERIC(9,5) NOT NULL,
    radius     INTEGER NOT NULL,
    facilities JSONB NOT NULL,        -- {"office": 45, "restaurant": 32, ...}
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL   -- fetched_at + 14 days
);
```

`facilities` カラムはJSONBなので、PostgreSQL上で直接集計クエリも可能:
```sql
SELECT cache_key, facilities->>'restaurant' as restaurants
FROM overpass_cache
WHERE (facilities->>'restaurant')::int > 20;
```

---

## 外部依存・API

| リソース | 用途 | レート制限 | 呼び出し元 |
|---------|------|-----------|-----------|
| Overpass API (`overpass-api.de`) | OSM施設データ取得 | 2req/sec推奨 | サーバーサイド (route.ts) |
| OpenStreetMap Tiles | 地図タイル | Fair use policy | ブラウザ (react-leaflet) |
| PostgreSQL | キャッシュDB | N/A | サーバーサイド (lib/db.ts) |
| 国土数値情報 | 駅乗降客数 (CSV) | N/A | Python CLI |

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
| next | App Router, Route Handlers |
| react-leaflet / leaflet | 地図表示 |
| pg | PostgreSQL クライアント |
| tailwindcss | スタイリング |

- `MapView`は`dynamic(() => import(...), { ssr: false })`でクライアントのみレンダリング（Leafletがwindowに依存するため）
- `lib/overpass.ts`, `lib/cache.ts`, `lib/db.ts` はサーバーサイド専用（Route Handler内でのみ実行）

### インフラ

| コンポーネント | 構成 |
|--------------|------|
| PostgreSQL | Docker Compose (`postgres:16-alpine`) |
| Next.js | `npm run dev` (開発) / Vercel (本番) |

---

## 開発ガイド

### ローカル起動

```bash
# 1. PostgreSQL起動
docker compose up -d

# 2. Python CLI
pip install -e .
python -m geo_sim.cli simulate
python -m geo_sim.cli explore explore 35.6812 139.7671

# 3. Web
cd web
cp .env.example .env.local  # 必要に応じてポート修正
npm install
npm run dev
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

### キャッシュを手動クリアする

```bash
docker compose exec db psql -U geosim -c "DELETE FROM overpass_cache;"
```

---

## 既知の制約と今後の課題

- **人流メッシュ未統合**: 国交省の1kmメッシュデータ（2019-2021）は未使用。駅データのみで推定している。
- **時間帯パターンは推定値**: 実測ではなく一般的な分布の加重平均。
- **定数の二重管理**: Python/TSで同じカテゴリ定数を持っている。共通のJSON定義にする余地あり。
- **検証データなし**: POSデータ等がないため売上推定の精度検証は未実施。
- **キャッシュのウォームアップ**: 初回アクセスは必ずOverpass APIを叩くため遅い。事前にバッチでキャッシュを温める仕組みがあると良い。
