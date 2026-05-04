# geo-sim

地図上の任意の地点の「街の性格」を分析する街プロファイリングツール。

## 機能

- 街の類型判定（ビジネス街 / 繁華街 / ファミリー住宅街 / 単身者住宅街 / 学生街）
- 生活利便性スコア（買い物・飲食・医療・教育・公園・交通の6軸）
- 時間帯別の賑わいパターン推定
- 人流メッシュデータ（国交省1kmメッシュ）の統合

## Web版 (Next.js)

```bash
# PostgreSQL起動
docker compose up -d

# 開発サーバー起動
cd web && cp .env.example .env.local && npm install && npm run dev
```

構成: Next.js (App Router) + PostgreSQL (Overpass APIキャッシュ)

```
ブラウザ → POST /api/explore → キャッシュ検索(PostgreSQL)
                                   ├─ ヒット → 即レスポンス
                                   └─ ミス → Overpass API → DB保存 → レスポンス
```

## CLI版

```bash
pip install -e .

# 指定地点の街プロファイル
python -m geo_sim.cli explore explore 35.6595 139.7005

# 2地点を比較
python -m geo_sim.cli explore compare 35.6595 139.7005 35.7080 139.7521

# オフラインモード（サンプルデータ）
python -m geo_sim.cli explore explore 35.6812 139.7671 --offline
```

## セットアップ

```bash
# インフラ
docker compose up -d

# Python CLI
pip install -e .

# Web
cd web && npm install
```

## テスト

```bash
python -m pytest tests/
```

## データソース

- **施設データ**: [OpenStreetMap](https://www.openstreetmap.org/) (Overpass API)
- **人流メッシュ**: [国土交通省 人流オープンデータ](https://www.geospatial.jp/ckan/dataset/mlit-1702) (1kmメッシュ、2019-2021)

## ライセンス

MIT
